"""Bounded OS SendInput mouse movement for the test-owned WinUI L08 GUI.

Unlike pywinauto.mouse.move (SetCursorPos), SendInput generates routed WinUI
PointerEntered/PointerMoved in the Windows interactive desktop. This helper
moves only the pointer; it never presses buttons or alters application state.
Use solely while the exact isolated test-owned application is foreground.
"""
from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes


class _MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG), ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t),
    ]


class _InputUnion(ctypes.Union):
    _fields_ = [("mi", _MouseInput)]


class _Input(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _InputUnion)]


_MOUSEEVENTF_MOVE = 0x0001
_MOUSEEVENTF_VIRTUALDESK = 0x4000
_MOUSEEVENTF_ABSOLUTE = 0x8000


def _normalized_point(x: int, y: int,
                      left: int, top: int, width: int, height: int) -> tuple[int, int]:
    """Convert on-screen integer pixels to the full virtual-desktop range."""
    if (any(type(v) is not int for v in (x, y, left, top, width, height))
            or width <= 1 or height <= 1
            or not (left <= x < left + width and top <= y < top + height)):
        raise ValueError("cursor destination outside valid virtual desktop")
    return ((x - left) * 65535 // (width - 1),
            (y - top) * 65535 // (height - 1))


def sendinput_mouse_move(coords: tuple[int, int]) -> None:
    """Inject a 4-step OS mouse move, never silently fall back to SetCursorPos."""
    if os.name != "nt":
        raise OSError("SendInput mouse movement requires Windows")
    if (type(coords) is not tuple or len(coords) != 2
            or any(type(v) is not int for v in coords)):
        raise ValueError("cursor destination must be an integer (x, y) tuple")

    user32 = ctypes.windll.user32
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    left, top = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
    width, height = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
    _normalized_point(*coords, left, top, width, height)

    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.GetCursorPos.restype = wintypes.BOOL
    current = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(current)):
        raise ctypes.WinError()

    user32.SendInput.argtypes = [
        wintypes.UINT, ctypes.POINTER(_Input), ctypes.c_int,
    ]
    user32.SendInput.restype = wintypes.UINT
    start_x, start_y = current.x, current.y
    x, y = coords
    for step in range(1, 5):
        intermediate_x = round(start_x + (x - start_x) * step / 4)
        intermediate_y = round(start_y + (y - start_y) * step / 4)
        dx, dy = _normalized_point(
            intermediate_x, intermediate_y, left, top, width, height)
        move = _Input(
            0, _InputUnion(mi=_MouseInput(
                dx, dy, 0,
                _MOUSEEVENTF_MOVE | _MOUSEEVENTF_VIRTUALDESK |
                _MOUSEEVENTF_ABSOLUTE,
                0, 0,
            )),
        )
        if user32.SendInput(1, ctypes.byref(move), ctypes.sizeof(move)) != 1:
            raise ctypes.WinError()
        time.sleep(.006)

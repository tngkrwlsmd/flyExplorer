"""Opt-in, test-owned *screen* pixel sampling; never a visual PASS by itself.

This is intentionally separate from F05's XAML RenderTargetBitmap path.
A failed ownership/visibility/desktop probe must not read desktop pixels.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path


def capture_box(rect, width: int, height: int) -> tuple[int, int, int, int]:
    """Reject offscreen, excessive or implausibly small test windows."""
    left, top, right, bottom = map(int, rect)
    if not (640 <= right - left <= 1100 and
            350 <= bottom - top <= 750 and
            0 <= left < right <= width and
            0 <= top < bottom <= height):
        raise ValueError("Test-owned window is not wholly within active screen")
    return left, top, right, bottom


def attempt_capture(*, win, process_id: int, visual_dir: Path, stage: str,
                    theme: str, focus, owned_foreground) -> bool:
    """Capture a verified foreground test-only HWND crop, never the desktop.

    Privacy gate: the window must own the foreground and all sampled visible
    surface points. No fallback to an unrestricted fullscreen capture.
    """
    if stage not in ("name", "size", "month", "type") or theme not in ("light", "dark"):
        raise ValueError("Unsupported isolated F05 screenshot fixture")
    target = visual_dir / ("screen-" + stage + ".png")
    if target.exists() or target.is_symlink() or visual_dir.is_symlink():
        raise ValueError("Screenshot destination collision")
    import ctypes
    from ctypes import wintypes
    from PIL import ImageGrab

    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.WindowFromPoint.argtypes = [wintypes.POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    focus()
    if not owned_foreground():
        print("F05_SCREEN_CAPTURE=BLOCKED_NOT_OWNED_FOREGROUND", flush=True)
        return False
    window = win.wrapper_object()
    if window.element_info.process_id != process_id or process_id <= 0:
        raise ValueError("Non-owned screenshot process")
    hwnd = window.handle
    if not user32.IsWindowVisible(hwnd):
        print("F05_SCREEN_CAPTURE=BLOCKED_INVISIBLE_WINDOW", flush=True)
        return False
    bounds = win.rectangle()
    try:
        box = capture_box((bounds.left, bounds.top, bounds.right, bounds.bottom),
                          user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    except ValueError:
        print("F05_SCREEN_CAPTURE=BLOCKED_OFFSCREEN_WINDOW", flush=True)
        return False

    # Verify a dense grid of visible points is covered by our own process.
    # Never record arbitrary content from a second user's overlapping window.
    left, top, right, bottom = box
    for iy in range(1, 8):
        for ix in range(1, 8):
            x = left + (right - left) * ix // 8
            y = top + (bottom - top) * iy // 8
            visible_hwnd = user32.WindowFromPoint(wintypes.POINT(x, y))
            visible_pid = wintypes.DWORD()
            if visible_hwnd:
                user32.GetWindowThreadProcessId(
                    visible_hwnd, ctypes.byref(visible_pid))
            if visible_pid.value != process_id:
                print("F05_SCREEN_CAPTURE=BLOCKED_NONOWNED_OVERLAY", flush=True)
                return False
    if not owned_foreground():
        print("F05_SCREEN_CAPTURE=BLOCKED_FOREGROUND_CHANGED", flush=True)
        return False
    try:
        screenshot = ImageGrab.grab(bbox=box, include_layered_windows=True)
        # The real desktop may change between the visibility checks and grab.
        # If so, discard the in-memory sample without writing its pixels.
        if not owned_foreground():
            print("F05_SCREEN_CAPTURE=BLOCKED_FOREGROUND_CHANGED", flush=True)
            return False
        extrema = screenshot.convert("RGB").getextrema()
        if max(hi - lo for lo, hi in extrema) < 32:
            print("F05_SCREEN_CAPTURE=BLOCKED_BLANK_SCREEN_PIXEL_API", flush=True)
            return False
        screenshot.save(target, format="PNG")
        if not (1500 < target.stat().st_size < 3_000_000):
            target.unlink(missing_ok=True)
            print("F05_SCREEN_CAPTURE=BLOCKED_UNUSABLE_IMAGE", flush=True)
            return False
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        print("F05_SCREEN_CAPTURE=PIXELS_ONLY_NEEDS_VISUAL_REVIEW"
              + " THEME=" + theme + " STAGE=" + stage
              + " SIZE=" + str(screenshot.width) + "x" + str(screenshot.height)
              + " SHA256=" + digest
              + " FILE=" + str(target), flush=True)
        return True
    except (OSError, ValueError):
        print("F05_SCREEN_CAPTURE=BLOCKED_CAPTURE_API", flush=True)
        return False

"""Read only a test-owned WinUI initial-navigation phase page on failure.

The mapping is named for the launched synthetic test child PID. Never enumerate
named objects/processes or open arbitrary application memory. All values are
decoded into fixed public phase codes, without paths, environment or raw bytes.
"""
from __future__ import annotations

import ctypes
import os
import struct

MAGIC = 0x47303150
CAPACITY = 64
PHASES = (
    "LEFT_SUBMIT_BEGIN", "RIGHT_SUBMIT_BEGIN",
    "LEFT_SUBMIT_ACCEPTED", "LEFT_SUBMIT_REJECTED",
    "RIGHT_SUBMIT_ACCEPTED", "RIGHT_SUBMIT_REJECTED",
    "RESULT_CALLBACK", "RESULT_ENQUEUE_OK",
    "RESULT_ENQUEUE_REJECTED", "RESULT_IGNORED",
    "LEFT_APPLIED", "LEFT_FAILED", "LEFT_REJECTED",
    "LEFT_EXTENDED", "LEFT_NOCHANGE",
    "RIGHT_APPLIED", "RIGHT_FAILED", "RIGHT_REJECTED",
    "RIGHT_EXTENDED", "RIGHT_NOCHANGE",
)
PAGE_BYTES = 12 + CAPACITY * 4
FILE_MAP_READ = 0x0004


def decode_owned_startup_page(data: bytes, expected_pid: int) -> list[str]:
    """Decode fixed native codes, checking magic/PID and bounded row count."""
    if not isinstance(expected_pid, int) or expected_pid <= 0:
        return []
    if len(data) != PAGE_BYTES:
        return []
    magic, pid, count = struct.unpack_from("<iii", data)
    if magic != MAGIC or pid != expected_pid or count < 0:
        return []
    codes = struct.unpack_from("<" + "i" * CAPACITY, data, 12)
    return [PHASES[code - 1] for code in codes[:min(count, CAPACITY)]
            if 1 <= code <= len(PHASES)]


def read_owned_startup_events(child_pid: int) -> list[str]:
    """Read only this spawned app's Local file mapping, never its raw memory."""
    if os.name != "nt" or type(child_pid) is not int or child_pid <= 0:
        return []
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenFileMappingW.argtypes = (
        ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p)
    kernel.OpenFileMappingW.restype = ctypes.c_void_p
    kernel.MapViewOfFile.argtypes = (
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_uint32, ctypes.c_size_t)
    kernel.MapViewOfFile.restype = ctypes.c_void_p
    kernel.UnmapViewOfFile.argtypes = (ctypes.c_void_p,)
    kernel.UnmapViewOfFile.restype = ctypes.c_int
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel.CloseHandle.restype = ctypes.c_int
    handle = kernel.OpenFileMappingW(
        FILE_MAP_READ, 0, f"Local\\flyExplorer-G01-startup-{child_pid}")
    if not handle:
        return []
    try:
        view = kernel.MapViewOfFile(handle, FILE_MAP_READ, 0, 0, PAGE_BYTES)
        if not view:
            return []
        try:
            data = ctypes.string_at(view, PAGE_BYTES)
        finally:
            kernel.UnmapViewOfFile(view)
    finally:
        kernel.CloseHandle(handle)
    return decode_owned_startup_page(data, child_pid)

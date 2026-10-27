"""G01-only, x64 crash-time stowed HRESULT/frame observer for an owned child.

Attaches to the exact synthetic GUI fixture process, does not handle its
exceptions, create dumps, persist raw pointers, or read user files.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import struct
import sys
import time

DWORD = ctypes.c_uint32
PTR = ctypes.c_void_p
U64 = ctypes.c_uint64
STOWED_V2 = struct.Struct("<IIiIQIIQI4xQ")
LABELS = {
    "flyexplorer.exe": "FLY", "microsoft.ui.xaml.dll": "XAML",
    "combase.dll": "COMBASE", "coremessagingxp.dll": "COREMSG",
    "ntdll.dll": "NTDLL",
}


class EXCEPTION_RECORD(ctypes.Structure):
    _fields_ = [("ExceptionCode", DWORD), ("ExceptionFlags", DWORD),
                ("ExceptionRecord", PTR), ("ExceptionAddress", PTR),
                ("NumberParameters", DWORD),
                ("ExceptionInformation", U64 * 15)]


class EXCEPTION_INFO(ctypes.Structure):
    _fields_ = [("record", EXCEPTION_RECORD), ("first_chance", DWORD)]


class EVENT_DATA(ctypes.Union):
    _fields_ = [("exception", EXCEPTION_INFO), ("file", PTR),
                ("raw", ctypes.c_byte * 160)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("code", DWORD), ("pid", DWORD), ("tid", DWORD),
                ("data", EVENT_DATA)]


class MODULE_INFO(ctypes.Structure):
    _fields_ = [("base", PTR), ("size", DWORD), ("entry", PTR)]


def decode_v2(data):
    """Read the documented x64 SE02 binary layout, never error text."""
    if not data or len(data) != 56:
        return None
    size, signature, hr, flags, _origin, width, count, trace, _nested_type, _nested = STOWED_V2.unpack(data)
    if size != 56 or signature != 0x53453032:
        return None
    if flags & 3 != 1 or width != 8 or count > 16 or (count and not trace):
        return (hr & 0xFFFFFFFF, 0, 0)
    return (hr & 0xFFFFFFFF, count, trace)


def describe_v2(data, modules):
    """Emit a bounded stack-availability classification, never a raw pointer."""
    if not data or len(data) != STOWED_V2.size:
        return None
    size, signature, _, flags, origin, width, words, trace, nested, _ = STOWED_V2.unpack(data)
    if size != 56 or signature != 0x53453032:
        return None
    form = {1: "BINARY", 2: "TEXT"}.get(flags & 3, "UNKNOWN")
    result = [f"FORM_{form}"]
    if form == "BINARY":
        if width != 8 or words > 16 or (words and not trace):
            result.append("STACK_INVALID")
        else:
            result.append(f"WORDS_{words}")
        origin_label = frame_label(origin, modules)
        if origin_label:
            result.append(f"ORIGIN_{origin_label}")
    if nested:
        result.append("NESTED_PRESENT")
    return result


def _api():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    p = ctypes.WinDLL("psapi", use_last_error=True)
    defs = [
        (k.DebugActiveProcess, [DWORD], wintypes.BOOL),
        (k.DebugActiveProcessStop, [DWORD], wintypes.BOOL),
        (k.DebugSetProcessKillOnExit, [wintypes.BOOL], wintypes.BOOL),
        (k.WaitForDebugEvent, [ctypes.POINTER(DEBUG_EVENT), DWORD], wintypes.BOOL),
        (k.ContinueDebugEvent, [DWORD, DWORD, DWORD], wintypes.BOOL),
        (k.OpenProcess, [DWORD, wintypes.BOOL, DWORD], PTR),
        (k.ReadProcessMemory, [PTR, PTR, PTR, ctypes.c_size_t,
                              ctypes.POINTER(ctypes.c_size_t)], wintypes.BOOL),
        (k.CloseHandle, [PTR], wintypes.BOOL),
        (p.EnumProcessModulesEx, [PTR, PTR, DWORD, ctypes.POINTER(DWORD), DWORD], wintypes.BOOL),
        (p.GetModuleInformation, [PTR, PTR, ctypes.POINTER(MODULE_INFO), DWORD], wintypes.BOOL),
        (p.GetModuleBaseNameW, [PTR, PTR, wintypes.LPWSTR, DWORD], DWORD),
    ]
    for function, args, result in defs:
        function.argtypes, function.restype = args, result
    return k, p


def _read(k, handle, ptr, size):
    if not ptr or size < 1 or size > 128:
        return None
    buf, count = ctypes.create_string_buffer(size), ctypes.c_size_t()
    ok = k.ReadProcessMemory(handle, PTR(ptr), buf, size, ctypes.byref(count))
    return buf.raw if ok and count.value == size else None


def _modules(p, handle):
    entries, count = (PTR * 512)(), DWORD()
    if not p.EnumProcessModulesEx(handle, entries, ctypes.sizeof(entries),
                                  ctypes.byref(count), 3):
        return []
    modules = []
    for entry in list(entries)[:min(count.value // ctypes.sizeof(PTR), 512)]:
        info, name = MODULE_INFO(), ctypes.create_unicode_buffer(90)
        if (not entry or not p.GetModuleInformation(
                handle, entry, ctypes.byref(info), ctypes.sizeof(info)) or
                not p.GetModuleBaseNameW(handle, entry, name, len(name))):
            continue
        label = LABELS.get(name.value.lower())
        if label and info.base and info.size:
            modules.append((int(info.base), int(info.size), label))
    return modules


def frame_label(address, modules):
    """Return whitelisted module+RVA, never a raw instruction pointer."""
    for base, size, label in modules:
        if base <= address < base + size and address - base <= 0xFFFFFFFF:
            return f"{label}_{address - base:08X}"
    return None


def _decode(k, p, handle, record):
    if record.NumberParameters < 2:
        return ["G01_DEBUG_STOWED_PARAMS_INVALID"]
    count = int(record.ExceptionInformation[1])
    address = int(record.ExceptionInformation[0])
    if not address or count < 1 or count > 16:
        return ["G01_DEBUG_STOWED_PARAMS_INVALID"]
    limit = min(count, 4)
    array = _read(k, handle, address, limit * 8)
    if array is None:
        return ["G01_DEBUG_STOWED_ARRAY_UNREADABLE"]
    result = [f"G01_DEBUG_STOWED_COUNT_{limit}"]
    if count > limit:
        result.append("G01_DEBUG_STOWED_COUNT_TRUNCATED")
    modules = _modules(p, handle)
    for i, addr in enumerate(struct.unpack("<" + "Q" * limit, array)):
        data = _read(k, handle, addr, 56)
        item = decode_v2(data)
        if item is None:
            result.append(f"G01_DEBUG_STOWED_{i}_UNREADABLE")
            continue
        hr, count_frames, stack_ptr = item
        result.append(f"G01_DEBUG_STOWED_{i}_HRESULT_{hr:08X}")
        metadata = describe_v2(data, modules)
        if metadata:
            result.extend(f"G01_DEBUG_STOWED_{i}_{piece}" for piece in metadata)
        if count_frames:
            raw = _read(k, handle, stack_ptr, count_frames * 8)
            if raw is None:
                result.append(f"G01_DEBUG_STOWED_{i}_FRAMES_UNREADABLE")
            else:
                mapped = 0
                for frame_index, ip in enumerate(
                        struct.unpack("<" + "Q" * count_frames, raw)):
                    frame = frame_label(ip, modules)
                    if frame:
                        mapped += 1
                        result.append(f"G01_DEBUG_STOWED_{i}_FRAME_{frame_index:02d}_{frame}")
                result.append(f"G01_DEBUG_STOWED_{i}_MAPPED_{mapped}")
    return result


def run(arguments):
    if sys.platform != "win32" or ctypes.sizeof(PTR) != 8 or len(arguments) != 5:
        return 2
    if ctypes.sizeof(EXCEPTION_RECORD) != 152 or ctypes.sizeof(DEBUG_EVENT) != 176:
        return 2
    import psutil

    pid, exe, stamp, ready, report = arguments
    pid, stamp, exe = int(pid), float(stamp), Path(exe).resolve()
    ready, report = Path(ready).resolve(), Path(report).resolve()
    owned = Path(os.environ["TEMP"]).resolve().parent
    if (not owned.name.startswith("columns-gui-owned-") or
            ready.parent != owned or report.parent != owned or
            exe.name.lower() != "flyexplorer.exe" or
            exe.parent.name.lower() != "release"):
        return 2
    process = psutil.Process(pid)
    if (process.exe().lower() != str(exe).lower() or
            abs(process.create_time() - stamp) > 0.15):
        return 2
    k, p = _api()
    if not k.DebugActiveProcess(pid):
        ready.write_text("FAILED\n", encoding="ascii")
        return 1
    if not k.DebugSetProcessKillOnExit(False):
        k.DebugActiveProcessStop(pid)
        ready.write_text("FAILED\n", encoding="ascii")
        return 1
    handle = k.OpenProcess(0x0410, False, pid)
    if not handle:
        k.DebugActiveProcessStop(pid)
        ready.write_text("FAILED\n", encoding="ascii")
        return 1
    ready.write_text("ATTACHED\n", encoding="ascii")
    initial_break = False
    started = time.monotonic()
    try:
        while time.monotonic() - started < 110 and not (owned / "g01-debugger-stop").exists():
            event = DEBUG_EVENT()
            if not k.WaitForDebugEvent(ctypes.byref(event), 125):
                continue
            code = int(event.code)
            status = 0x00010002  # DBG_CONTINUE: regular non-exception events
            if code == 1:
                exception = event.data.exception.record
                native_code = int(exception.ExceptionCode)
                status = 0x80010001  # DBG_EXCEPTION_NOT_HANDLED, preserve crash
                if native_code == 0x80000003 and not initial_break:
                    initial_break, status = True, 0x00010002
                elif native_code == 0xC000027B:
                    with report.open("a", encoding="ascii") as stream:
                        stream.write("G01_DEBUG_STOWED_EXCEPTION\n")
                        for token in _decode(k, p, handle, exception):
                            stream.write(token + "\n")
                elif native_code == 0xC0000409:
                    with report.open("a", encoding="ascii") as stream:
                        stream.write("G01_DEBUG_FAILFAST_C0000409\n")
            if code in (3, 6) and event.data.file:
                k.CloseHandle(event.data.file)
            k.ContinueDebugEvent(event.pid, event.tid, status)
            if code == 5:  # Owned child has exited
                break
    finally:
        k.DebugActiveProcessStop(pid)
        k.CloseHandle(handle)
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))

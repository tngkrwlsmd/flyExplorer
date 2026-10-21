"""Bounded stack/context capture for an already-owned Popen child; no PID-only API."""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def validate_paths(exe, directory, root=ROOT):
    exe, directory, root = Path(exe).resolve(), Path(directory).resolve(), root.resolve()
    if not exe.is_relative_to(root / "out") or not exe.is_file():
        raise ValueError("target must be a built repository executable")
    if exe.name.lower() not in ("flyexplorer.exe", "flyshellisolationhelper.exe"):
        raise ValueError("unsupported owned executable")
    if not directory.is_relative_to(root / "logs"):
        raise ValueError("dump must remain in ignored repository logs")
    return exe, directory


def summarize(data):
    """Validate bounded directory/thread records before calling a dump usable."""
    if not 32 <= len(data) <= 64 * 1024**2:
        raise ValueError("dump size bounds")
    signature, version, count, directory = struct.unpack_from("<IIII", data)
    if signature != 0x504d444d or version & 0xffff != 0xa793 or not 1 <= count <= 128:
        raise ValueError("dump header")
    if directory < 32 or directory + count * 12 > len(data):
        raise ValueError("dump directory")
    streams = {}
    unused = 0
    for index in range(count):
        kind, size, offset = struct.unpack_from("<III", data, directory + index * 12)
        # Windows may reserve several directory slots as UnusedStream (0).
        # They contain no stream to dereference and need not be unique.
        if kind == 0:
            unused += 1
            continue
        if offset + size > len(data):
            raise ValueError("dump stream data bounds")
        if kind in streams:
            raise ValueError(f"duplicate dump stream type {kind}")
        streams[kind] = (size, offset)
    size, offset = streams.get(3, (0, 0))
    if size < 4:
        raise ValueError("thread list missing")
    threads = struct.unpack_from("<I", data, offset)[0]
    if not 1 <= threads <= 4096 or size < 4 + threads * 48:
        raise ValueError("thread list bounds")
    contexts, stacks = 0, 0
    for index in range(threads):
        entry = offset + 4 + index * 48
        for descriptor, label in ((entry + 32, "stack"), (entry + 40, "context")):
            length, rva = struct.unpack_from("<II", data, descriptor)
            if length and (rva < 32 or rva + length > len(data)):
                raise ValueError("thread data bounds")
            if length:
                if label == "stack":
                    stacks += 1
                else:
                    contexts += 1
    if not contexts or not stacks:
        raise ValueError("no native thread stack/context")
    return {"threads": threads, "contexts": contexts, "stacks": stacks,
            "bytes": len(data), "unused_streams": unused}


def kernel():
    api = c.WinDLL("kernel32", use_last_error=True)
    api.GetCurrentProcess.restype = W.HANDLE
    api.GetProcessId.argtypes = [W.HANDLE]
    api.GetProcessId.restype = W.DWORD
    api.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, c.POINTER(W.DWORD)]
    api.QueryFullProcessImageNameW.restype = W.BOOL
    api.DuplicateHandle.argtypes = [W.HANDLE, W.HANDLE, W.HANDLE, c.POINTER(W.HANDLE), W.DWORD, W.BOOL, W.DWORD]
    api.DuplicateHandle.restype = W.BOOL
    api.CloseHandle.argtypes = [W.HANDLE]
    api.CloseHandle.restype = W.BOOL
    api.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    api.WaitForSingleObject.restype = W.DWORD
    return api


def verify_handle(api, handle, pid, exe):
    image = c.create_unicode_buffer(32768)
    size = W.DWORD(len(image))
    if api.GetProcessId(handle) != pid:
        raise ValueError("process handle/PID mismatch")
    if not api.QueryFullProcessImageNameW(handle, 0, image, c.byref(size)):
        raise c.WinError(c.get_last_error())
    if Path(image.value).resolve() != exe:
        raise ValueError("process executable mismatch")
    if api.WaitForSingleObject(handle, 0) != 0x102:
        raise ValueError("owned process already exited")


def capture_owned_dump(process, exe, directory, *, timeout=10):
    """Best effort only; caller must retain its original timeout/failure."""
    api, inherited = None, W.HANDLE()
    try:
        exe, directory = validate_paths(exe, directory)
        if os.name != "nt" or not isinstance(process, subprocess.Popen):
            raise ValueError("requires a caller-owned Windows Popen child")
        if not 0 < timeout <= 10 or process.poll() is not None:
            raise ValueError("invalid budget or exited child")
        api = kernel()
        verify_handle(api, int(process._handle), process.pid, exe)
        # Duplicate the original handle, never reopen an arbitrary/recycled PID.
        # Collector gets query/read/synchronize rights, never terminate rights.
        if not api.DuplicateHandle(api.GetCurrentProcess(), int(process._handle),
                                   api.GetCurrentProcess(), c.byref(inherited),
                                   0x100410, True, 0):
            raise c.WinError(c.get_last_error())
        directory.mkdir(parents=True, exist_ok=True)
        output = directory / f"owned-{process.pid}-{uuid4().hex}.dmp"
        startup = subprocess.STARTUPINFO()
        startup.lpAttributeList = {"handle_list": [int(inherited.value)]}
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--handle", str(inherited.value),
             "--pid", str(process.pid), "--exe", str(exe), "--output", str(output)],
            startupinfo=startup, close_fds=True, creationflags=0x08000000,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout,
        )
        if completed.returncode:
            details = json.loads(completed.stdout)
            return {"status": "FAILED", "error_type": details.get("error_type"),
                    "detail": details.get("detail"), "winerror": details.get("winerror")}
        result = json.loads(completed.stdout)
        if result.get("status") != "CAPTURED" or not output.is_file():
            raise RuntimeError("collector result incomplete")
        return result
    except Exception as error:
        return {"status": "FAILED", "error_type": type(error).__name__,
                "detail": str(error)[:200], "winerror": getattr(error, "winerror", None)}
    finally:
        if api and inherited.value:
            api.CloseHandle(inherited)


def collect(handle, pid, exe, output):
    import msvcrt
    exe, directory = validate_paths(exe, output.parent)
    if output.suffix != ".dmp" or output.parent.resolve() != directory:
        raise ValueError("invalid dump output")
    api = kernel()
    verify_handle(api, handle, pid, exe)
    dbg = c.WinDLL("dbghelp.dll", use_last_error=True, winmode=0x800)
    dbg.MiniDumpWriteDump.argtypes = [W.HANDLE, W.DWORD, W.HANDLE, W.DWORD,
                                     c.c_void_p, c.c_void_p, c.c_void_p]
    dbg.MiniDumpWriteDump.restype = W.BOOL
    # MiniDumpNormal | MiniDumpWithThreadInfo. No full-memory/token/handle dump.
    with output.open("xb", buffering=0) as stream:
        if not dbg.MiniDumpWriteDump(handle, pid, msvcrt.get_osfhandle(stream.fileno()),
                                    0x1000, None, None, None):
            raise c.WinError(c.get_last_error())
        os.fsync(stream.fileno())
    if output.stat().st_size > 64 * 1024**2:
        raise ValueError("dump validation size bound")
    result = {"status": "CAPTURED", "pid": pid, "dump": str(output),
              "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
              **summarize(output.read_bytes())}
    output.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle", type=int, required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = collect(args.handle, args.pid, args.exe, args.output)
    except Exception as error:
        print(json.dumps({"status": "FAILED", "error_type": type(error).__name__,
                          "detail": str(error)[:200], "winerror": getattr(error, "winerror", None)}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

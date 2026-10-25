"""Offline, single-address PE/PDB symbol lookup for an explicitly supplied module.

Read-only: no debugger, process attach, registry changes, network or symbol downloads.
Works on 64-bit Windows. Output excludes local paths and arbitrary process memory.
A faulting symbol is NOT the exception-time caller stack or the crash root cause.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import struct
import sys

from inspect_release_symbols import pe_codeview, msf_pdb_identity


class SymbolInfo(ctypes.Structure):
    _fields_ = [
        ("SizeOfStruct", wintypes.DWORD),
        ("TypeIndex", wintypes.DWORD),
        ("Reserved", ctypes.c_uint64 * 2),
        ("Index", wintypes.DWORD),
        ("Size", wintypes.DWORD),
        ("ModBase", ctypes.c_uint64),
        ("Flags", wintypes.DWORD),
        ("Value", ctypes.c_uint64),
        ("Address", ctypes.c_uint64),
        ("Register", wintypes.DWORD),
        ("Scope", wintypes.DWORD),
        ("Tag", wintypes.DWORD),
        ("NameLen", wintypes.DWORD),
        ("MaxNameLen", wintypes.DWORD),
        ("Name", ctypes.c_char * 1),
    ]


def image_info(module: Path) -> tuple[int, int]:
    with module.open("rb") as stream:
        header = stream.read(4096)
    if len(header) < 512 or header[:2] != b"MZ":
        raise ValueError("not a PE image")
    pe = struct.unpack_from("<I", header, 0x3C)[0]
    if pe + 24 + 60 > len(header) or header[pe:pe + 4] != b"PE\0\0":
        raise ValueError("invalid PE header")
    machine = struct.unpack_from("<H", header, pe + 4)[0]
    magic = struct.unpack_from("<H", header, pe + 24)[0]
    stamp = struct.unpack_from("<I", header, pe + 8)[0]
    size = struct.unpack_from("<I", header, pe + 24 + 56)[0]
    if machine != 0x8664 or magic != 0x20B or not 0 < size < 1 << 30:
        raise ValueError("expected bounded x64 PE32+ image")
    return stamp, size


def resolve(module: Path, pdb: Path, rva: int, expected_stamp: int | None) -> dict:
    if os.name != "nt" or struct.calcsize("P") != 8:
        raise RuntimeError("requires 64-bit Windows")
    if not module.is_file() or module.suffix.lower() not in (".dll", ".exe"):
        raise ValueError("expected an existing DLL or EXE")
    if not pdb.is_file() or pdb.suffix.lower() != ".pdb":
        raise ValueError("expected an existing PDB")
    if module.stem.casefold() != pdb.stem.casefold():
        raise ValueError("module/PDB filename mismatch")
    if module.is_symlink() or pdb.is_symlink():
        raise ValueError("reparse/symbolic link input not supported")
    if module.stat().st_size > 256 * 1024 * 1024 or pdb.stat().st_size > 512 * 1024 * 1024:
        raise ValueError("oversized input")
    timestamp, size = image_info(module)
    if expected_stamp is not None and timestamp != expected_stamp:
        raise ValueError("PE COFF timestamp mismatch")
    if not 0 <= rva < size:
        raise ValueError("RVA outside PE SizeOfImage")

    cv = pe_codeview(module)
    info = msf_pdb_identity(pdb)
    if cv != info:
        raise ValueError("PE CodeView GUID/age differs from PDB")
    # DbgHelp reads *only the explicitly supplied local folder*. No srv* search.
    system = Path(os.environ["SystemRoot"]) / "System32"
    dbghelp = ctypes.WinDLL(str(system / "dbghelp.dll"), use_last_error=True)
    kernel = ctypes.WinDLL(str(system / "kernel32.dll"), use_last_error=True)
    handle_t = ctypes.c_void_p
    kernel.CreateEventW.argtypes = (handle_t, wintypes.BOOL, wintypes.BOOL, ctypes.c_wchar_p)
    kernel.CreateEventW.restype = handle_t
    kernel.CloseHandle.argtypes = (handle_t,)
    kernel.CloseHandle.restype = wintypes.BOOL
    dbghelp.SymSetOptions.argtypes = (wintypes.DWORD,)
    dbghelp.SymSetOptions.restype = wintypes.DWORD
    dbghelp.SymInitializeW.argtypes = (handle_t, ctypes.c_wchar_p, wintypes.BOOL)
    dbghelp.SymInitializeW.restype = wintypes.BOOL
    dbghelp.SymLoadModuleExW.argtypes = (
        handle_t, handle_t, ctypes.c_wchar_p, ctypes.c_wchar_p,
        ctypes.c_uint64, wintypes.DWORD, handle_t, wintypes.DWORD)
    dbghelp.SymLoadModuleExW.restype = ctypes.c_uint64
    dbghelp.SymFromAddr.argtypes = (
        handle_t, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(SymbolInfo))
    dbghelp.SymFromAddr.restype = wintypes.BOOL
    dbghelp.SymCleanup.argtypes = (handle_t,)
    dbghelp.SymCleanup.restype = wintypes.BOOL

    token = kernel.CreateEventW(None, False, False, None)
    if not token:
        raise RuntimeError("cannot create private symbol session token")
    initialized = False
    try:
        # EXACT_SYMBOLS | NO_PROMPTS | FAIL_CRITICAL_ERRORS; no network symbol path.
        dbghelp.SymSetOptions(0x400 | 0x80000 | 0x200 | 0x2)
        if not dbghelp.SymInitializeW(token, str(pdb.parent), False):
            raise RuntimeError("SymInitializeW failed")
        initialized = True
        base = 0x180000000
        loaded = dbghelp.SymLoadModuleExW(token, None, str(module), None, base, 0, None, 0)
        if not loaded:
            raise RuntimeError("SymLoadModuleExW failed")
        reserve = 1024
        buffer = ctypes.create_string_buffer(ctypes.sizeof(SymbolInfo) + reserve)
        sym = ctypes.cast(buffer, ctypes.POINTER(SymbolInfo))
        sym.contents.SizeOfStruct = ctypes.sizeof(SymbolInfo)
        sym.contents.MaxNameLen = reserve
        displacement = ctypes.c_uint64(0)
        if not dbghelp.SymFromAddr(token, base + rva, ctypes.byref(displacement), sym):
            raise RuntimeError("SymFromAddr failed; symbol not available locally")
        name_len = int(sym.contents.NameLen)
        if not 1 <= name_len < reserve:
            raise RuntimeError("invalid symbol name length")
        offset = SymbolInfo.Name.offset
        name = buffer.raw[offset:offset + name_len].decode("utf-8", errors="replace")
        if not name.isprintable():
            raise RuntimeError("unexpected symbol name")
        return {
            "status": "LOCAL_SYMBOL_RESOLVED",
            "module": module.name,
            "rva": f"0x{rva:X}",
            "coff_timestamp": f"{timestamp:08X}",
            "pdb_guid": str(cv[0]),
            "pdb_age": cv[1],
            "nearest_symbol": name[:512],
            "symbol_displacement": int(displacement.value),
            "note": "Symbol only; no exception-time stack or proof of root cause",
        }
    finally:
        if initialized:
            dbghelp.SymCleanup(token)
        kernel.CloseHandle(token)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--pdb", type=Path, required=True)
    parser.add_argument("--rva", type=lambda s: int(s, 0), required=True)
    parser.add_argument("--expected-stamp", type=lambda s: int(s, 16))
    args = parser.parse_args()
    try:
        result = resolve(args.module, args.pdb, args.rva, args.expected_stamp)
    except (OSError, ValueError, RuntimeError, struct.error, KeyError) as exc:
        print(json.dumps({"status": "LOCAL_SYMBOL_LOOKUP_FAILED", "error": type(exc).__name__}))
        return 2
    print("G01_LOCAL_FAULT_SYMBOL=" + json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

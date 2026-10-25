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


# Only fixed, reviewed failure codes may cross the CI-log boundary.
# Never print exception messages: parsing failures can embed local paths.
_REJECTION_CODES = {
    "not a PE image": "PE_SIGNATURE_INVALID",
    "invalid PE header": "PE_HEADER_INVALID",
    "expected bounded x64 PE32+ image": "PE_ARCH_OR_SIZE_INVALID",
    "not a bounded PE image": "PE_SIGNATURE_INVALID",
    "missing PE header": "PE_HEADER_INVALID",
    "unreasonable PE sections": "PE_SECTION_COUNT_INVALID",
    "truncated section table": "PE_SECTION_TABLE_TRUNCATED",
    "not a supported PE optional header": "PE_OPTIONAL_HEADER_UNSUPPORTED",
    "no debug data directory": "PE_DEBUG_DIRECTORY_ABSENT",
    "missing bounded debug entries": "PE_DEBUG_ENTRIES_INVALID",
    "debug RVA outside available file section": "PE_DEBUG_RVA_INVALID",
    "unbounded CodeView entry": "PE_CODEVIEW_ENTRY_INVALID",
    "expected one PE CodeView RSDS identity": "PE_RSDS_IDENTITY_AMBIGUOUS",
    "not an MSF7 PDB": "PDB_MAGIC_INVALID",
    "unsupported MSF block size": "PDB_BLOCK_SIZE_UNSUPPORTED",
    "unreasonable MSF stream directory": "PDB_DIRECTORY_INVALID",
    "unsupported MSF block-map span": "PDB_BLOCK_MAP_SPAN_UNSUPPORTED",
    "MSF block outside PDB": "PDB_STREAM_BLOCK_INVALID",
    "short MSF block": "PDB_STREAM_BLOCK_TRUNCATED",
    "bad MSF stream directory count": "PDB_STREAM_COUNT_INVALID",
    "truncated MSF stream blocks": "PDB_STREAM_TABLE_TRUNCATED",
    "invalid PDB information stream": "PDB_INFO_STREAM_INVALID",
    "out of bounds metadata": "BOUNDS_INVALID",
}


class SymbolValidationError(ValueError):
    def __init__(self, stage: str, reason: str):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason


def _checked(stage: str, operation):
    try:
        return operation()
    except (ValueError, struct.error) as exc:
        raise SymbolValidationError(
            stage, _REJECTION_CODES.get(str(exc), "PARSE_REJECTED")
        ) from None


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


def probe_module(module: Path, expected_stamp: int | None) -> dict:
    """Check only a local PE: no PDB, symbols, debugger, or network required."""
    if not module.is_file() or module.suffix.lower() not in (".dll", ".exe"):
        raise ValueError("expected an existing DLL or EXE")
    if module.is_symlink() or module.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("unsafe or oversized PE")
    timestamp, size = _checked("PE_HEADER", lambda: image_info(module))
    if expected_stamp is not None and timestamp != expected_stamp:
        raise SymbolValidationError("PE_TIMESTAMP", "STAMP_MISMATCH")
    guid, age = _checked("PE_CODEVIEW", lambda: pe_codeview(module))
    return {
        "status": "LOCAL_PE_PROBE_OK",
        "module": module.name,
        "coff_timestamp": f"{timestamp:08X}",
        "image_size": size,
        "pdb_guid": str(guid),
        "pdb_age": age,
    }


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
    timestamp, size = _checked("PE_HEADER", lambda: image_info(module))
    if expected_stamp is not None and timestamp != expected_stamp:
        raise SymbolValidationError("PE_TIMESTAMP", "STAMP_MISMATCH")
    if not 0 <= rva < size:
        raise SymbolValidationError("PE_RVA", "RVA_OUT_OF_IMAGE")

    cv = _checked("PE_CODEVIEW", lambda: pe_codeview(module))
    info = _checked("PDB_MSF7", lambda: msf_pdb_identity(pdb))
    if cv != info:
        raise SymbolValidationError("PDB_IDENTITY", "GUID_AGE_MISMATCH")
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
    parser.add_argument("--pdb", type=Path)
    parser.add_argument("--rva", type=lambda s: int(s, 0))
    parser.add_argument("--expected-stamp", type=lambda s: int(s, 16))
    parser.add_argument("--probe-module", action="store_true",
                        help="validate only the local PE image and CodeView identity")
    args = parser.parse_args()
    if not args.probe_module and (args.pdb is None or args.rva is None):
        parser.error("--pdb and --rva are required unless --probe-module is set")
    if args.probe_module and (args.pdb is not None or args.rva is not None):
        parser.error("--probe-module does not accept --pdb or --rva")
    try:
        if args.probe_module:
            result = probe_module(args.module, args.expected_stamp)
        else:
            result = resolve(args.module, args.pdb, args.rva, args.expected_stamp)
    except (OSError, ValueError, RuntimeError, struct.error, KeyError) as exc:
        details = {"status": "LOCAL_SYMBOL_LOOKUP_FAILED",
                   "stage": "MODULE_PROBE" if args.probe_module else "RVA_LOOKUP",
                   "error": type(exc).__name__}
        if isinstance(exc, SymbolValidationError):
            details["stage"] = exc.stage
            details["reason"] = exc.reason
        print(json.dumps(details, sort_keys=True))
        return 2
    prefix = "G01_LOCAL_PE_PROBE=" if args.probe_module else "G01_LOCAL_FAULT_SYMBOL="
    print(prefix + json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

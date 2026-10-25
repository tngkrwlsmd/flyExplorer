"""Synthetic, offline G01 PE/PDB preflight regressions.

No Windows VM, debugger, symbol server, registry, process dump or real-user files.
The tests use only temporary, synthetic PE32+ and MSF7 byte arrays.
"""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import uuid

TOOL_DIR = Path(__file__).resolve().parents[2] / "tools" / "winui"
sys.path.insert(0, str(TOOL_DIR))
import inspect_release_symbols as symbols  # noqa: E402
import resolve_local_rva as resolver  # noqa: E402


STAMP = 0x05FCB77A
GUID = uuid.UUID("4acDBE85-d668-192e-b8b6-a9334ac91b79")


def synthetic_pe(path: Path, guid: uuid.UUID = GUID, age: int = 1) -> None:
    data = bytearray(0x1400)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    pe = 0x80
    data[pe:pe + 4] = b"PE\0\0"
    struct.pack_into("<H", data, pe + 4, 0x8664)
    struct.pack_into("<H", data, pe + 6, 1)
    struct.pack_into("<I", data, pe + 8, STAMP)
    struct.pack_into("<H", data, pe + 20, 0xF0)
    optional = pe + 24
    struct.pack_into("<H", data, optional, 0x20B)
    struct.pack_into("<I", data, optional + 56, 0x3000)
    struct.pack_into("<II", data, optional + 160, 0x1010, 28)
    section = optional + 0xF0
    struct.pack_into("<IIII", data, section + 8, 0x1000, 0x1000, 0x1000, 0x200)
    struct.pack_into("<II", data, 0x210 + 12, 2, 28)
    struct.pack_into("<I", data, 0x210 + 24, 0x300)
    data[0x300:0x304] = b"RSDS"
    data[0x304:0x314] = guid.bytes_le
    struct.pack_into("<I", data, 0x314, age)
    path.write_bytes(data)


def synthetic_pdb(path: Path, guid: uuid.UUID = GUID, age: int = 1) -> None:
    size = 4096
    data = bytearray(8 * size)
    data[:32] = b"Microsoft C/C++ MSF 7.00\r\n\x1aDS\0\0\0"
    struct.pack_into("<6I", data, 32, size, 1, 8, 32, 0, 4)
    struct.pack_into("<I", data, 4 * size, 5)  # directory block index
    struct.pack_into("<I", data, 5 * size, 6)  # six streams
    struct.pack_into("<6I", data, 5 * size + 4, 0, 64, 0, 0, 0, 0)
    struct.pack_into("<I", data, 5 * size + 28, 6)  # PDB info stream block
    struct.pack_into("<I", data, 6 * size + 8, age)
    data[6 * size + 12:6 * size + 28] = guid.bytes_le
    path.write_bytes(data)


class G01OfflinePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="fly-g01-synthetic-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.pe = root / "Microsoft.UI.Xaml.dll"
        self.pdb = root / "Microsoft.UI.Xaml.pdb"
        synthetic_pe(self.pe)
        synthetic_pdb(self.pdb)

    def test_synthetic_pe_and_pdb_have_matching_codeview_identity(self) -> None:
        self.assertEqual(symbols.pe_codeview(self.pe), (GUID, 1))
        self.assertEqual(symbols.msf_pdb_identity(self.pdb), (GUID, 1))
        result = resolver.probe_module(self.pe, STAMP)
        self.assertEqual(result["status"], "LOCAL_PE_PROBE_OK")
        self.assertEqual(result["pdb_guid"], str(GUID))
        self.assertEqual(result["coff_timestamp"], "05FCB77A")

    def test_coff_timestamp_mismatch_has_fixed_stage_and_reason(self) -> None:
        with self.assertRaises(resolver.SymbolValidationError) as caught:
            resolver.probe_module(self.pe, 0x12345678)
        self.assertEqual((caught.exception.stage, caught.exception.reason),
                         ("PE_TIMESTAMP", "STAMP_MISMATCH"))

    def test_missing_debug_directory_has_non_sensitive_error_code(self) -> None:
        data = bytearray(self.pe.read_bytes())
        # Clear the PE32+ debug directory without exposing any real PDB paths.
        struct.pack_into("<II", data, 0x80 + 24 + 160, 0, 0)
        self.pe.write_bytes(data)
        with self.assertRaises(resolver.SymbolValidationError) as caught:
            resolver.probe_module(self.pe, STAMP)
        self.assertEqual((caught.exception.stage, caught.exception.reason),
                         ("PE_CODEVIEW", "PE_DEBUG_ENTRIES_INVALID"))

    def test_invalid_pdb_map_fails_closed_with_structured_reason(self) -> None:
        data = bytearray(self.pdb.read_bytes())
        struct.pack_into("<I", data, 32 + 20, 100)  # beyond NumBlocks
        self.pdb.write_bytes(data)
        with self.assertRaises(resolver.SymbolValidationError) as caught:
            resolver._checked("PDB_MSF7", lambda: symbols.msf_pdb_identity(self.pdb))
        self.assertEqual((caught.exception.stage, caught.exception.reason),
                         ("PDB_MSF7", "PDB_BLOCK_MAP_SPAN_UNSUPPORTED"))

    def test_unknown_parser_message_is_redacted(self) -> None:
        def fail() -> None:
            raise ValueError("private-user-path/should-never-be-logged")
        with self.assertRaises(resolver.SymbolValidationError) as caught:
            resolver._checked("PDB_MSF7", fail)
        self.assertEqual(caught.exception.reason, "PARSE_REJECTED")
        self.assertNotIn("private", str(caught.exception))

    def test_probe_cli_requires_no_pdb_and_returns_bounded_json(self) -> None:
        argv = sys.argv
        try:
            sys.argv = ["resolve_local_rva.py", "--probe-module", "--module",
                        str(self.pe), "--expected-stamp", "05FCB77A"]
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = resolver.main()
            self.assertEqual(code, 0)
            self.assertIn("G01_LOCAL_PE_PROBE=", stdout.getvalue())
        finally:
            sys.argv = argv


if __name__ == "__main__":
    unittest.main()

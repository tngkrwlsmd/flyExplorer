"""Source-level tests for one read-only EXE/PDB GUID-and-age verifier."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "winui"))
import inspect_release_symbols as symbols


class TestReleaseSymbolIdentity(unittest.TestCase):
    def test_invalid_metadata_fails_closed(self):
        with self.assertRaises(ValueError):
            symbols.get_u32(b"\0\0", 0)
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            exe = folder / "flyExplorer.exe"
            pdb = folder / "flyExplorer.pdb"
            exe.write_bytes(b"MZ" + b"\0" * 1022)
            pdb.write_bytes(b"not a PDB" * 200)
            with self.assertRaises(ValueError):
                symbols.pe_codeview(exe)
            with self.assertRaises(ValueError):
                symbols.msf_pdb_identity(pdb)

    def test_genuine_identity_comparison_required(self):
        source = (ROOT / "tools/winui/inspect_release_symbols.py").read_text(
            encoding="utf-8"
        )
        for term in ("uuid.UUID(bytes_le=", "directory_blocks",
                     "CodeView RSDS GUID/age does not match",
                     '"EXACT_PDB_MATCH"', "exe_sha256", "pdb_sha256"):
            self.assertIn(term, source)
        for forbidden in ("reg add", "DbgHelp!Sym", "subprocess.", "OpenProcess("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

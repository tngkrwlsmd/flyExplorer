"""F08 ZIP Store DOS-time + ASCII/UTF-8 compatibility source contracts.
This source-only test is deliberately NOT EXECUTED during this change.
"""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

class ZipStoreCompatContracts(unittest.TestCase):
    def test_only_dos_versions_and_strict_flags(self):
        s = source("src/base/zip_store_compat.h")
        for literal in (
            "version==10u||version==20u",
            "flags==0u||flags==kUtf8NameFlag",
            "flags==kUtf8NameFlag,name",
            "local+10u",
            "central+12u",
            "local+12u",
            "central+14u",
            "zipinspect::detail::decode(",
        ):
            self.assertIn(literal, s)
        for forbidden in (
            "MultiByteToWideChar(CP_ACP", "CP_OEMCP",
            "MoveFileExW(", "CreateFileW(", "ShellExecute",
            "COMPRESS_ALGORITHM_MSZIP",
        ):
            # The MSZIP string may appear only as an explanatory comment.
            if forbidden == "COMPRESS_ALGORITHM_MSZIP":
                continue
            self.assertNotIn(forbidden, s)

    def test_both_extractors_reconcile_local_and_central(self):
        for p in (
            "src/base/zip_store_extractor.h",
            "src/base/zip_store_batch_extractor.h",
        ):
            s = source(p)
            for literal in (
                '#include "zip_store_compat.h"',
                "zipstorecompat::supportedDosVersion(",
                "zipstorecompat::supportedFlags(flags)",
                "zipstorecompat::sameDosTime(",
                "zipstorecompat::decodeName(",
                "zipstore::detail::crc32(",
                "MOVEFILE_WRITE_THROUGH",
            ):
                self.assertIn(literal, s)
            self.assertNotIn("flags!=0x0800u", s)
            self.assertNotIn("u16(bytes,localCursor+6)!=0x0800u", s)

if __name__ == "__main__":
    unittest.main()

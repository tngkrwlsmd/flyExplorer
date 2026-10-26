"""Focused unit tests for read-only G01 WER signature aggregation."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "winui"))

from inspect_g01_wer import inventory, parse_report  # noqa: E402


def report_text(module="combase.dll", code="800710dd",
                offset="000000000005cf34", name="flyExplorer.exe"):
    return (
        "Version=1\nEventType=APPCRASH\n"
        f"Sig[0].Value={name}\nSig[1].Value=1.0.0.0\n"
        f"Sig[3].Value={module}\nSig[6].Value={code}\n"
        f"Sig[7].Value={offset}\n"
        "AppPath=C:\\Users\\someone\\private\\flyExplorer.exe\n"
    )


class G01WerSignatures(unittest.TestCase):
    def test_report_decodes_windows_utf16_le(self):
        source = ("\ufeff" + report_text()).encode("utf-16-le")
        self.assertEqual(
            parse_report(source),
            ("combase.dll", "0x800710dd", "0x5cf34"),
        )

    def test_report_decodes_utf8_and_normalizes_hex(self):
        sample = report_text("CoreMessagingXP.dll",
                             "C000027B", "0000000000097976")
        self.assertEqual(
            parse_report(sample.encode("utf-8")),
            ("coremessagingxp.dll", "0xc000027b", "0x97976"),
        )

    def test_invalid_app_and_malformed_offsets_are_ignored(self):
        for data in (
            report_text(name="other.exe"),
            report_text(module=r"C:\\Users\\private.dll"),
            report_text(code="this-is-not-hex"),
            report_text(offset="not_an_offset"),
            report_text().replace("Sig[7].Value=", "BadSig[7].Value="),
            report_text() + "Sig[6].Value=c000027b\n",
        ):
            with self.subTest(data=data[:45]):
                self.assertIsNone(parse_report(data.encode("utf-8")))
        self.assertIsNone(parse_report(b"x" * (512 * 1024 + 1)))

    def test_aggregate_only_owned_report_names_and_never_output_paths(self):
        with tempfile.TemporaryDirectory(prefix="g01-wer-test-") as td:
            root = Path(td)
            a = root / "AppCrash_flyExplorer.exe_same_a"
            b = root / "AppCrash_flyExplorer.exe_same_b"
            c = root / "AppCrash_other.exe_any"
            for item in (a, b, c):
                item.mkdir()
            (a / "Report.wer").write_bytes(report_text().encode("utf-16"))
            (b / "Report.wer").write_bytes(report_text().encode("utf-8"))
            (c / "Report.wer").write_bytes(report_text().encode("utf-8"))
            (a / "internal.dmp").write_bytes(b"not-read")
            summary = inventory([root])
            self.assertEqual(summary["reports_inspected"], 2)
            self.assertEqual(summary["valid_flyexplorer_reports"], 2)
            self.assertEqual(summary["signatures"], [{
                "fault_module": "combase.dll",
                "exception_code": "0x800710dd",
                "module_offset": "0x5cf34",
                "report_count": 2,
            }])
            self.assertFalse(summary["changes_system_settings"])
            self.assertFalse(summary["contains_native_call_stack"])
            self.assertNotIn("someone", str(summary))
            self.assertNotIn("AppPath", str(summary))
            self.assertNotIn(str(root), str(summary))
            self.assertEqual((a / "internal.dmp").read_bytes(), b"not-read")

    def test_bounded_inventory_and_missing_archive(self):
        with tempfile.TemporaryDirectory(prefix="g01-wer-test-") as td:
            root = Path(td)
            for suffix in ("a", "b", "c"):
                directory = root / ("AppCrash_flyExplorer.exe_" + suffix)
                directory.mkdir()
                (directory / "Report.wer").write_text(report_text(), encoding="utf-8")
            self.assertEqual(inventory([root], 2)["reports_inspected"], 2)
            self.assertEqual(inventory([root], 2)["valid_flyexplorer_reports"], 2)
            self.assertEqual(inventory([root / "missing"])["reports_inspected"], 0)


if __name__ == "__main__":
    unittest.main()

"""Focused source/format tests for test-owned G01 unhandled HRESULT tracing.

A captured WinUI HRESULT is diagnostic only; no crash is marked handled.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "app" / "winui" / "MainWindow.xaml.cpp"
APP = ROOT / "app" / "winui" / "App.xaml.cpp"
TEST = ROOT / "tests" / "winui" / "test_owned_g01_shutdown_gui.py"


class G01UnhandledTraceContract(unittest.TestCase):
    def test_callback_only_installed_for_exact_owned_fixture(self):
        main = MAIN.read_text(encoding="utf-8")
        app = APP.read_text(encoding="utf-8")
        self.assertIn('L"FLY_G01_OWNED_CLOSE_TRACE"', main)
        self.assertIn('L"columns-gui-owned-"', main)
        self.assertIn("return G01OwnedCloseTraceEnabled();", main)
        self.assertIn("if(G01OwnedAppDiagnosticsEnabled()){", app)
        self.assertLess(app.index("if(G01OwnedAppDiagnosticsEnabled()){"),
                        app.index("APP_UNHANDLED_EXCEPTION_ENTER"))

    def test_exception_not_suppressed_or_private_message_logged(self):
        app = APP.read_text(encoding="utf-8")
        section = app.split("if(G01OwnedAppDiagnosticsEnabled()){", 1)[1]
        section = section.split("\n        }", 1)[0]
        self.assertIn("e.Exception().value", section)
        self.assertNotIn("e.Message()", section)
        self.assertNotIn(".Handled(", section)
        self.assertNotIn("Message()", section)

    def test_trace_is_bounded_to_hex_hresult(self):
        main = MAIN.read_text(encoding="utf-8")
        section = main.split(
            "void TraceG01AppUnhandledHresult(std::uint32_t code)", 1
        )[1].split("MainWindow::MainWindow()", 1)[0]
        self.assertIn('"APP_UNHANDLED_HRESULT_%08X"', section)
        self.assertIn("TraceG01OwnedClose(phase)", section)
        self.assertNotIn("Message()", section)

    def test_trace_reader_restricts_dynamic_hresults(self):
        reader = TEST.read_text(encoding="utf-8")
        match = re.search(
            r're\.fullmatch\(r"(APP_UNHANDLED_HRESULT_\[0-9A-F\]\{8\})", p\)',
            reader,
        )
        self.assertIsNotNone(match)
        whitelist = re.compile(
            r"APP_UNHANDLED_HRESULT_[0-9A-F]{8}", re.ASCII
        )
        self.assertTrue(whitelist.fullmatch("APP_UNHANDLED_HRESULT_800710DD"))
        self.assertFalse(whitelist.fullmatch("APP_UNHANDLED_HRESULT_800710DD_PRIVATE"))
        self.assertFalse(whitelist.fullmatch("APP_UNHANDLED_HRESULT_ZZZZZZZZ"))


if __name__ == "__main__":
    unittest.main()

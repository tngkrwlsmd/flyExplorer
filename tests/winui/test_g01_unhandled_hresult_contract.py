"""G01 owned-only WinUI unhandled-HRESULT probe source contracts.

No debugger, dumps or global WER changes. Runtime results are separately
verified by focused owned Windows Release GUI scenarios.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui" / "App.xaml.cpp"
WINDOW = ROOT / "app" / "winui" / "MainWindow.xaml.cpp"
HARNESS = ROOT / "tests" / "winui" / "test_owned_g01_shutdown_gui.py"


class G01OwnedHresultContract(unittest.TestCase):
    def test_handler_gated_to_owned_trace_and_only_observes(self):
        code = APP.read_text(encoding="utf-8")
        start = code.index("if(G01OwnedAppDiagnosticsEnabled()){")
        stop = code.index("\n        }", start)
        handler = code[start:stop]
        self.assertIn("UnhandledException(", handler)
        self.assertIn("TraceG01AppUnhandledHresult(", handler)
        self.assertIn("e.Exception().value", handler)
        self.assertNotIn("e.Handled(", handler)
        self.assertNotIn("e.Message(", handler)
        self.assertNotIn("throw ", handler)

    def test_test_owned_environment_and_temp_marker_both_required(self):
        code = WINDOW.read_text(encoding="utf-8")
        start = code.index("bool G01OwnedCloseTraceEnabled() noexcept")
        stop = code.index("void TraceG01OwnedClose(", start)
        gate = code[start:stop]
        self.assertIn('L"FLY_G01_OWNED_CLOSE_TRACE"', gate)
        self.assertIn('std::wcscmp(enabled,L"YES")', gate)
        self.assertIn('L"columns-gui-owned-"', gate)
        self.assertIn("GetTempPathW(", gate)
        self.assertIn("return false", gate)

    def test_only_uppercase_fixed_width_hresult_is_written(self):
        code = WINDOW.read_text(encoding="utf-8")
        start = code.index("void TraceG01AppUnhandledHresult(")
        stop = code.index("MainWindow::MainWindow()", start)
        body = code[start:stop]
        self.assertIn('"APP_UNHANDLED_HRESULT_%08X"', body)
        self.assertIn("TraceG01OwnedClose(phase)", body)
        self.assertNotIn("Message()", body)
        self.assertNotIn("GetLastError", body)

    def test_fixture_binds_trace_to_synthetic_profile_only(self):
        code = HARNESS.read_text(encoding="utf-8")
        self.assertIn('"FLY_G01_OWNED_CLOSE_TRACE": "YES"', code)
        self.assertIn('prefix="columns-gui-owned-"', code)
        for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
            self.assertIn(f'"{key}"', code)
        self.assertIn(
            r'APP_UNHANDLED_HRESULT_[0-9A-F]{8}', code
        )
        self.assertIn('"APP_UNHANDLED_EXCEPTION_ENTER"', code)
        self.assertIn('"APP_UNHANDLED_EXCEPTION_EXIT"', code)

    def test_old_close_behavior_and_tokens_remain(self):
        code = WINDOW.read_text(encoding="utf-8")
        self.assertIn(
            'TraceG01OwnedClose("QUEUED_XAML_TIMERS_STOPPED")',
            code,
        )
        self.assertIn(
            'TraceG01OwnedClose("WINDOW_CLOSED_EXIT")',
            code,
        )


if __name__ == "__main__":
    unittest.main()

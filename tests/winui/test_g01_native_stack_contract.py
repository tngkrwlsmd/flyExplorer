"""Contracts for opt-in, observe-only x64 native stowed-exception trace."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui" / "App.xaml.cpp"
GUI = ROOT / "tests" / "winui" / "test_owned_g01_shutdown_gui.py"

class G01NativeStackContract(unittest.TestCase):
    def test_only_g01_owned_fixture_registers_and_removes_observer(self):
        app = APP.read_text(encoding="utf-8")
        start = app.index("if(G01OwnedAppDiagnosticsEnabled()){")
        self.assertLess(start, app.index("AddVectoredExceptionHandler("))
        self.assertIn("RemoveVectoredExceptionHandler(mG01NativeExceptionHandler)", app)
        self.assertIn("#if defined(_M_X64)", app)

    def test_only_stowed_status_and_never_handle_exception(self):
        app = APP.read_text(encoding="utf-8")
        section = app.split("LONG CALLBACK ObserveG01NativeStowed(", 1)[1].split(
            "#endif", 1)[0]
        self.assertIn("ExceptionRecord->ExceptionCode != 0xC000027B", section)
        self.assertIn("EXCEPTION_CONTINUE_SEARCH", section)
        self.assertNotIn("EXCEPTION_CONTINUE_EXECUTION", section)
        self.assertNotIn("MiniDumpWriteDump", section)

    def test_fault_context_unwinds_only_bounded_relative_frames(self):
        app = APP.read_text(encoding="utf-8")
        section = app.split("LONG CALLBACK ObserveG01NativeStowed(", 1)[1].split(
            "#endif", 1)[0]
        for value in ("*exception->ContextRecord", "RtlLookupFunctionEntry",
                      "RtlVirtualUnwind", "RtlPcToFileHeader",
                      "index < 8", "rva <= 0xFFFFFFFFull",
                      "NATIVE_STOWED_FRAME_%02u_%s_%08X"):
            self.assertIn(value, app if value == "RtlPcToFileHeader" else section)
        self.assertNotIn("ExceptionInformation[", section)
        self.assertNotIn("Message()", section)

    def test_harness_accepts_only_fixed_native_frame_tokens(self):
        source = GUI.read_text(encoding="utf-8")
        pattern = re.compile(
            r"NATIVE_STOWED_FRAME_0[0-7]_(?:FLY|XAML|COMBASE|COREMSG|NTDLL|OTHER)_[0-9A-F]{8}",
            re.ASCII)
        self.assertIn("NATIVE_STOWED_ENTER", source)
        self.assertIn("NATIVE_STOWED_EXIT", source)
        self.assertIn(pattern.pattern, source)
        self.assertTrue(pattern.fullmatch("NATIVE_STOWED_FRAME_00_XAML_00097976"))
        for item in (
            "NATIVE_STOWED_FRAME_08_XAML_00097976",
            "NATIVE_STOWED_FRAME_00_XAML_C:\\private",
            "NATIVE_STOWED_FRAME_00_OTHER_0123ZZZZ"):
            self.assertIsNone(pattern.fullmatch(item))

if __name__ == "__main__":
    unittest.main()

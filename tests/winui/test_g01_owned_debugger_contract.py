"""Portable synthetic source contracts for the test-owned x64 stowed debugger."""
import ctypes
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tests" / "winui" / "g01_owned_debugger.py"
HARNESS = ROOT / "tests" / "winui" / "test_owned_g01_shutdown_gui.py"
module_spec = importlib.util.spec_from_file_location("g01_owned_debugger", SOURCE)
observer = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(observer)


class G01OwnedDebuggerContract(unittest.TestCase):
    def test_windows_x64_structure_layout(self):
        self.assertEqual(observer.STOWED_V2.size, 56)
        self.assertEqual(ctypes.sizeof(observer.EXCEPTION_RECORD), 152)
        self.assertEqual(ctypes.sizeof(observer.DEBUG_EVENT), 176)

    def test_decodes_only_v2_and_preserves_hresult(self):
        data = struct.pack("<IIiIQIIQI4xQ", 56, 0x53453032,
                           -2147024891, 1, 0, 8, 2, 0x2000, 0, 0)
        self.assertEqual(observer.decode_v2(data),
                         (0x80070005, 2, 0x2000))
        self.assertIsNone(observer.decode_v2(bytes(56)))
        self.assertIsNone(observer.decode_v2(data[:-1]))
        self.assertEqual(observer.decode_v2(data[:24] + b"\xff\xff\xff\xff" +
                                               data[28:])[1], 0)

    def test_long_stowed_stack_preserves_bounded_prefix(self):
        data = struct.pack("<IIiIQIIQI4xQ", 56, 0x53453032,
                           -2147020579, 1, 0x100AB, 8, 24, 0x2000, 0, 0)
        self.assertEqual(observer.decode_v2(data), (0x800710DD, 16, 0x2000))
        self.assertEqual(observer.describe_v2(data, []),
                         ["FORM_BINARY", "WORDS_16", "STACK_TRUNCATED"])

    def test_classifies_stowed_form_stack_availability_and_origin(self):
        binary = struct.pack("<IIiIQIIQI4xQ", 56, 0x53453032,
                             -2147020579, 1, 0x100AB, 8, 0, 0, 0, 0)
        self.assertEqual(observer.describe_v2(
            binary, [(0x10000, 0x2000, "XAML")]),
            ["FORM_BINARY", "WORDS_0", "ORIGIN_XAML_000000AB"])
        text = struct.pack("<IIiIQIIQI4xQ", 56, 0x53453032,
                           -2147020579, 2, 0, 0, 0, 0, 0, 0)
        self.assertEqual(observer.describe_v2(text, []), ["FORM_TEXT"])
        self.assertIsNone(observer.describe_v2(bytes(56), []))

    def test_frame_labels_drop_unlisted_modules_and_addresses(self):
        modules = [(0x10000, 0x2000, "XAML")]
        self.assertEqual(observer.frame_label(0x100AB, modules),
                         "XAML_000000AB")
        self.assertIsNone(observer.frame_label(0xDEADBEEF, modules))
        self.assertNotIn("OTHER", observer.LABELS.values())

    def test_attach_and_memory_read_are_strictly_owned_and_bounded(self):
        text = SOURCE.read_text(encoding="utf-8")
        for required in ("columns-gui-owned-", "process.create_time()",
                         "DebugActiveProcess(pid)", "DebugActiveProcessStop(pid)",
                         "DebugSetProcessKillOnExit(False)", "size > 128",
                         "count > 16", "min(count, 4)",
                         "DBG_EXCEPTION_NOT_HANDLED", "g01-debugger-stop"):
            self.assertIn(required, text)
        for forbidden in ("MiniDumpWriteDump", "SetUnhandledExceptionFilter",
                          "WriteProcessMemory", "REG ADD", "PDE.DSE"):
            self.assertNotIn(forbidden, text)

    def test_harness_opt_in_only(self):
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn('debug_stowed=False', source)
        self.assertIn('"debug-stowed"', source)
        self.assertIn("G01_OWNED_DEBUGGER_ATTACHED", source)
        self.assertIn("G01_OWNED_DEBUG_STOWED_TRACE", source)
        self.assertIn("FORM_(?:BINARY|TEXT|UNKNOWN)", source)
        self.assertIn("MAPPED_", source)
        self.assertIn("G01_OWNED_GUI_FIXTURE_CLEANED=YES", source)


if __name__ == "__main__":
    unittest.main()

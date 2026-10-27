"""G01 synthetic startup phases: fixed in-memory page, no runtime file writes."""
import json
from pathlib import Path
import re
import struct
from tempfile import TemporaryDirectory
import unittest

from gui_failure_evidence import (
    G01_SHARED_MAGIC, G01_SHARED_FORMAT, G01_SHARED_PHASES,
    decode_g01_owned_shared_phases, _safe_g01_startup_events, capture_failure,
)

ROOT = Path(__file__).resolve().parents[2]
CPP = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
HARNESS = (ROOT / "tests/winui/test_shell_gui.py").read_text(encoding="utf-8")
EVIDENCE = (ROOT / "tests/winui/gui_failure_evidence.py").read_text(encoding="utf-8")


class G01NativeStartupPhaseContract(unittest.TestCase):
    def test_app_uses_only_test_owned_pid_mapping_not_file_io(self):
        helper = CPP.split("constexpr LONG kG01StartupMagic", 1)[1].split(
            "constexpr UINT_PTR kDetailColumnCursorSubclassId", 1)[0]
        for marker in (
            "FLY_G01_INTEGRATED_STARTUP_ONLY", 'L"shell-owned-"',
            'L"\\\\tmp\\\\"', "CreateFileMappingW", "MapViewOfFile",
            "GetCurrentProcessId()", "InterlockedIncrement",
            "InterlockedExchange", "kG01StartupCapacity=64",
            "Local\\\\flyExplorer-G01-startup-%lu",
        ):
            self.assertIn(marker, helper)
        for forbidden in (
            "WriteFile(", "CreateFileW(", "ReadProcessMemory",
            "WriteProcessMemory", "MiniDumpWriteDump", "FILE_APPEND_DATA"
        ):
            self.assertNotIn(forbidden, helper)
        names = CPP.split("char const* const kG01StartupPhases[]={", 1)[1].split(
            "};", 1)[0]
        self.assertEqual(list(G01_SHARED_PHASES),
                         re.findall(r'"([A-Z_]+)"', names))
        self.assertIn("mShellNavigation->accept(", CPP)

    def test_failure_reader_is_exact_pid_and_bounded_without_attach(self):
        self.assertIn("if G01_INTEGRATED_STARTUP_ONLY and p is not None:", HARNESS)
        self.assertIn("read_g01_owned_shared_phases(p.pid)", HARNESS)
        self.assertIn("startup_events=startup_events", HARNESS)
        for required in (
            "OpenFileMappingW", "MapViewOfFile", "0x0004",
            "ctypes.string_at(view, size)", "decode_g01_owned_shared_phases",
        ):
            self.assertIn(required, EVIDENCE)
        for forbidden in ("DebugActiveProcess", "OpenProcess(",
                          "ReadProcessMemory", "WriteProcessMemory"):
            self.assertNotIn(forbidden, EVIDENCE)

    def test_pid_and_magic_validation_rejects_untrusted_values(self):
        slots = [1, 7, 11, 16] + [0] * 60
        raw = struct.pack(G01_SHARED_FORMAT, G01_SHARED_MAGIC,
                          4102, 4, *slots)
        self.assertEqual(
            decode_g01_owned_shared_phases(raw, 4102),
            [G01_SHARED_PHASES[code - 1] for code in slots[:4]])
        self.assertEqual([], decode_g01_owned_shared_phases(raw, 4103))
        self.assertEqual([], decode_g01_owned_shared_phases(raw[:-1], 4102))
        corrupt = struct.pack(G01_SHARED_FORMAT, 0, 4102, 4, *slots)
        self.assertEqual([], decode_g01_owned_shared_phases(corrupt, 4102))
        overflow = struct.pack(G01_SHARED_FORMAT,
                               G01_SHARED_MAGIC, 4102, 513, *slots)
        self.assertEqual([], decode_g01_owned_shared_phases(overflow, 4102))
        self.assertEqual([], decode_g01_owned_shared_phases(raw, False))

    def test_only_allowlisted_stages_enter_failure_evidence(self):
        bad = "C:\\Users\\example\\private.txt"
        events = ["LEFT_SUBMIT_ACCEPTED", "RESULT_CALLBACK",
                  "RESULT_ENQUEUE_OK", "RIGHT_APPLIED", bad, "LEFT_FAILED"]
        self.assertEqual(
            events[:4] + events[-1:], _safe_g01_startup_events(events))
        self.assertEqual(
            64, len(_safe_g01_startup_events(["LEFT_FAILED"] * 200)))
        with TemporaryDirectory() as td:
            base = Path(td) / "phase6-winui"
            owned = base / "shell-owned-startup"
            left, right = owned / "Left", owned / "Right"
            left.mkdir(parents=True)
            right.mkdir()
            error = AssertionError(
                "UI-independent native core/helper was not active at startup")
            folder = capture_failure(
                base=base, owned=owned, left=left, right=right,
                win=None, hwnd=None, pid=None, error=error,
                startup_events=events)
            raw = (folder / "panes.json").read_text(encoding="utf-8")
            saved = json.loads(raw)["Startup"]["owned_native_events"]
            self.assertEqual(events[:4] + events[-1:], saved)
            self.assertNotIn(bad, raw)
            unrelated = capture_failure(
                base=base, owned=owned, left=left, right=right,
                win=None, hwnd=None, pid=None,
                error=AssertionError("different"), startup_events=events)
            self.assertNotIn("owned_native_events", json.loads(
                (unrelated / "panes.json").read_text("utf-8"))["Startup"])


if __name__ == "__main__":
    unittest.main()

"""G01-only owned startup trace: fixed stage names, no user paths."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gui_failure_evidence import _safe_g01_startup_events, capture_failure

ROOT = Path(__file__).resolve().parents[2]
CPP = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
HARNESS = (ROOT / "tests/winui/test_shell_gui.py").read_text(encoding="utf-8")

class G01NativeStartupPhaseContract(unittest.TestCase):
    def test_app_trace_is_strictly_test_owned_and_not_global(self):
        helper = CPP.split("void TraceG01OwnedStartup(char const* phase) noexcept", 1)[1].split(
            "constexpr UINT_PTR kDetailColumnCursorSubclassId", 1)[0]
        for marker in ("FLY_G01_INTEGRATED_STARTUP_ONLY", 'L"shell-owned-"',
                       'L"\\\\tmp\\\\"', "FILE_APPEND_DATA",
                       "GetCurrentProcessId()", "bytes<80"):
            self.assertIn(marker, helper)
        self.assertNotIn("WriteProcessMemory", helper)
        self.assertNotIn("MiniDumpWriteDump", helper)
        for phase in ("LEFT_SUBMIT_BEGIN", "RIGHT_SUBMIT_BEGIN",
                      "LEFT_SUBMIT_ACCEPTED", "RIGHT_SUBMIT_ACCEPTED",
                      "RESULT_CALLBACK", "RESULT_ENQUEUE_OK",
                      "RESULT_ENQUEUE_REJECTED", "RESULT_IGNORED",
                      "LEFT_APPLIED", "LEFT_FAILED", "LEFT_REJECTED",
                      "RIGHT_APPLIED", "RIGHT_FAILED"):
            self.assertIn('"'+phase+'"', CPP)
        self.assertIn("mShellNavigation->accept(", CPP)

    def test_failure_harness_only_reads_its_child_bounded_file(self):
        self.assertIn("if G01_INTEGRATED_STARTUP_ONLY and p is not None:", HARNESS)
        self.assertIn('native = temp / ("fly-g01-startup-" + str(p.pid) + ".log")',
                      HARNESS)
        self.assertIn("native.stat().st_size <= 4096", HARNESS)
        self.assertIn("not native.is_symlink()", HARNESS)
        self.assertIn("startup_events=startup_events", HARNESS)

    def test_only_allowlisted_phases_go_to_failure_evidence(self):
        bad = "C:\\Users\\example\\private.txt"
        events = ["LEFT_SUBMIT_ACCEPTED", "RESULT_CALLBACK",
                  "RESULT_ENQUEUE_OK", "RIGHT_APPLIED", bad, "LEFT_FAILED"]
        self.assertEqual(events[:4]+events[-1:],_safe_g01_startup_events(events))
        self.assertEqual(64,len(_safe_g01_startup_events(["LEFT_FAILED"]*200)))
        with TemporaryDirectory() as td:
            base=Path(td)/"phase6-winui"
            owned=base/"shell-owned-startup"
            left,right=owned/"Left",owned/"Right"
            left.mkdir(parents=True)
            right.mkdir()
            failure=AssertionError("UI-independent native core/helper was not active at startup")
            folder=capture_failure(base=base,owned=owned,left=left,right=right,
                                   win=None,hwnd=None,pid=None,error=failure,
                                   startup_events=events)
            raw=(folder/"panes.json").read_text(encoding="utf-8")
            saved=json.loads(raw)["Startup"]["owned_native_events"]
            self.assertEqual(events[:4]+events[-1:],saved)
            self.assertNotIn(bad,raw)
            unrelated=capture_failure(base=base,owned=owned,left=left,right=right,
                                      win=None,hwnd=None,pid=None,
                                      error=AssertionError("different"),
                                      startup_events=events)
            self.assertNotIn("owned_native_events",json.loads(
                (unrelated/"panes.json").read_text("utf-8"))["Startup"])

if __name__=="__main__":
    unittest.main()

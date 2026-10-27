"""G01: one bounded retry for a dead isolated Shell reply pipe."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUP = (ROOT / "src/base/shell_isolated_supervisor.cpp").read_text(encoding="utf-8")
NAV = (ROOT / "app/winui/shell_navigation_controller.cpp").read_text(encoding="utf-8")


class G01BrokenPipeRetryContract(unittest.TestCase):
    def test_only_broken_pipe_or_existing_timeout_can_retry(self):
        self.assertIn("constexpr DWORD kMaxAttempts=2;", SUP)
        lane = SUP.split("void IsolatedShellSupervisor::runLane(", 1)[1]
        self.assertIn("for(DWORD attempt=0;attempt<kMaxAttempts;++attempt)", lane)
        self.assertIn(
            "outcome.hr==HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)", lane)
        self.assertIn(
            "if((outcome.timeout||brokenPipe)&&\n"
            "                   attempt+1<kMaxAttempts){", lane)
        self.assertIn("result.recovered=true;", lane)
        self.assertNotIn("if(FAILED(outcome.hr))", lane)
        self.assertNotIn("std::this_thread::sleep_for(", lane)

    def test_stale_request_and_cancel_dont_retry(self):
        lane = SUP.split("void IsolatedShellSupervisor::runLane(", 1)[1]
        retry = lane.index("if((outcome.timeout||brokenPipe)&&")
        self.assertLess(lane.index("if(!current(lane,item))break;"), retry)
        self.assertLess(
            lane.index("if(outcome.canceled||!current(lane,item))break;"),
            retry)
        self.assertLess(retry, lane.index("result.hr=outcome.hr;"))
        self.assertIn("if(cb&&current(lane,item)){", lane)
        self.assertIn("::TerminateJobObject(", SUP)

    def test_failure_still_propagates_after_bounded_attempts(self):
        lane = SUP.split("void IsolatedShellSupervisor::runLane(", 1)[1]
        retry = lane.index("if((outcome.timeout||brokenPipe)&&")
        self.assertIn("result.hr=outcome.hr;", lane[retry:])
        self.assertIn("result.timedOut=outcome.timeout;", lane[retry:])
        self.assertIn(
            "if(FAILED(result.hr)){\n"
            "                completed.kind=CompletionKind::Failed;",
            NAV)

if __name__ == "__main__":
    unittest.main()

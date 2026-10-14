"""F03 child process supervisor and route gate: static integration, not GUI QA."""
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
SUP=(ROOT/"src/base/file_preview_supervisor.cpp").read_text(encoding="utf-8")
HEADER=(ROOT/"src/base/file_preview_supervisor.h").read_text(encoding="utf-8")
GATE=(ROOT/"src/base/file_preview_request_gate.h").read_text(encoding="utf-8")
TEST=(ROOT/"tests/winui/native_preview_supervisor.cpp").read_text(encoding="utf-8")
RUN=(ROOT/"tools/winui/run_f03_supervisor_native.ps1").read_text(encoding="utf-8")

class F03SupervisorContract(unittest.TestCase):
    def test_process_child_suspended_before_job_and_no_unowned_kill(self):
        for value in ("STARTUPINFOEXW", "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
                      "EXTENDED_STARTUPINFO_PRESENT", "CREATE_SUSPENDED",
                      "CreateJobObjectW", "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
                      "AssignProcessToJobObject", "ResumeThread",
                      "TerminateJobObject", "SetHandleInformation",
                      "CreateProcessW(helper.c_str()", "CREATE_NO_WINDOW"):
            self.assertIn(value,SUP)
        self.assertLess(SUP.index("AssignProcessToJobObject"),
                        SUP.index("ResumeThread"))
        for value in ("ShellExecute", "CreateRemoteThread", "taskkill",
                      "TerminateProcessByName", "DispatcherQueue", "CoInitialize"):
            self.assertNotIn(value,SUP)

    def test_bounded_response_and_cancel(self):
        for value in ("previewpolicy::screen(stable)",
                      "previewwire::validHeader(request)",
                      "previewwire::validReply(reply)",
                      "reply.byteCount<=decision.maxEncodedBytes",
                      "reply.checksum==previewwire::checksum",
                      "readAll(outputRead.get()",
                      "cancelled.load()", "Status::Deadline",
                      "Status::ProtocolError", "io.join()", "kDeadlineMs+800"):
            self.assertIn(value, SUP+"\n"+HEADER)
        self.assertIn("std::wstring helper(helperExe),path(candidate.absolutePath)",SUP)

    def test_stale_request_gate(self):
        for value in ("window=0","pane=0","tab=0","generation=0",
                      "selectedIdentity", "current_.cancel->store(true)",
                      "current_.cancel==ticket.cancel",
                      "current_.key==ticket.key", "std::mutex"):
            self.assertIn(value,GATE)
        for value in ("F03_SUPERVISOR_REAL_CHILD_WIRE=PASS",
                      "F03_SUPERVISOR_NEGATIVES=PASS",
                      "F03_SUPERVISOR_JOB_TIMEOUT_AND_CORRUPT_WIRE=PASS",
                      "F03_SUPERVISOR_STALE_ROUTE_CANCEL_GATE=PASS"):
            self.assertIn(value,TEST)

    def test_included_in_release_and_owned_native_harness(self):
        xml=ET.parse(ROOT/"app/winui/flyExplorer.project-template.xml")
        compiles={x.get("Include","").replace("\\","/")
                  for x in xml.iter() if x.tag.endswith("ClCompile")}
        self.assertIn("../../src/base/file_preview_supervisor.cpp",compiles)
        for token in ("$ExpectedSha", "$FixtureRoot", "$helper",
                      "F03_SUPERVISOR_REAL_CHILD_NATIVE_PASS",
                      "F03_SUPERVISOR_BATCH_SERIALIZATION_INVALID"):
            self.assertIn(token,RUN)

if __name__=="__main__":unittest.main()

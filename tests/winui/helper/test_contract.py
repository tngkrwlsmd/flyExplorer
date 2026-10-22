"""Scoped M1.6 guardrails. No claims of production WinUI integration."""
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
HELPER=ROOT/"app"/"winui"/"helper"

def source(path):
    return (path if isinstance(path,Path) else HELPER/path).read_text(encoding="utf-8-sig")

class IsolationContracts(unittest.TestCase):
    def test_current_native_shell_enumerator(self):
        p=source("FlyShellIsolationHelper.project-template.xml")
        h=source("FlyShellIsolationHelper.cpp")
        self.assertIn("shell_navigation_core.cpp",p)
        self.assertIn("shell_enum_bridge.cpp",p)
        self.assertIn("shellnav::enumeratePage",h)
        self.assertIn("COINIT_APARTMENTTHREADED",h)
        for forbidden in ("ExplorerCtrl","ListCtrlEx","afxwin.h",
                          "file_operation_core.cpp","ProductCommandBridge",
                          "UseWinUI"):
            self.assertNotIn(forbidden,p+h)

    def test_strict_navigation_ipc_contract(self):
        h=source("FlyShellIsolationHelper.cpp")
        t=(HERE/"test_process_isolation.py").read_text(encoding="utf-8-sig")
        t+=(HERE/"wire_client.py").read_text(encoding="utf-8-sig")
        wire=source(ROOT/"src/base/shell_isolation_wire.h")
        for required in ("kVersion=3","kAbsolutePidl=2",
                         "kMaxPathUnits=16384","kMaxPidl=65536",
                         "kMaxPageEntries=1024","kMaxCompleteModelEntries=20000",
                         "kMaxBrowseEntries=100000",
                         "kMaxBody=8u*1024u*1024u","sizeof(Request)==24",
                         "sizeof(Reply)==28","validPidl"):
            self.assertIn(required,wire)
        for required in ("exactRead","exactWrite","ILGetSize",
                         "checksum(body.bytes.data(),body.bytes.size())",
                         "req.limit>kMaxBrowseEntries-req.offset",
                         "SHGetPathFromIDListEx"):
            self.assertIn(required,h)
        for forbidden in ("DeleteFileW(","MoveFileW(","CopyFileW(",
                          "SHFileOperationW(","ShellExecuteW("):
            self.assertNotIn(forbidden,h)
        for required in ("pidl_valid(raw)","string bounds",
                         "result frame length","corrupted body",
                         "REAL_NATIVE_HELPER_PAGED_OFFSET_LIMIT_PASS",
                         "REAL_NATIVE_HELPER_OFFSET_OVER_COMPLETE_MODEL_PASS"):
            self.assertIn(required,t)

    def test_file_transfer_mode_is_explicit_and_owned(self):
        helper=source("FlyShellIsolationHelper.cpp")
        project=source("FlyShellIsolationHelper.project-template.xml")
        core=source(ROOT/"src/base/shell_transfer_core.cpp")
        for token in (
            '--file-transfer',
            "runIsolatedHelper",
            "shell_transfer_core.cpp",
            "file_command_core.cpp",
        ):
            self.assertIn(token,helper+project)
        for token in (
            "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "JOB_OBJECT_LIMIT_ACTIVE_PROCESS",
            "AssignProcessToJobObject",
            "TerminateJobObject",
            "kTransferCancelGraceMs",
            "CreateEventW",
        ):
            self.assertIn(token,core)

    def test_private_job_boundaries_without_product_switch(self):
        h=source("FlyShellIsolationHelper.cpp")
        t=(HERE/"test_process_isolation.py").read_text(encoding="utf-8-sig")
        main=source(ROOT/"app/winui/MainWindow.xaml.cpp")
        navigation=source(ROOT/"app/winui/shell_navigation_controller.cpp")
        self.assertIn("FLY_M16_OWNED_TEST_ONLY",h)
        self.assertIn("AssignProcessToJobObject",t)
        self.assertIn("KILL_ON_JOB_CLOSE",t)
        self.assertIn("TerminateJobObject(slowjob",t)
        self.assertIn("OWNED_JOB_ONLY_TIMEOUT",t)
        self.assertIn("OWNED_JOB_KILL_ON_CLOSE",t)
        self.assertIn("supervisor_->submit",navigation)
        self.assertIn("FlyShellIsolationHelper.exe",main)
        self.assertNotIn("mWorker->submit",main+navigation)
        project=source(ROOT/"app/winui/flyExplorer.project-template.xml")

if __name__=="__main__":
    unittest.main()

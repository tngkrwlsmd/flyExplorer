"""Scoped M1.6 guardrails. No claims of production WinUI integration."""
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
HELPER=ROOT/"app"/"winui"/"helper"

def source(path):
    return (path if isinstance(path,Path) else HELPER/path).read_text(encoding="utf-8-sig")

class IsolationContracts(unittest.TestCase):
    def test_mfc_free_original_shell_enumerator_reuse(self):
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

    def test_strict_read_only_ipc_contract(self):
        h=source("FlyShellIsolationHelper.cpp")
        t=(HERE/"test_process_isolation.py").read_text(encoding="utf-8-sig")
        wire=source(ROOT/"src/base/shell_isolation_wire.h")
        for required in ("kVersion=3","kAbsolutePidl=2",
                         "kMaxPathUnits=16384","kMaxPidl=65536",
                         "kMaxPageEntries=1024","kMaxNavigationEntries=20000",
                         "kMaxBody=8u*1024u*1024u","sizeof(Request)==24",
                         "sizeof(Reply)==28","validPidl"):
            self.assertIn(required,wire)
        for required in ("exactRead","exactWrite","ILGetSize",
                         "checksum(body.bytes.data(),body.bytes.size())",
                         "SHGetPathFromIDListEx"):
            self.assertIn(required,h)
        for forbidden in ("DeleteFileW(","MoveFileW(","CopyFileW(",
                          "SHFileOperationW(","ShellExecuteW("):
            self.assertNotIn(forbidden,h)
        for required in ("pidl_valid(raw)","string bounds",
                         "result frame length","corrupted body",
                         "REAL_NATIVE_HELPER_PAGED_OFFSET_LIMIT_PASS"):
            self.assertIn(required,t)

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
        self.assertNotIn("shell_async_worker.cpp",project)

if __name__=="__main__":
    unittest.main()

"""Scoped M1.6 guardrails. No claims of production WinUI integration."""
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def source(path):
    return (path if isinstance(path,Path) else HERE/path).read_text(encoding="utf-8-sig")

class IsolationContracts(unittest.TestCase):
    def test_mfc_free_original_shell_enumerator_reuse(self):
        p=source("FlyShellIsolationHelper.project-template.xml")
        h=source("FlyShellIsolationHelper.cpp")
        self.assertIn("shell_navigation_core.cpp",p)
        self.assertIn("shell_enum_bridge.cpp",p)
        self.assertIn("shellnav::enumerate",h)
        self.assertIn("COINIT_APARTMENTTHREADED",h)
        for forbidden in ("ExplorerCtrl","ListCtrlEx","afxwin.h",
                          "file_operation_core.cpp","ProductCommandBridge",
                          "UseWinUI"):
            self.assertNotIn(forbidden,p+h)

    def test_strict_read_only_ipc_contract(self):
        h=source("FlyShellIsolationHelper.cpp")
        t=source("test_process_isolation.py")
        for required in ("kMaxUnits=16384","kMaxItemUnits=4096",
                         "kMaxPidl=65536","kMaxBody=4u*1024u*1024u",
                         "sizeof(Reply)==28","exactRead","exactWrite",
                         "ILGetSize","checksum(body.bytes)"):
            self.assertIn(required,h)
        for forbidden in ("DeleteFileW(","MoveFileW(","CopyFileW(",
                          "SHFileOperationW(","ShellExecuteW("):
            self.assertNotIn(forbidden,h)
        for required in ("pidl_valid(raw)","string bounds",
                         "result frame length","corrupted body"):
            self.assertIn(required,t)

    def test_private_job_boundaries_without_product_switch(self):
        h=source("FlyShellIsolationHelper.cpp")
        t=source("test_process_isolation.py")
        main=source(ROOT/"experiments/phase6_winui_shell/MainWindow.xaml.cpp")
        self.assertIn("FLY_M16_OWNED_TEST_ONLY",h)
        self.assertIn("AssignProcessToJobObject",t)
        self.assertIn("KILL_ON_JOB_CLOSE",t)
        self.assertIn("TerminateJobObject(slowjob",t)
        self.assertIn("OWNED_JOB_ONLY_TIMEOUT",t)
        self.assertIn("OWNED_JOB_KILL_ON_CLOSE",t)
        self.assertIn("mWorker->submit",main)
        self.assertNotIn("FlyShellIsolationHelper",main)

if __name__=="__main__":
    unittest.main()

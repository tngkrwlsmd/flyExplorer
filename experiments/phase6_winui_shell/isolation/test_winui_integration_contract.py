"""M1.7 focused source/architecture regression; real GUI tests are separate."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"src/base"
UI=ROOT/"experiments/phase6_winui_shell"
ISO=UI/"isolation"
def read(path):return path.read_text(encoding="utf-8-sig")
class RealWinUIIsolationContract(unittest.TestCase):
    def test_two_bounded_native_supervisor_lanes_and_owned_job(self):
        code=read(SRC/"shell_isolated_supervisor.cpp")
        hdr=read(SRC/"shell_isolated_supervisor.h")
        for token in ("std::array<std::shared_ptr<Lane>,2>",
                      "kDeadlineMs=4500","kMaxAttempts=2",
                      "CREATE_SUSPENDED","AssignProcessToJobObject",
                      "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
                      "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
                      "TerminateJobObject(lane->activeJob",
                      "IsolatedShellSupervisor::runLane"):
            self.assertIn(token,code)
        self.assertIn("std::uint64_t submit(int pane",hdr)
        self.assertNotIn("OpenProcess(",code)
        self.assertNotIn("EnumProcesses(",code)

    def test_helper_is_same_config_exact_sibling_and_protocol_validated(self):
        cmd=read(UI/"build.cmd")
        winui=read(UI/"MainWindow.xaml.cpp")
        proj=read(UI/"FlyExplorerWinUIShell.project-template.xml")
        helper=read(ISO/"FlyShellIsolationHelper.cpp")
        supervisor=read(SRC/"shell_isolated_supervisor.cpp")
        for token in ("call \"%HERE%isolation\\build.cmd\"",
                      "FlyShellIsolationHelper.exe","%CONFIG%"):
            self.assertIn(token,cmd)
        self.assertIn("GetModuleFileNameW(nullptr,module",winui)
        self.assertIn('helper+=L"FlyShellIsolationHelper.exe"',winui)
        self.assertIn("shell_isolated_supervisor.cpp",proj)
        self.assertNotIn("shell_async_worker.cpp",proj)
        self.assertIn("shell_isolation_wire.h",helper)
        self.assertIn("shell_isolation_wire.h",supervisor)
        self.assertIn("validPidl(bytes.data()+pos,n)",supervisor)
        self.assertIn("checksum(body.data(),body.size())",supervisor)
        self.assertIn("body.name(path,kMaxPathUnits)",helper)
        self.assertIn("reader.string(kMaxPathUnits)",supervisor)

    def test_ui_routes_via_process_and_change_watcher_not_shell_on_ui(self):
        ui=read(UI/"MainWindow.xaml.cpp")
        hdr=read(UI/"MainWindow.xaml.h")
        watcher=read(SRC/"directory_watcher.cpp")
        for token in ("mSupervisor->submitParsing(",
                      "mSupervisor->submit(","mSupervisor->forget(",
                      "mWatcher->watch(","mWatcher->unwatch(",
                      "result.filesystemPath"):
            self.assertIn(token,ui)
        self.assertIsNone(re.search(r"::SHGetPathFromIDListEx\s*\(",ui))
        self.assertNotIn("mWorker->",ui)
        self.assertIn("IsolatedShellSupervisor>",hdr)
        self.assertIn("DirectoryWatcher>",hdr)
        self.assertIn("WaitForMultipleObjects(",watcher)
        self.assertIn("directory_change_bridge.h",watcher)
        self.assertNotIn("CoInitialize",watcher)
        self.assertNotIn("IShellFolder",watcher)

    def test_real_owned_debug_gui_fault_injection_is_explicit(self):
        ui=read(UI/"MainWindow.xaml.cpp")
        sup=read(SRC/"shell_isolated_supervisor.cpp")
        helper=read(ISO/"FlyShellIsolationHelper.cpp")
        harness=read(UI/"test_shell_gui.py")
        for text in ("#if defined(_DEBUG)",
                     "FLY_M16_OWNED_TEST_ONLY",
                     "--m17-test-left-helper-hang"):
            self.assertIn(text,ui)
        self.assertIn("item.ownedDelay=true",sup)
        self.assertIn('L"--test-block"',helper)
        self.assertIn("REAL_WINUI_RIGHT_PANE_PROGRESS_WHILE_LEFT_HELPER_BLOCKED",harness)
        self.assertIn("REAL_WINUI_LEFT_HELPER_TIMEOUT_AND_AUTOMATIC_RESTART",harness)

if __name__=="__main__":
    unittest.main()

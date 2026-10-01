"""M1.7 focused source/architecture regression; real GUI tests are separate."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"src/base"
UI=ROOT/"app/winui"
ISO=UI/"helper"
TESTS=ROOT/"tests"/"winui"
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
        proj=read(UI/"flyExplorer.project-template.xml")
        helper=read(ISO/"FlyShellIsolationHelper.cpp")
        supervisor=read(SRC/"shell_isolated_supervisor.cpp")
        for token in ("call \"%HERE%helper\\build.cmd\"",
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
        harness=read(TESTS/"test_shell_gui.py")
        for text in ("#if defined(_DEBUG)",
                     "FLY_M16_OWNED_TEST_ONLY",
                     "--m17-test-left-helper-hang"):
            self.assertIn(text,ui)
        self.assertIn("item.ownedDelay=true",sup)
        self.assertIn('L"--test-block"',helper)
        self.assertIn("REAL_WINUI_RIGHT_PANE_PROGRESS_WHILE_LEFT_HELPER_BLOCKED",harness)
        self.assertIn("REAL_WINUI_LEFT_HELPER_TIMEOUT_AND_AUTOMATIC_RESTART",harness)

    def test_m18_shell_namespace_notification_separate_from_shell_helpers(self):
        watch=read(SRC/"shell_namespace_watcher.cpp")
        host=read(UI/"MainWindow.xaml.cpp")
        project=read(UI/"flyExplorer.project-template.xml")
        harness=read(TESTS/"test_shell_gui.py")
        for token in ("SHChangeNotifyRegister","SHChangeNotification_Lock",
                      "SHChangeNotification_Unlock","SHChangeNotifyDeregister",
                      "MsgWaitForMultipleObjectsEx","HWND_MESSAGE",
                      "found->second.token==token"):
            self.assertIn(token,watch)
        self.assertNotIn("EnumObjects(",watch)
        self.assertNotIn("SHParseDisplayName(",watch)
        self.assertIn("shell_namespace_watcher.cpp",project)
        self.assertIn("mShellWatcher->watch(",host)
        self.assertIn("mShellWatcher->unwatch(",host)
        self.assertIn("FLY_M18_OWNED_SHELL_NOTIFY",harness)
        self.assertIn("REAL_WINUI_OWNED_SHELL_NAMESPACE_EVENT_REFRESH",harness)

    def test_m18_com_stall_and_network_or_timeout_errors_are_bounded(self):
        helper=read(ISO/"FlyShellIsolationHelper.cpp")
        native=read(SRC/"shell_isolated_supervisor.cpp")
        ui=read(UI/"MainWindow.xaml.cpp")
        harness=read(TESTS/"test_shell_gui.py")
        self.assertIn("OwnedBlockingCom",helper)
        self.assertIn("FLY_M18_OWNED_COM_TEST_ONLY",helper)
        self.assertIn("ownedComDelay",native)
        self.assertIn("result.networkRequest=",native)
        self.assertIn("result.timedOut=outcome.timeout",native)
        self.assertIn("4.5초씩 두 번 응답하지",ui)
        self.assertIn("네트워크 폴더에 접근할 수 없거나 권한이 없습니다.",ui)
        self.assertIn("REAL_WINUI_OWNED_COM_VTABLE_STALL_RECOVERED",harness)
        self.assertIn("REAL_WINUI_LOOPBACK_UNC_REJECTED_WITH_PRIOR_FOLDER_PRESERVED",harness)
        self.assertIn("FLY_M18_EXHAUST_TIMEOUT",harness)
        self.assertIn("mOwnedComExhaustOnVirtual",ui)
        self.assertIn("item.ownedComExhaust",native)
        self.assertIn("REAL_WINUI_BOTH_COM_TIMEOUTS_EXHAUSTED_PREVIOUS_FOLDERS_PRESERVED",harness)

if __name__=="__main__":
    unittest.main()

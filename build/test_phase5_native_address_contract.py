"""Phase 5 opt-in native/WinUI address bridge: source-only safety gates.

This is NOT evidence of runtime DPI, Shell, IME or clean-machine packaging.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "src/fxfile"
BRIDGE = ROOT / "experiments/phase5_island_bridge"


class TestPhase5NativeAddressContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = (MAIN / "main_frame.cpp").read_text(encoding="utf-8-sig")
        cls.view = (MAIN / "explorer_view.cpp").read_text(encoding="utf-8-sig")
        cls.observer = (MAIN / "explorer_view_observer.h").read_text(encoding="utf-8-sig")
        cls.bridge = (BRIDGE / "bridge.cpp").read_text(encoding="utf-8-sig")
        cls.dist = (ROOT / "dist/copy.bat").read_text(encoding="utf-8-sig")

    def test_real_navigation_and_tab_events_feed_native_address(self):
        self.assertGreaterEqual(
            self.view.count("mObserver->onActivePathChanged(*this)"), 2)
        self.assertIn("virtual void onActivePathChanged(", self.observer)
        self.assertIn("void MainFrame::onActivePathChanged(", self.frame)
        self.assertIn("MainFrame::onSplitterActivedPane(", self.frame)
        self.assertIn("PostMessage(WM_TEST_ISLAND_PATH_CHANGED)", self.frame)
        self.assertIn("sTestIslandRefreshPath();", self.frame)
        self.assertIn("FlyIslandRefreshPath()", self.bridge)

    def test_native_engine_retained_and_shell_fallback_guarded(self):
        self.assertIn("TestIslandFrameFor(HWND hwnd)", self.frame)
        self.assertIn("::GetCurrentThreadId()", self.frame)
        self.assertIn("::GetFileAttributesW(explorer->getCurPath())", self.frame)
        self.assertIn("FILE_ATTRIBUTE_DIRECTORY", self.frame)
        self.assertIn("explorer->explore(pidl)", self.frame)
        self.assertIn("m_textBoxProbe.Text(L\"\")", self.bridge)
        self.assertIn("Use the existing MFC address", self.bridge)

    def test_actual_dirty_edit_is_preserved_but_clean_focus_refreshes(self):
        self.assertIn("m_dirtyEdit", self.bridge)
        self.assertIn("m_textBoxProbe.TextChanged(", self.bridge)
        self.assertIn("m_editing && m_dirtyEdit && !forceEdit", self.bridge)
        self.assertIn("m_settingNativeText", self.bridge)
        self.assertIn("m_pendingNativeUpdate", self.bridge)
        self.assertIn("m_lastNativeText", self.bridge)
        self.assertIn("std::wstring(m_textBoxProbe.Text().c_str()) != m_lastNativeText", self.bridge)

    def test_all_this_capturing_callbacks_revoked_before_xaml_detach(self):
        cleanup = self.bridge.split("    void Close() {", 1)[1].split(
            "static NavIsland* s_island", 1)[0]
        for token in ("m_textboxGotFocusToken", "m_textboxLostFocusToken",
                      "m_textboxKeyDownToken", "m_textboxTextChangedToken",
                      "m_upClickToken", "m_backClickToken", "m_forwardClickToken"):
            self.assertIn(token, cleanup)
        self.assertLess(cleanup.index("m_textboxTextChangedToken"),
                        cleanup.index("m_source.Content(nullptr)"))

    def test_optin_package_only_release_x64_and_collision_guards(self):
        self.assertIn('if /I "%FLYEXP_PHASE5_INCLUDE_WINUI%"=="1"', self.dist)
        self.assertIn('if exist "..\\bin\\x64\\resources.pri"', self.dist)
        self.assertIn('".package-stage\\x64\\resources.pri"', self.dist)
        self.assertIn('Microsoft.WindowsAppRuntime.Bootstrap.dll', self.dist)
        self.assertIn('Microsoft.Web.WebView2.Core.dll', self.dist)


if __name__ == "__main__":
    unittest.main()

"""UI-02 negative source regressions; runtime drag acceptance is separate."""
from pathlib import Path
import unittest
from validate_source_invariants import validate_ui02_layered_scrollbar_contract

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "src" / "fxfile" / "gui"

class LayeredScrollbarContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = {
            "modern": (GUI / "ModernUI.cpp").read_text(encoding="utf-8"),
            "header": (GUI / "ModernUI.h").read_text(encoding="utf-8"),
            "listing": (GUI / "ListCtrlEx.cpp").read_text(encoding="utf-8"),
            "tree": (GUI / "TreeCtrlEx.cpp").read_text(encoding="utf-8"),
            "probe": (ROOT / "build" / "visual_ui_probe.py").read_text(
                encoding="utf-8"),
        }

    def test_current_source_contract_passes(self):
        self.assertEqual(validate_ui02_layered_scrollbar_contract(**self.inputs), [])

    def mutation(self, key, old, new):
        source = self.inputs[key]
        self.assertIn(old, source, "source test fixture changed")
        inputs = dict(self.inputs)
        inputs[key] = source.replace(old, new, 1)
        self.assertTrue(validate_ui02_layered_scrollbar_contract(**inputs))

    def test_native_input_pass_through_must_remain(self):
        self.mutation("modern", "WS_EX_LAYERED | WS_EX_TRANSPARENT",
                      "WS_EX_LAYERED")

    def test_native_hit_testing_must_remain(self):
        self.mutation("modern", "return HTTRANSPARENT;",
                      "return HTCLIENT;")

    def test_native_window_cannot_be_activated(self):
        self.mutation("modern", "return MA_NOACTIVATE;",
                      "return MA_ACTIVATE;")

    def test_separate_final_pixel_owner_must_remain(self):
        self.mutation("modern", "::UpdateLayeredWindow(",
                      "::UpdateWindow(")

    def test_thumb_tracking_modal_hook_must_remain(self):
        self.mutation("modern", "WH_MSGFILTER, DarkScrollbarModalFilter",
                      "WH_GETMESSAGE, DarkScrollbarModalFilter")

    def test_native_post_scroll_refresh_hook_must_remain(self):
        self.mutation("modern", "WH_CALLWNDPROCRET, DarkScrollbarCallRet",
                      "WH_CALLWNDPROC, DarkScrollbarCallRet")

    def test_window_movement_sync_must_remain(self):
        self.mutation("modern", "sMsg == WM_WINDOWPOSCHANGED",
                      "sMsg == WM_NULL")

    def test_cleanup_must_unhook(self):
        self.mutation("modern", "        StopDarkScrollbarHooks();",
                      "        /* missing unhook */;")

    def test_explicit_theme_disable_contract_must_remain(self):
        self.mutation("header", "removeDarkScrollbarOverlay(",
                      "neverRemoveDarkScrollbarOverlay(")

    def test_list_destroy_must_release_popup(self):
        self.mutation("listing", "removeDarkScrollbarOverlay(m_hWnd)",
                      "neverRemoveDarkScrollbarOverlay(m_hWnd)")

    def test_tree_destroy_must_release_popup(self):
        self.mutation("tree", "aMessage == WM_NCDESTROY",
                      "aMessage == WM_NULL")

    def test_capture_must_include_layered_pixels(self):
        self.mutation("probe", "include_layered_windows=True",
                      "include_layered_windows=False")

    def test_popup_must_not_be_treated_as_main_window(self):
        self.mutation("probe", 'cls.value == "flyExplorer.DarkScrollbarOverlay.v1"',
                      'cls.value == "AnotherClass"')

    def test_temporary_tint_must_not_ship(self):
        inputs = dict(self.inputs)
        inputs["modern"] += "\n// FXFILE_UI02_DIAG_TINT\n"
        self.assertTrue(validate_ui02_layered_scrollbar_contract(**inputs))

if __name__ == "__main__":
    unittest.main()

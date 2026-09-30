"""UI-02 source guardrails for deterministic, user-profile-safe actual GUI harness.

The existing ModernUI native overlay already provides the old branch's
observable behavior; NEVER add a second opaque overlay to the same HWND.
Actual dark/light pointer and modal outcomes live in ignored owned GUI logs.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=(ROOT/"build/test_ui_primary_scrollbars_runtime.py")

class SafeNativeScrollbarHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=RUNTIME.read_text(encoding="utf-8-sig")

    def test_real_monitor_viewport_and_focused_owned_app(self):
        for token in ("SystemParametersInfoW(0x30",
                      "OWNED_MAIN_FITS_MONITOR_WORKAREA",
                      "rect(main)[3] <= work.bottom-5",
                      "u.SetForegroundWindow(main)",
                      "pid(u.GetForegroundWindow())==proc.pid"):
            self.assertIn(token,self.code)

    def test_dedicated_owned_tabs_and_modal_tip_dismissal(self):
        for token in ("main.view1.tab1.path = ",
                      "PRIVATE_SYNTHETIC_SCOPED_LIST_ENTRIES",
                      "OWNED_STARTUP_TIP_MODAL_PHYSICALLY_DISMISSED",
                      'klass(h)=="#32770"',
                      "u.GetDlgItem(tip,1029)",
                      "u.GetDlgItem(tip,1)",
                      "not u.IsWindow(tip)"):
            self.assertIn(token,self.code)

    def test_real_native_invariants_and_user_state(self):
        for token in ("NATIVE_POINTER_SCROLL",
                      "NATIVE_SCROLLBAR_THUMB_DRAG",
                      "NATIVE_SCROLLBAR_TRACK_CLICK",
                      "PRIMARY_LIST_TREE_SCROLLBAR_GUI_PASS",
                      "ORIGINAL_SIX_CONFIGS_UNCHANGED",
                      "assert after==before"):
            self.assertIn(token,self.code)
        for forbidden in ("ImageGrab","CreateProcessW(","SendInput(","TerminateProcess("):
            self.assertNotIn(forbidden,self.code)
        self.assertIn("proc.terminate()",self.code) # only own Popen child

if __name__=="__main__":
    unittest.main()

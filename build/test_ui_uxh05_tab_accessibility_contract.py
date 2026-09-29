"""UXH-05: scoped contract for native drawn-tab MFC accessibility."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]/"src/fxfile/gui"
class NativeTabAccessibilityContract(unittest.TestCase):
 def test_native_interface_and_reused_tab_engine(self):
  s=(R/"TabCtrl.cpp").read_text(encoding="utf-8-sig")
  h=(R/"TabCtrl.h").read_text(encoding="utf-8-sig")
  for term in ("EnableActiveAccessibility()","ROLE_SYSTEM_PAGETABLIST",
               "ROLE_SYSTEM_PAGETAB","ROLE_SYSTEM_PUSHBUTTON",
               "get_accChildCount","get_accName","get_accState",
               "get_accSelection","get_accFocus","accSelect",
               "accLocation","accHitTest","accDoDefaultAction",
               "mObserver->onTabNewButton(*this)",
               "mObserver->onTabCloseButton(*this, sTab)",
               "getTabItem(sTab)->mText",
               "SELFLAG_TAKEFOCUS","STATE_SYSTEM_SELECTED",
               "EVENT_OBJECT_NAMECHANGE","EVENT_OBJECT_SELECTION",
               "EVENT_OBJECT_REORDER","EVENT_OBJECT_FOCUS",
               "WS_TABSTOP","sMemDC.DrawFocusRect",
               "SetFocus();\n            Invalidate(FALSE)"):
   self.assertIn(term,s)
  self.assertIn("virtual HRESULT accDoDefaultAction",h)
  self.assertIn("virtual HRESULT get_accSelection",h)
  self.assertNotIn("case WM_GETOBJECT",s,
    "Use MFC built-in proxy without hand-written COM refcounting")
 def test_runtime_isolation_harness(self):
  s=(R.parents[2]/"build/test_ui_uxh05_tab_accessibility_runtime.py").read_text()
  for term in ("AccessibleObjectFromWindow","ORIGINAL_CONFIG_HASHES_IDENTICAL",
               "OWNED_MSAA_NEW_TAB_ACTUAL_GUI_PASS","--conf_dir",
               "OWNED_ACTUAL_FOCUSED_ARROW_HOME_END_PASS"):
   self.assertIn(term,s)
if __name__=="__main__":unittest.main()

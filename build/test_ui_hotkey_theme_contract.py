"""Dark native CHotKeyCtrl painting retains actual keyboard control."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class HotKeyTheme(unittest.TestCase):
 def test_native_hotkey_reuses_common_dialog_theming(self):
  s=(ROOT/"src/fxfile/gui/ModernUI.cpp").read_text(encoding="utf-8-sig")
  for term in ("msctls_hotkey32","DialogHotKeySubclassProc",
               "kDialogHotKeySubclassId","HKM_GETHOTKEY",
               "HOTKEYF_SHIFT","HOTKEYF_CONTROL","HOTKEYF_ALT",
               "MAPVK_VK_TO_VSC","mHighContrast","WM_NCDESTROY",
               "::DefSubclassProc(aHwnd","::GetFocus() == aHwnd"):
   self.assertIn(term,s)
  self.assertIn("::SetWindowSubclass(aHwnd,\n            DialogHotKeySubclassProc",s)
  self.assertIn("::RemoveWindowSubclass(\n                aHwnd, DialogHotKeySubclassProc",s)
if __name__=="__main__":unittest.main()

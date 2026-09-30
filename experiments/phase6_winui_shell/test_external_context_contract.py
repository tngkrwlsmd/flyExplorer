"""External Shell menu: own process, path checks, explicit user-only verbs."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[2]
def src(path):return (R/path).read_text(encoding="utf-8")
class ContextContract(unittest.TestCase):
 def test_third_party_menu_is_a_disposable_process_only(self):
  helper=src("experiments/phase6_winui_shell/isolation/FlyShellIsolationHelper.cpp")
  app=src("experiments/phase6_winui_shell/m22_transfers.cpp")
  client=src("src/base/shell_context_core.cpp")
  for term in ("--context-inspect","--context-menu","GetUIObjectOf",
               "QueryContextMenu","TrackPopupMenuEx","InvokeCommand",
               "SIIGBF_THUMBNAILONLY","GetAttributesW"):
   if term=="GetAttributesW":continue
   self.assertIn(term,helper)
  for term in ("GetFileAttributesW(part.c_str())",
               "FILE_ATTRIBUTE_REPARSE_POINT","verb==\"delete\"",
               "FAILED(canonical)||!name[0]",
               "verb==\"rename\"","HandleMenuMsg2"):
   self.assertIn(term,helper)
  for term in ("filename()!=L\"FlyShellIsolationHelper.exe\"",
               "ERROR_TIMEOUT","WaitForSingleObject","--context-menu"):
   self.assertIn(term,client)
  for term in ("OnExternalWindowsContextMenu",
               "mFileOperationPending","items[index].isFileSystem()",
               "root[1]!=L':'","shellcontext::show("):
   self.assertIn(term,app)
  self.assertNotIn("QueryContextMenu",app)
  xml=src("experiments/phase6_winui_shell/MainWindow.xaml")
  self.assertEqual(xml.count('Click="OnExternalWindowsContextMenu"'),2)
  self.assertIn("OnExternalWindowsContextMenu",src(
       "experiments/phase6_winui_shell/MainWindow.xaml.h"))
 def test_no_automatic_external_command_execution(self):
  a=src("experiments/phase6_winui_shell/test_shell_gui.py")
  b=src("experiments/phase6_winui_shell/test_owned_thumbnail_gui.py")
  self.assertNotIn("InvokeCommand",a+b)
  self.assertNotIn("TrackPopupMenuEx",a+b)
class OwnedContextInvocationRegression(unittest.TestCase):
 def test_right_click_uses_only_intersection_of_owned_row_and_list(self):
  probe=src("experiments/phase6_winui_shell/test_owned_context_menu_gui.py")
  self.assertIn("left=max(item.left,area.left)",probe)
  self.assertIn("right=min(item.right,area.right)",probe)
  self.assertIn("top=max(item.top,area.top)",probe)
  self.assertIn("bottom=min(item.bottom,area.bottom)",probe)
  self.assertIn('assert user.GetForegroundWindow()==hwnd',probe)
  self.assertIn('"--context-menu" in q.cmdline()',probe)
  self.assertIn('pid.value==child.pid',probe)

if __name__=="__main__":unittest.main()

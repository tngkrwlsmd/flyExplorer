"""External Shell menu: own process, path checks, explicit user-only verbs."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[2]
def src(path):return (R/path).read_text(encoding="utf-8")
class ContextContract(unittest.TestCase):
 def test_third_party_menu_is_a_disposable_process_only(self):
  helper=src("app/winui/helper/FlyShellIsolationHelper.cpp")
  app=src("app/winui/m22_transfers.cpp")
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
  for term in ("ShowExternalWindowsContextMenu(int side)",
               "OnFileRightTapped","args.Handled(true)",
               "VisualTreeHelper::GetParent","mFileOperations.busy()",
               "session.indexedItem(","indexed->isFileSystem()","root[1]!=L':'",
               "shellcontext::show("):
   self.assertIn(term,app)
  self.assertNotIn("QueryContextMenu",app)
  self.assertIn("VirtualKey::F10",app)
  self.assertIn("!ctrl&&shift&&!alt",app)
  self.assertIn("ShowExternalWindowsContextMenu(side)",app)
  self.assertIn("가상 Shell 항목의 외부 메뉴는 아직 지원하지 않습니다.",app)
  self.assertIn("로컬 고정 디스크만 지원합니다.",app)
  xml=src("app/winui/MainWindow.xaml")
  self.assertNotIn("<ListView.ContextFlyout>",xml)
  self.assertEqual(xml.count('RightTapped="OnFileRightTapped"'),2)
  header=src("app/winui/MainWindow.xaml.h")
  self.assertIn("ShowExternalWindowsContextMenu(int side)",header)
  self.assertIn("OnExternalWindowsContextMenu",header)
 def test_no_automatic_external_command_execution(self):
  a=src("tests/winui/test_shell_gui.py")
  b=src("tests/winui/test_owned_thumbnail_gui.py")
  self.assertNotIn("InvokeCommand",a+b)
  self.assertNotIn("TrackPopupMenuEx",a+b)
class OwnedContextInvocationRegression(unittest.TestCase):
 def test_right_click_uses_only_intersection_of_owned_row_and_list(self):
  probe=src("tests/winui/test_owned_context_menu_gui.py")
  self.assertIn("left=max(item.left,area.left)",probe)
  self.assertIn("right=min(item.right,area.right)",probe)
  self.assertIn("top=max(item.top,area.top)",probe)
  self.assertIn("bottom=min(item.bottom,area.bottom)",probe)
  self.assertIn('OWNED_CONTEXT_DIRECT_RIGHT_CLICK_HELPER',probe)
  self.assertIn('mouse.click(button="right",coords=click)',probe)
  self.assertIn('keyboard.send_keys("+{F10}")',probe)
  self.assertIn('OWNED_CONTEXT_SHIFT_F10_MENU_CANCEL',probe)
  self.assertIn('"--context-menu" in q.cmdline()',probe)
  self.assertIn('pid.value==child.pid',probe)
  self.assertNotIn('Windows Shell isolated context menu',probe)

if __name__=="__main__":unittest.main()

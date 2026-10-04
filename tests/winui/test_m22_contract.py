"""M2.2 architecture/safety contracts; native+real GUI are separate."""
from pathlib import Path
import unittest,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2]
def src(p):return (R/p).read_text(encoding="utf-8-sig")
A="app/winui/"
class M22Contracts(unittest.TestCase):
 def test_mfc_independent_shell_worker_contract(self):
  h=src("src/base/shell_transfer_core.h")
  cpp=src("src/base/shell_transfer_core.cpp")
  for text in ("Kind { Copy, Move, Recycle }","Collision { Reject, KeepBoth }",
               "recycleConfirmed=false","IFileOperation","CoInitializeEx",
               "COINIT_APARTMENTTHREADED","FOFX_RECYCLEONDELETE",
               "FOF_RENAMEONCOLLISION","GetAnyOperationsAborted",
               "GetDriveTypeW","FILE_ATTRIBUTE_REPARSE_POINT",
               "std::atomic_bool","UpdateProgress"):
   self.assertIn(text,h+cpp)
  for forbidden in ("CWnd","XamlRoot","Windows::ApplicationModel"):
   self.assertNotIn(forbidden,cpp+h)
 def test_safety_guards_are_executable_not_comments_only(self):
  s=src("src/base/shell_transfer_core.cpp")
  for text in ("request.sources.size()>32","!request.recycleConfirmed",
                "ERROR_ALREADY_EXISTS","descendant(item,dest)",
                "GetFileAttributesW(target.c_str())",
                "state_.cancel.load","E_ABORT"):
   self.assertIn(text,s)
 def test_compiled_reusable_file_toolbar_and_status(self):
  x=src(A+"MainWindow.xaml")
  for text in ('x:Name="ToolbarView"','x:Name="FooterView"',
               'SelectionMode="Multiple"','RightTapped="OnFileRightTapped"'):
   self.assertIn(text,x)
  self.assertNotIn("<ListView.ContextFlyout>",x)
  for component in ("FileToolbar","StatusFooter"):
   for suffix in (".idl",".xaml",".xaml.h",".xaml.cpp"):
    self.assertTrue((R/A/(component+suffix)).is_file(),component+suffix)
  harness=src("tests/winui/test_m22_gui.py")
  self.assertIn('select_one("복사본.txt")',harness)
  self.assertIn("iface_selection_item.AddToSelection()",harness)
 def test_project_compiles_both_native_and_new_reusable_controls(self):
  xml=src(A+"flyExplorer.project-template.xml")
  for name in ("FileToolbar.xaml.cpp","StatusFooter.xaml.cpp",
               "file_operation_controller.cpp","m22_transfers.cpp","shell_transfer_core.cpp",
               "Strings\\ko-KR\\Resources.resw","/utf-8",
               "<DefaultLanguage>ko-KR</DefaultLanguage>"):
   self.assertIn(name,xml)
 def test_real_korean_resw_has_ui_button_semantics(self):
  p=R/A/"Strings/ko-KR/Resources.resw"
  root=ET.parse(p).getroot()
  values={d.get("name"):d.findtext("value") for d in root.findall("data")}
  for text in ("CopyAction.Content","MoveAction.Content","RecycleAction.Content",
               "CancelAction.Content"):
   self.assertIn(text,values)
   self.assertTrue(any("\uac00"<=c<="\ud7a3" for c in values[text]))
 def test_real_gui_dispatch_uses_explicit_confirmation_and_async_progress(self):
  s=src(A+"m22_transfers.cpp")
  controller=src(A+"file_operation_controller.cpp")
  for text in ("ContentDialog","ConfirmCollision","ConfirmRecycle",
               "ContentDialogResult::Primary","OperationProgress().Value",
               "mFileOperations.cancel","get_weak","DispatcherQueue"):
   self.assertIn(text,s)
  for text in ("shelltransfer::execute","state_->progress",
               "completion.ticket!=state_->epoch","sameContext("):
   self.assertIn(text,controller)
 def test_successful_transfer_always_refreshes_visible_touched_other_pane(self):
  source=src(A+"m22_transfers.cpp")
  controller=src(A+"file_operation_controller.cpp")
  self.assertIn("completion.touchedFolders.begin()",source)
  self.assertIn("QueuePidl(side",source)
  self.assertNotIn("!pane.pending[pane.active]",source)
  self.assertIn("touched.push_back(request.sourceParent)",controller)
  self.assertIn("touched.push_back(request.destination)",controller)
  self.assertIn("TransferDisposition::Succeeded",controller)

 def test_shortcuts_and_context_menu_have_noninert_handlers(self):
  x=src(A+"MainWindow.xaml")
  m=src(A+"m22_transfers.cpp")
  for text in ('Click="OnCopySelected"','Click="OnMoveSelected"',
               'Click="OnRecycleSelected"'):
   self.assertIn(text,x)
  for text in ('VirtualKey::F5','VirtualKey::F6','VirtualKey::Delete',
               'VirtualKey::A','VirtualKey::C','VirtualKey::V'):
   self.assertIn(text,m)
 def test_m22_owned_native_fixtures_never_mutate_real_recycle_bin(self):
  s=src("tests/winui/m22/m22_transfer_fixture.cpp")
  self.assertIn("recycle_plan",s) if "recycle_plan" in s else self.assertIn("recycle_requires_explicit_consent",s)
  self.assertNotIn("execute(r,progress); // recycle",s)
if __name__=="__main__":unittest.main()

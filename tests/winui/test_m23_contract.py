"""M2.3 scoped safety contracts; actual OS clipboard is NOT automated."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[2]
A="app/winui/"
def src(p):return (R/p).read_text(encoding="utf-8-sig")
class M23Contracts(unittest.TestCase):
 def test_mfc_winrt_independent_os_clipboard(self):
  c=src("src/base/shell_clipboard_core.cpp")
  for token in ("CF_HDROP","Preferred DropEffect","GlobalAlloc",
                "OpenClipboard(owner)","SetClipboardData","DROPFILES",
                "GlobalSize","CompareStringOrdinal"):
   self.assertIn(token,c)
  for token in ("winrt::","CWnd"):
   self.assertNotIn(token,c)
  # External Explorer CF_HDROP HGLOBAL buffers may contain padding.
  # The platform drag parser is appropriate for externally supplied data;
  # native strict decode() is still used for in-memory wire validation.
  self.assertIn("DragQueryFileW",c)
  self.assertIn("valid(candidate)",c)
 def test_strict_unicode_wire_and_bounded_input(self):
  c=src("src/base/shell_clipboard_core.cpp")
  for token in ("MaxBytes=65536","MaxItems=32","!full(s)",
                "drop.fWide","if(result.paths.empty())return false;","sizeof(wchar_t)",
                "payload.paths.size()>MaxItems"):
   self.assertIn(token,c)
 def test_cut_effect_error_is_not_silent_copy(self):
  c=src("src/base/shell_clipboard_core.cpp")
  self.assertIn("return ERROR_NOT_SUPPORTED;",c)
  self.assertIn("if(answer==ERROR_SUCCESS)answer=::GetLastError();",c)
 def test_os_paste_reuses_previously_verified_native_transfer(self):
  s=src(A+"m22_transfers.cpp")
  for token in ("shellclipboard::read","StartTransfer(std::move(request))",
                "shelltransfer::execute","CompareStringOrdinal",
                "CopySelectedToWindowsClipboard","GetActiveWindow"):
   self.assertIn(token,s)
 def test_keyboard_standard_os_clipboard(self):
  s=src(A+"m22_transfers.cpp")
  self.assertIn("VirtualKey::C",s)
  self.assertIn("VirtualKey::X",s)
  self.assertIn("VirtualKey::V",s)
  self.assertIn("CopySelectedToWindowsClipboard(",s)
  self.assertIn("PasteFromWindowsClipboard();args.Handled(true);return;",s)
 def test_real_winui_context_actions_both_lists(self):
  x=src(A+"MainWindow.xaml")
  for item in ('Click="OnWindowsCopy"','Click="OnWindowsCut"',
               'Click="OnWindowsPaste"'):
   self.assertEqual(x.count(item),2)
  for method in ("OnWindowsCopy","OnWindowsCut","OnWindowsPaste"):
   self.assertIn(method,src(A+"MainWindow.xaml.h"))
  self.assertIn("shell_clipboard_core.cpp",src(A+"flyExplorer.project-template.xml"))
 def test_owned_native_never_touches_global_clipboard(self):
  s=src("tests/winui/m23/m23_native_fixture.cpp")
  self.assertNotIn("shellclipboard::write(",s)
  self.assertNotIn("shellclipboard::read(",s)
  self.assertIn("reject_missing_second_terminal_unicode_null",s)
 def test_no_broken_runtime_ko_and_default_korean_resources(self):
  s=src(A+"m22_transfers.cpp")
  self.assertNotIn('L"??',s)
  p=src(A+"flyExplorer.project-template.xml")
  self.assertIn("<DefaultLanguage>ko-KR</DefaultLanguage>",p)

 def test_m23_private_session_versioned_bounds_and_reparse_rejection(self):
  body=src("src/base/ui_session.cpp")
  for token in ("'F','X','S','E','S','S','2','3'","FILE_ATTRIBUTE_REPARSE_POINT",
                "DRIVE_FIXED","MaxSize=524288","MaxWindowTabs=10",
                "MaxPaneTabs=8","MaxHistory=16","checksum(bytes,bytes.size()-4)",
                "MOVEFILE_REPLACE_EXISTING","if(version==1)return decodeV1",
                "if(version==2)return decodeV2","return false;"):
   self.assertIn(token,body)
 def test_session_profile_strict_and_isolated_from_legacy(self):
  body=src("src/base/ui_session.cpp")
  self.assertIn("flyExplorer",body)
  self.assertIn("winui-session-v1.bin",body)
  self.assertIn("MOVEFILE_WRITE_THROUGH",body)
  self.assertIn("MOVEFILE_REPLACE_EXISTING",body)
  self.assertNotIn("fxfile\\\\conf",body)
 def test_real_winui_opt_in_controls_and_default_korean_resource(self):
  x=src(A+"MainWindow.xaml")
  res=src(A+"Strings/ko-KR/Resources.resw")
  for control in ("SaveSessionButton","RestoreSessionButton","ClearSessionButton"):
   self.assertIn(control,x)
  for key in ("SaveSessionAction.Content","RestoreSessionAction.Content",
              "ClearSessionAction.Content"):
   self.assertIn(key,res)
 def test_real_winui_tab_sort_split_window_active_restored(self):
  coordinator=src(A+"session_coordinator.cpp")
  surface=src(A+"m23_session.cpp")
  for name in ("data.windowTabs.reserve(workspace.count())","data.activeWindow",
               "splitPermille","nameColumnWidth","viewMode","sortMode",
               "historyLocations","historyPathsFromLocations","restoreHistoryPaths",
               "workspace.replace(","workspace.activeIndex()"):
   self.assertIn(name,coordinator)
  for name in ("mSessionCoordinator.capture(","mSessionCoordinator.save(",
               "mSessionCoordinator.load(","mSessionCoordinator.applyRestore(",
               "ApplyActiveWindowTab"):
   self.assertIn(name,surface)
  self.assertNotIn("SHGetPathFromIDListEx",coordinator)
 def test_session_auto_restore_no_explicit_startup_path_override(self):
  coordinator=src(A+"session_coordinator.cpp")
  surface=src(A+"m23_session.cpp")
  for token in ('GetEnvironmentVariableW(L"FLY_M23_OWNED_SESSION"',
                '"--m23-owned-auto-restore"','explicitPath',
                "autoRestoreAllowed"):
   self.assertIn(token,coordinator)
  self.assertIn("mSessionCoordinator.autoRestoreAllowed()",surface)
 def test_owned_real_second_process_saves_reloads_and_clears(self):
  body=src("tests/winui/test_m23_gui.py")
  for token in ("REAL_M23_EXPLICIT_KOREAN_PRIVATE_SESSION_SAVE",
                "REAL_M23_SECOND_OWNED_PROCESS_AUTO_RESTORED",
                "REAL_M23_PRIVATE_SESSION_CLEAR_REVOKES",
                "psutil.Process(child.pid).exe()","proc.cmdline()[1]",
                "PostMessageW"):
   self.assertIn(token,body)
 def test_session_native_m23_compiled_in_both_targets(self):
  first=src(A+"flyExplorer.project-template.xml")
  second=src("tests/winui/m23/FlyM23NativeContracts.project-template.xml")
  self.assertIn("ui_session.cpp",first)
  self.assertIn("session_coordinator.cpp",first)
  self.assertNotIn("session_coordinator.cpp",second)
  self.assertIn("ui_session.cpp",second)
  self.assertEqual(first.count("<DefaultLanguage>ko-KR</DefaultLanguage>"),1)
  self.assertNotIn("<DefaultLanguage>en-US</DefaultLanguage>",first)
 def test_session_gui_never_automates_global_clipboard_or_recycle(self):
  body=src("tests/winui/test_m23_gui.py")
  for forbidden in ("shellclipboard::write(","OpenClipboard(","recycleConfirmed=true"):
   self.assertNotIn(forbidden,body)
 def test_external_and_private_drop_routes_common_core(self):
  source=src(A+"m23_drag.cpp")
  for token in ("GetStorageItemsAsync","DragItemsStartingEventArgs",
                "args.GetDeferral()","mPrivateDragToken.clear()",
                "StartTransfer(std::move(request))",
                "DataPackageOperation::Copy","route!=mPrivateDragRoute"):
   if token=="route!=mPrivateDragRoute":
    self.assertIn("source.routeIds[source.active]!=mPrivateDragRoute",source)
   else:self.assertIn(token,source)
  x=src(A+"MainWindow.xaml")
  self.assertEqual(x.count('DragItemsStarting="OnFileDragItemsStarting"'),2)
  self.assertEqual(x.count('Drop="OnFileDrop"'),2)
 def test_all_drag_runtime_messages_are_genuine_korean(self):
  code=src(A+"m23_drag.cpp")
  self.assertNotIn('StatusText().Text(L"?',code)
  for part in ("원본 폴더가 변경됐습니다","최대 32개",
               "파일 놓기 데이터를 읽지 못했습니다"):
   self.assertIn(part,code)
 def test_row_drag_is_compiled_and_physical_test_is_separate_gate(self):
  source=src(A+"MainWindow.xaml.cpp")
  drag=src(A+"m23_drag.cpp")
  test=src("tests/winui/test_m23_gui.py")
  self.assertIn("row.CanDrag(true)",source)
  self.assertIn("OnFileRowDragStarting",source)
  self.assertIn("OnFileRowDragStarting",drag)
  self.assertIn('FLY_M23_OWNED_DRAG_TEST',test)
if __name__=="__main__":unittest.main()

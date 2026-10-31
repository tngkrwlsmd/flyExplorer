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
  for term in ("--context-inspect","--context-menu","--context-properties",
               "GetUIObjectOf",
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
  for term in ("ShowExternalWindowsContextMenu(int side,bool propertiesOnly)",
               "OnFileRightTapped","args.Handled(true)",
               "VisualTreeHelper::GetParent","mFileOperations.busy()",
               "session.indexedItem(","indexed->isFileSystem()","root[1]!=L':'",
               "shellcontext::show("):
   self.assertIn(term,app)
  self.assertNotIn("QueryContextMenu",app)
  self.assertIn("VirtualKey::F10",app)
  self.assertIn("!ctrl&&shift&&!alt",app)
  self.assertIn("VirtualKey::Application",app)
  self.assertIn("!ctrl&&!shift&&!alt",app)
  self.assertIn("const bool contextMenuKey=",app)
  self.assertIn("if(contextMenuKey){",app)
  self.assertIn("ShowExternalWindowsContextMenu(side)",app)
  self.assertIn("ShowExternalWindowsContextMenu(side,true)",app)
  self.assertIn("!ctrl&&!shift&&alt&&vk==Windows::System::VirtualKey::Enter",app)
  window=src("app/winui/MainWindow.xaml.cpp")
  # Bare Enter still opens an item, while modified Enter must bubble to the
  # list shortcut handler so Alt+Enter can reach the properties route.
  row_key=window.split("row.KeyDown([weak,side]",1)[1].split("row.CanDrag(true)",1)[0]
  for token in ("GetKeyState(VK_CONTROL)","GetKeyState(VK_SHIFT)",
                "GetKeyState(VK_MENU)","OpenSelectedFolder(side)",
                "ShowExternalWindowsContextMenu(side,true)"):
   self.assertIn(token,row_key)
  self.assertLess(row_key.index("ShowExternalWindowsContextMenu(side,true)"),
                  row_key.index("OpenSelectedFolder(side)"))
  self.assertIn("if(alt&&!control&&!shift)",row_key)
  left_key=window.split("void MainWindow::OnLeftFileKeyDown(",1)[1].split(
      "void MainWindow::OnRightFileKeyDown(",1)[0]
  right_key=window.split("void MainWindow::OnRightFileKeyDown(",1)[1]
  for body in (left_key,right_key):
   self.assertIn("a.Key()==Windows::System::VirtualKey::Enter&&!modified",body)
   self.assertLess(body.index("&&!modified"),body.index("HandleFileShortcut("))
  self.assertIn("45000,propertiesOnly",app)
  self.assertIn("bool propertiesOnly=false",src("src/base/shell_context_core.h"))
  self.assertIn('propertiesOnly?L"\\\" --context-properties"',client)
  self.assertIn("inspectOrShowContext(false,true)",helper)
  self.assertIn('verb=="properties"){chosen=offset+1;break;}',helper)
  self.assertIn("HRESULT_CODE(added)",helper)
  self.assertLess(app.index("ShowExternalWindowsContextMenu(side,true)"),
                  app.index("VirtualKey::F10"))
  self.assertIn("ShowAppFileContextMenu(side,clicked,args.GetPosition(clicked))",app)
  self.assertIn("ShowAppBackgroundContextMenu(side,list,args.GetPosition(list))",app)
  self.assertIn("MenuFlyoutSubItem sendTo;",app)
  self.assertIn("MenuFlyoutSubItem create;",app)
  itemMenu=app.split("void MainWindow::ShowAppFileContextMenu(",1)[1].split(
      "void MainWindow::ShowAppBackgroundContextMenu(",1)[0]
  for token in (
      "pane.active>=pane.filesystemPaths.size()",
      "const bool localSource=!pane.filesystemPaths[tab].empty();",
      "bool boundedSources=true;",
      "fxfile::shelltransfer::kMaxSourcePathUnits-sourceUnits",
      "const bool localSelection=ready&&boundedSources&&",
      "const bool canProviderSource=ready&&boundedSources&&!localSource&&",
      "const bool canRename=localSelection&&count==1;",
      "other.active<other.pending.size()",
      "!other.pending[other.active]",
      "const bool canOppositeCopy=(localSelection||canProviderSource)&&",
      "const bool canOppositeMove=localSelection&&destinationFilesystem;",
      "sendTo.IsEnabled(canOppositeCopy||canOppositeMove);",
      "const bool canExternal=localSelection&&",
  ):
   self.assertIn(token,itemMenu)
  self.assertIn('make(L"추가 옵션 표시"',app)
  self.assertIn("kMaxContextSelection=32",src("src/base/shell_context_core.h"))
  self.assertIn("kMaxContextPathUnits=16*1024",src("src/base/shell_context_core.h"))
  self.assertIn("paths.size()>kMaxContextSelection",client)
  self.assertIn("paths.size()>1&&verb!=\"properties\"",helper)
  self.assertIn("CMIC_MASK_NOASYNC",helper)
  self.assertIn("awaitOwnedPropertySheet(owner)",helper)
  self.assertIn("MsgWaitForMultipleObjectsEx(",helper)
  self.assertIn("EnumWindows(&scanPropertySheet",helper)
  self.assertIn("rc=69;",helper)
  self.assertIn("children.size()==paths.size()",helper)
  self.assertIn("static_cast<UINT>(children.size())",helper)
  self.assertIn("paths.push_back",app)
  self.assertIn("list.SelectedItems().Size()",app)
  self.assertIn("commonParent",app)
  self.assertIn("16*1024-totalUnits",helper)
  self.assertIn("std::vector<std::wstring> const& paths",client)
  self.assertIn("가상 Shell 항목의 외부 메뉴는 아직 지원하지 않습니다.",app)
  self.assertIn("로컬 고정 디스크만 지원합니다.",app)
  xml=src("app/winui/MainWindow.xaml")
  self.assertNotIn("<ListView.ContextFlyout>",xml)
  # Both lists now use handledEventsToo=true: child ListViewItems can
  # consume RightTapped, but the pane's menu must still run once.
  self.assertEqual(xml.count('RightTapped="OnFileRightTapped"'),0)
  constructor=src("app/winui/MainWindow.xaml.cpp").split(
      "MainWindow::MainWindow()",1)[1].split(
      "RootShell().AddHandler(",1)[0]
  self.assertIn("for(auto const& files:{LeftFiles(),RightFiles()})",constructor)
  self.assertIn("UIElement::RightTappedEvent()",constructor)
  self.assertIn("this,&MainWindow::OnFileRightTapped",constructor)
  self.assertEqual(constructor.count("UIElement::RightTappedEvent()"),1)
  self.assertIn("true);",constructor)
  header=src("app/winui/MainWindow.xaml.h")
  self.assertIn("ShowExternalWindowsContextMenu(int side,bool propertiesOnly=false)",header)
  self.assertIn("OnExternalWindowsContextMenu",header)
 def test_folder_background_menu_reuses_all_toolbar_modes(self):
  app=src("app/winui/m22_transfers.cpp")
  header=src("app/winui/MainWindow.xaml.h")
  body=app.split("void MainWindow::ShowAppBackgroundContextMenu(",1)[1].split(
      "void MainWindow::OnFileRightTapped(",1)[0]
  self.assertIn("ToggleMenuFlyoutItem item;",body)
  self.assertIn("item.IsChecked(checked);",body)
  self.assertEqual(body.count("view.Items().Append(choice("),5)
  self.assertEqual(body.count("sort.Items().Append(choice("),8)
  for label,index in (
      ("이름 오름차순",0),("이름 내림차순",1),
      ("유형 오름차순",4),("유형 내림차순",5),
      ("크기 오름차순",6),("크기 내림차순",2),
      ("수정 날짜 오름차순",7),("수정 날짜 내림차순",3),
  ):
   self.assertIn('choice(L"'+label+'",sortMode=='+str(index),body)
  self.assertIn("pane.active>=pane.filesystemPaths.size()",body)
  self.assertIn("state.identity!=identity",body)
  self.assertIn("pane.routeIds[tab]!=route",body)
  self.assertIn("ShowAppBackgroundContextMenu(side,view,Windows::Foundation::Point{0,0})",app)
  self.assertIn("ShowAppBackgroundContextMenu(int side,",header)

 def test_external_menu_reports_safe_command_boundaries(self):
  app=src("app/winui/m22_transfers.cpp")
  helper=src("app/winui/helper/FlyShellIsolationHelper.cpp")
  self.assertIn('if(paths.size()>1&&verb!="properties")rc=65;',helper)
  self.assertIn("const auto count=list.SelectedItems().Size();",app)
  self.assertIn("StatusText().Text(propertiesOnly?",app)
  self.assertIn("여러 항목의 외부 Windows 메뉴는 속성 확인만 지원합니다.",app)
  self.assertIn("else if(code==65)",app)
  self.assertIn("이 Windows 메뉴 명령은 실행하지 않았습니다.",app)
  self.assertIn("else if(code==69)",app)
  self.assertIn("helper,paths,cursor,45000,propertiesOnly",app)

 def test_external_menu_result_cannot_overwrite_other_workspace_status(self):
  app=src("app/winui/m22_transfers.cpp")
  body=app.split("void MainWindow::ShowExternalWindowsContextMenu(int side,bool propertiesOnly){",1)[1].split(
      "void MainWindow::OnExternalWindowsContextMenu(",1)[0]
  for token in (
      "ActiveWindowTab().model.activePane!=side",
      "pane.active>=pane.tabs.size()",
      "pane.active>=pane.pending.size()",
      "pane.active>=pane.routeIds.size()",
      "pane.active>=pane.filesystemPaths.size()",
      "const auto identity=workspace.identity;",
      "const auto tab=pane.active;",
      "const auto route=pane.routeIds[tab];",
      "const auto folder=pane.filesystemPaths[tab];",
      "live.identity!=identity",
      "live.model.activePane!=side",
      "pane.active!=tab",
      "pane.routeIds[tab]!=route",
      "pane.filesystemPaths[tab]!=folder",
      "live.fileLists[side].visibleRoute!=route",
      "if(ui->mClosing)return;",
      "ui->mFileOperations.busy()",
  ):
   self.assertIn(token,body)
  callback=body.split("dispatch.TryEnqueue([weak,code,identity,side,tab,route,folder,",1)[1]
  self.assertLess(callback.index("live.identity!=identity"),
                  callback.index("if(code==0)ui->StatusText().Text("))
  self.assertLess(callback.index("pane.filesystemPaths[tab]!=folder"),
                  callback.index("else if(code==65)ui->StatusText().Text("))
  self.assertIn("helper,paths,cursor,45000,propertiesOnly",body)

 def test_late_shell_menu_result_keeps_new_selection_status(self):
  """The external menu can remain open while selection changes in one tab."""
  app=src("app/winui/m22_transfers.cpp")
  body=app.split("void MainWindow::ShowExternalWindowsContextMenu(int side,bool propertiesOnly){",1)[1].split(
      "void MainWindow::OnExternalWindowsContextMenu(",1)[0]
  self.assertIn("originalSelection.push_back(path);",body)
  self.assertIn("std::sort(originalSelection.begin(),originalSelection.end());",body)
  self.assertIn("std::make_shared<const std::vector<std::wstring>>(",body)
  self.assertIn("expectedSelection,propertiesOnly]{",body)
  callback=body.split("dispatch.TryEnqueue([weak,code,identity,side,tab,route,folder,",1)[1]
  self.assertIn("if(tab>=pane.tabs.size()||tab>=pane.pending.size()||",callback)
  self.assertIn("pane.pending[tab])return;",callback)
  self.assertIn("selection.SelectedItems().Size()!=expectedSelection->size()",callback)
  self.assertIn("pane.tabs[tab].indexedItem(",callback)
  self.assertIn("indexed->isFileSystem()",callback)
  self.assertIn("std::sort(actualSelection.begin(),actualSelection.end());",callback)
  self.assertIn("if(actualSelection!=*expectedSelection)return;",callback)
  self.assertLess(callback.index("if(actualSelection!=*expectedSelection)return;"),
                  callback.index("if(code==0)ui->StatusText().Text("))
  # A selection changed by the user must not launch a second Shell verb,
  # refresh unrelated files, or rewrite an unrelated status.
  self.assertNotIn("shellcontext::show(",callback)

 def test_no_automatic_external_command_execution(self):
  a=src("tests/winui/test_shell_gui.py")
  b=src("tests/winui/test_owned_thumbnail_gui.py")
  self.assertNotIn("InvokeCommand",a+b)
  self.assertNotIn("TrackPopupMenuEx",a+b)
class OwnedContextInvocationRegression(unittest.TestCase):
 def test_late_selection_gui_oracle_is_owned_and_observable(self):
  probe=src("tests/winui/test_owned_context_properties_gui.py")
  for token in (
      'third = source / "properties-test-third-owned.txt"',
      'original = {path: path.read_bytes() for path in (a, b, third)}',
      'def select_different_pair():',
      'assert pid_of(app_hwnd) == app.pid',
      'first.iface_selection_item.Select()',
      'replacement.iface_selection_item.AddToSelection()',
      'not old.is_selected()',
      'before_close_status = status_view.window_text()',
      'assert status_view.window_text() == before_close_status',
      'OWNED_PROPERTIES_STALE_SELECTION_STATUS_SUPPRESSED',
      'OWNED_PROPERTIES_EXPLICIT_EXTENSION_CHOICE',
      'item.window_text() == "추가 옵션 표시"',
      'item.element_info.process_id == app.pid',
      'extension.click_input()',
      'all(p.read_bytes() == data for p, data in original.items())',
  ):
   self.assertIn(token,probe)
  # The established owned context test identifies this WinUI menu item
  # without a provider-dependent UIA visibility/enabled heuristic.
  self.assertNotIn('and item.is_visible() and item.is_enabled()',probe)
  self.assertLess(probe.index('keyboard.send_keys("+{F10}")'),
                  probe.index('extension.click_input()'))
  self.assertLess(probe.index('extension.click_input()'),
                  probe.index('def spawned():'))
  self.assertLess(probe.index('def select_different_pair():'),
                  probe.index('assert user.PostMessageW(dialog_hwnd, 0x10, 0, 0)'))
  self.assertLess(probe.index('assert user.PostMessageW(dialog_hwnd, 0x10, 0, 0)'),
                  probe.index('assert status_view.window_text() == before_close_status'))
  self.assertNotIn('os.system(',probe)
  self.assertNotIn('shellcontext::show(',probe)
  # This functional oracle must not report PASS after forced WinUI teardown
  # or keep a screenshot potentially containing unrelated desktop windows.
  self.assertNotIn('ImageGrab',probe)
  self.assertNotIn('owned-multi-properties-dialog.png',probe)
  self.assertIn('normal_exit = app.poll() == 0',probe)
  self.assertIn('OWNED_MULTI_PROPERTIES_APP_EXIT_ZERO',probe)
  self.assertIn('if completed and unchanged and files_unchanged and normal_exit:',probe)
  self.assertIn('return 0 if completed and unchanged and files_unchanged and normal_exit else 1',probe)

 def test_right_click_uses_only_intersection_of_owned_row_and_list(self):
  probe=src("tests/winui/test_owned_context_menu_gui.py")
  self.assertIn("left=max(item.left,area.left)",probe)
  self.assertIn("right=min(item.right,area.right)",probe)
  self.assertIn("top=max(item.top,area.top)",probe)
  self.assertIn("bottom=min(item.bottom,area.bottom)",probe)
  self.assertIn('OWNED_CONTEXT_RIGHT_CLICK_EXPLICIT_HELPER',probe)
  self.assertIn('choose_extension_menu()',probe)
  self.assertIn('mouse.click(button="right",coords=click)',probe)
  self.assertIn('keyboard.send_keys("+{F10}")',probe)
  self.assertIn('user.keybd_event(0x5d,0,0,0)',probe)
  self.assertIn('user.keybd_event(0x5d,0,2,0)',probe)
  self.assertIn('OWNED_CONTEXT_APPLICATION_KEY_MENU_CANCEL',probe)
  self.assertIn('OWNED_CONTEXT_MULTI_SHIFT_F10_MENU_CANCEL',probe)
  self.assertIn('OWNED_CONTEXT_MULTI_FILE_UNCHANGED',probe)
  self.assertIn('"--context-menu" in q.cmdline()',probe)
  self.assertIn('pid.value==child.pid',probe)
  self.assertNotIn('Windows Shell isolated context menu',probe)
  self.assertIn('item.window_text()=="추가 옵션 표시"',probe)

if __name__=="__main__":unittest.main()

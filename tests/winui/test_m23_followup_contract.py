"""Current ko-KR resource, drag-gate and file-list-state contracts."""
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2]
A=R/"app/winui"
X="{http://schemas.microsoft.com/winfx/2006/xaml}Uid"
def source(filename):return (A/filename).read_text(encoding="utf-8-sig")
class M23Followup(unittest.TestCase):
 def test_korean_resource_keys_match_original_static_winui_fallback(self):
  resources=ET.parse(A/"Strings/ko-KR/Resources.resw").getroot()
  lookup={entry.get("name"):entry.findtext("value")
          for entry in resources.findall("data")}
  found=0
  for name in ("MainWindow.xaml","FileToolbar.xaml","NavigationSidebar.xaml"):
   page=ET.parse(A/name).getroot()
   for control in page.iter():
    uid=control.get(X)
    if not uid:continue
    for attribute in ("Content","Header","PlaceholderText","ToolTipService.ToolTip"):
     key=uid+"."+attribute
     if key not in lookup:continue
     value=control.get(attribute) if attribute!="ToolTipService.ToolTip" else (
       control.get("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}ToolTipService.ToolTip"))
     if value is not None:
      self.assertEqual(lookup[key],value,key)
      found+=1
  self.assertGreaterEqual(found,7)
 def test_latest_document_summaries_not_corrupted(self):
  docs=R/"docs/development"
  for name in ("CURRENT_STATUS.md","README.md","ARCHITECTURE.md",
               "UI_VISUAL_RETEST.md"):
   text=(docs/name).read_text(encoding="utf-8")
   self.assertIn("flyExplorer",text,name)
   self.assertNotIn(chr(0xfffd),text,name)
  status=(docs/"CURRENT_STATUS.md").read_text(encoding="utf-8")
  self.assertIn("v7",status)
  self.assertIn("physical pointer drag acceptance",status)
  history=(docs/"ERROR_HISTORY.md").read_text(encoding="utf-8")
  self.assertTrue(history.startswith("# Error history"))
  self.assertIn("append-only",history[:400])

 def test_fixed_seven_true_hangul_drop_failure_messages(self):
  drag=source("m23_drag.cpp")
  self.assertNotIn('StatusText().Text(L"?',drag)
  for word in ("원본 폴더가 변경됐습니다","최대 32개",
               "서로 다른 원본 폴더","파일 놓기 데이터를 읽지 못했습니다"):
   self.assertIn(word,drag)
 def test_owned_drag_trace_only_when_opted_in(self):
  s=source("m23_drag.cpp")
  self.assertIn('FLY_M23_OWNED_DRAG_TRACE',s)
  self.assertIn('traceOwnedDrag()',s)
 def test_file_list_cache_has_one_per_pane_state_owner(self):
  state=source("file_list_state.h")
  window=source("MainWindow.xaml.h")
  owner=source("window_tab_state.h")
  render=source("MainWindow.xaml.cpp")
  for name in ("sortMode","details","renderedLogical","renderedPaths",
               "indexedNameProjection","epoch",
               "invalidate()","isCurrent(","accepts("):
   self.assertIn(name,state)
  self.assertIn("std::array<fxfile::previewlist::PaneState,2> fileLists",owner)
  self.assertIn('ClInclude Include="file_list_state.h"',source("flyExplorer.project-template.xml"))
  self.assertIn("FileDetailController mFileDetails",window)
  self.assertNotIn("mDetailCancel",window)
  self.assertIn("listState.begin(route,tab)",render)
  self.assertIn("listState.isCurrent(",render)
  self.assertIn("ActiveWindowTab().fileLists[side].accepts(",render)

 def test_owned_physical_drag_requires_manual_input_not_automatic_claim(self):
  probe=(R/"tests/winui/manual_owned_drag_probe.py").read_text(encoding="utf-8-sig")
  doc=(R/"docs/development/UI_VISUAL_RETEST.md").read_text(encoding="utf-8")
  status=(R/"docs/development/CURRENT_STATUS.md").read_text(encoding="utf-8")
  for item in ("FLY_M23_OWNED_DRAG_TRACE","tempfile.mkdtemp",
               "stdin=subprocess.DEVNULL","OWNED_FILE_COPY=","NOT_OBSERVED"):
   self.assertIn(item,probe)
  self.assertIn("physical pointer drag",doc)
  self.assertIn("manual/environment gates",doc)
  self.assertIn("physical pointer drag acceptance",status)
  self.assertIn("Not certified",status)

 def test_expanded_panels_preserve_accessible_panes_in_small_windows(self):
  page=ET.parse(A/"MainWindow.xaml").getroot()
  names="{http://schemas.microsoft.com/winfx/2006/xaml}Name"
  workspace=next(e for e in page.iter() if e.get(names)=="WorkspacePanel")
  lines=list(workspace)
  self.assertEqual(2,len(lines))
  self.assertTrue(all(e.tag.endswith("StackPanel") for e in lines))
  self.assertTrue(any(e.get(names)=="ClearSessionButton" for e in lines[1].iter()))
  self.assertTrue(any(e.get(names)=="SaveWorkspaceButton" for e in lines[0].iter()))
  search=next(e for e in page.iter() if e.get(names)=="SearchMatches")
  self.assertEqual("64",search.get("Height"))
  sidebar=ET.parse(A/"NavigationSidebar.xaml").getroot()
  self.assertTrue(any(e.tag.endswith("ScrollViewer") for e in sidebar.iter()))
  native=source("m19_features.cpp")
  self.assertIn("#include <winrt/Microsoft.UI.Windowing.h>",native)
  self.assertIn("#include <winrt/Windows.Graphics.h>",native)
  self.assertIn("EnsureExpandedPanelFits()",native)
  self.assertIn("MonitorFromPoint(",native)
  self.assertIn("monitor.rcWork.bottom-position.Y",native)
  self.assertIn("desired>=560&&desired>size.Height+40",native)
  self.assertNotIn("desired>=640",native)
  harness=(R/"tests/winui/test_shell_gui.py").read_text(encoding="utf-8-sig")
  self.assertIn("FLY_OWNED_COMPACT_MONITOR_CASE",harness)
  self.assertIn("u.SetWindowPos(hwnd,None,78,78,960,519,0x0014)",harness)

 def test_type_classification_does_not_invoke_shell_extension_on_ui_thread(self):
  impl=source("MainWindow.xaml.cpp")
  worker=source("file_detail_controller.cpp")
  self.assertIn('entry.typeLabel=L"폴더"',worker)
  self.assertIn('L" 파일"',worker)
  self.assertIn('if(!meta.typeLabel.empty())',impl)
  self.assertNotIn('SHGetFileInfo',worker)
  self.assertNotIn('fxfile::filetype::queryVisuals(',impl)
if __name__=="__main__":unittest.main()

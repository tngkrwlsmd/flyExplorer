"""M2.3 follow-up: real ko-KR resource wiring and conservative type display."""
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2]
A=R/"experiments/phase6_winui_shell"
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
  self.assertGreaterEqual(found,15)
 def test_latest_document_summaries_not_corrupted(self):
  docs=R/"docs/development"
  names=("CURRENT_STATUS.md","README.md",
         "WINUI3_FULL_REPLACEMENT_20260929.md",
         "ERROR_HISTORY.md",
         "WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md")
  for name in names:
   text=(docs/name).read_text(encoding="utf-8")
   self.assertIn("M2.3 후속" if name!="ERROR_HISTORY.md" else "M2.3 한국어",text,name)
   self.assertNotIn("M2.3 ??:",text[:500],name)
   self.assertNotIn("M2.3 ?? ??:",text[:500],name)
   self.assertNotIn("## ??",text[-500:],name)
   self.assertNotIn(chr(0xfffd),text[:350],name)

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
  render=source("MainWindow.xaml.cpp")
  for name in ("sortMode","details","renderedPaths","epoch",
               "invalidate()","isCurrent(","accepts("):
   self.assertIn(name,state)
  self.assertIn("std::array<fxfile::previewlist::PaneState,2> mFileLists",window)
  self.assertIn('ClInclude Include="file_list_state.h"',source("FlyExplorerWinUIShell.project-template.xml"))
  self.assertNotIn("mFileDetails",window)
  self.assertIn("mFileLists[side].begin(route,tab)",render)
  self.assertIn("mFileLists[side].isCurrent(",render)
  self.assertIn("mFileLists[side].accepts(ticket,route,tab)",render)

 def test_owned_physical_drag_requires_manual_input_not_automatic_claim(self):
  probe=source("manual_owned_drag_probe.py")
  doc=(R/"docs/development"/
       "WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md").read_text(encoding="utf-8")
  for item in ("FLY_M23_OWNED_DRAG_TRACE","tempfile.mkdtemp",
               "stdin=subprocess.DEVNULL","OWNED_FILE_COPY=","NOT_OBSERVED"):
   self.assertIn(item,probe)
  self.assertIn("수동 드래그 판별 절차",doc)
  self.assertIn("NOT TESTED",doc)

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
  harness=source("test_shell_gui.py")
  self.assertIn("FLY_OWNED_COMPACT_MONITOR_CASE",harness)
  self.assertIn("u.SetWindowPos(hwnd,None,78,78,960,519,0x0014)",harness)

 def test_type_classification_does_not_invoke_shell_extension_on_ui_thread(self):
  impl=source("MainWindow.xaml.cpp")
  self.assertIn('entry.typeLabel=L"폴더"',impl)
  self.assertIn('L" 파일"',impl)
  self.assertIn('if(!meta.typeLabel.empty())',impl)
  self.assertNotIn('SHGetFileInfo',impl)
if __name__=="__main__":unittest.main()

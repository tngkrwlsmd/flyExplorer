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
 def test_type_classification_does_not_invoke_shell_extension_on_ui_thread(self):
  impl=source("MainWindow.xaml.cpp")
  self.assertIn('entry.typeLabel=L"폴더"',impl)
  self.assertIn('L" 파일"',impl)
  self.assertIn('if(!meta.typeLabel.empty())',impl)
  self.assertNotIn('SHGetFileInfo',impl)
if __name__=="__main__":unittest.main()

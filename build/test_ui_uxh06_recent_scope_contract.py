"""UXH-06 new native search scope acceptance contract."""
from pathlib import Path
import unittest,xml.etree.ElementTree as ET,re
R=Path(__file__).resolve().parents[1]
class RecentScopeContract(unittest.TestCase):
 def test_new_control_ids_unique(self):
  text=(R/"src/fxfile/resource.h").read_text(encoding="utf-8-sig")
  ids={}
  for label,value in re.findall(r"(?m)^#define\s+([A-Za-z_][A-Za-z_0-9]*)\s+(\d+)\s*$",text):
   ids.setdefault(int(value),[]).append(label)
  for number in range(1859,1865):
   self.assertEqual(len(ids.get(number,[])),1,(number,ids.get(number)))
  self.assertEqual(ids[1859],["IDC_SEARCH_SCOPE_PREVIEW"])
  self.assertEqual(ids[1864],["IDC_SEARCH_REMEMBER"])
 def test_explicit_opt_in_and_scope_privacy(self):
  cpp=(R/"src/fxfile/search_dlg.cpp").read_text(encoding="utf-8-sig")
  rc=(R/"src/fxfile/fxfile.rc").read_text(encoding="utf-8-sig")
  for term in ("BST_UNCHECKED","IDC_SEARCH_REMEMBER",
      "sIncDirDeque.size() == 1","sExcDirDeque.empty()",
      "FILE_ATTRIBUTE_DIRECTORY","sRecent->InsertString(0",
      "sRecent->GetCount() > 8","sRecent->ResetContent()",
      "IDC_SEARCH_SCOPE_FULL","OnRecentLocation"):
   self.assertIn(term,cpp)
  for term in ("ES_READONLY","IDC_SEARCH_REMEMBER",
               "IDC_SEARCH_RECENT_CLEAR","CBS_DROPDOWNLIST"):
   self.assertIn(term,rc)
  self.assertIn("RecentLocations",cpp)
 def test_korean_source_and_optional_legacy_stage(self):
  # bin/ is an ignored, generated legacy-MFC staging directory. Canonical
  # WinUI main must pass source validation on a clean checkout without
  # requiring stale native build output to be present.
  a=(R/"src/fxfile/Languages/Korean.xml").read_text(encoding="utf-8-sig")
  ET.fromstring(a)
  keys=("popup.search.button.full_scope",
       "popup.search.label.recent_locations",
       "popup.search.button.clear_recent",
       "popup.search.check.remember_location")
  for key in keys:self.assertIn(key,a)
  staged=R/"bin/x64/Languages/Korean.xml"
  if staged.is_file():
   b=staged.read_text(encoding="utf-8-sig")
   ET.fromstring(b)
   for key in keys:self.assertIn(key,b)
if __name__=="__main__":unittest.main()

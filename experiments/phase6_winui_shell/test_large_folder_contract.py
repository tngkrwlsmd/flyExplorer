"""Static ownership and realistic large-folder smoke requirements."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parent
class FolderScaleContract(unittest.TestCase):
 def test_1100_files_below_existing_1200_guard(self):
  body=(ROOT/"test_large_owned_folder_gui.py").read_text(encoding="utf-8")
  app=(ROOT/"MainWindow.xaml.cpp").read_text(encoding="utf-8")
  for item in ('range(1100)',"bench-0000.txt","bench-1099.txt",
               "process.pid","LEGACY_PRESENT_SETTINGS_UNCHANGED",
               'auto_id="SortPicker"'):
   self.assertIn(item,body)
  self.assertIn("if(items.size()>1200)return",app)
  self.assertNotIn("EmptyClipboard(",body)
  supervisor=(ROOT.parents[1]/"src/base/shell_isolated_supervisor.cpp").read_text(
      encoding="utf-8")
  self.assertIn("Exit is not EOF.",supervisor)
  self.assertIn("readProgress=(received!=0);",supervisor)
  self.assertIn("!expected||frame.size()<expected",supervisor)

if __name__=="__main__":unittest.main()

"""Static ownership and realistic large-folder smoke requirements."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]/"app"/"winui"
class FolderScaleContract(unittest.TestCase):
 def test_1100_2300_and_5000_bounded_paged_owned_files(self):
  body=(Path(__file__).resolve().parent/"test_large_owned_folder_gui.py").read_text(encoding="utf-8")
  app=(ROOT/"MainWindow.xaml.cpp").read_text(encoding="utf-8")
  detail=(ROOT/"file_detail_controller.cpp").read_text(encoding="utf-8")
  for item in ('choices=(1100,2300,5000)','range(args.items)',"bench-0000.txt","bench-1099.txt",
               "process.pid","LEGACY_PRESENT_SETTINGS_UNCHANGED",
               'auto_id="SortPicker"'):
   self.assertIn(item,body)
  self.assertIn("if(items.size()>1200)return",app) # Native optional metadata is deferred for huge folders.
  self.assertIn("OnLoadMoreFiles(",app)
  self.assertIn("state.visibleCount+160",app)
  self.assertIn("OnNameFilterChanged(",app)
  self.assertIn("order.erase(std::remove_if(",app)
  self.assertIn("state.filteredCount=order.size()",app)
  self.assertIn('SetName(\n            button,hstring(',app)
  self.assertIn('side==0?L"\\uC67C\\uCABD \\uB354 \\uD45C\\uC2DC ":L"\\uC624\\uB978\\uCABD \\uB354 \\uD45C\\uC2DC "',app)
  self.assertIn("mFileDetails.cancel(side)",app)
  self.assertIn("if(cancelToken->load())return; // prevent stale metadata child launch",detail)
  self.assertIn("thumbnailBudget<4",detail)

  ui=(ROOT/"MainWindow.xaml").read_text(encoding="utf-8")
  self.assertIn("LeftNameFilterBox",ui)
  self.assertIn("RightNameFilterBox",ui)
  self.assertIn("OnNameFilterChanged",ui)
  shortcut=(ROOT/"m22_transfers.cpp").read_text(encoding="utf-8")
  self.assertIn("LeftNameFilterBox()",shortcut)
  self.assertIn("GetKeyState(VK_SHIFT)",shortcut)
  self.assertIn("OWNED_LARGE_CTRL_SHIFT_F_FILTER_FOCUS",body)
  self.assertIn("state.visibleRoute!=nextRoute",app)
  native=(ROOT.parents[1]/"src/base/shell_isolation_wire.h").read_text(encoding="utf-8")
  self.assertIn("kMaxEntries=6000",native)
  self.assertIn("kMaxBody=8u*1024u*1024u",native)
  self.assertNotIn("EmptyClipboard(",body)
  supervisor=(ROOT.parents[1]/"src/base/shell_isolated_supervisor.cpp").read_text(
      encoding="utf-8")
  self.assertIn("Exit is not EOF.",supervisor)
  self.assertIn("readProgress=(received!=0);",supervisor)
  self.assertIn("!expected||frame.size()<expected",supervisor)

if __name__=="__main__":unittest.main()

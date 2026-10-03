"""Bounded shell image thumbnail safety and render contracts."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[2]
def src(name):return (R/name).read_text(encoding="utf-8")
class ThumbnailContract(unittest.TestCase):
 def test_thumbnail_handler_stays_in_one_shot_owned_shell_child(self):
  helper=src("app/winui/helper/FlyShellIsolationHelper.cpp")
  for token in ('L"--file-thumbnail"','GetFileAttributesW(part.c_str())',
                'IShellItemImageFactory','SIIGBF_THUMBNAILONLY',
                'GetDIBits','exactWrite(output,pixels.data()'):
   self.assertIn(token,helper)
  app=src("app/winui/MainWindow.xaml.cpp")
  self.assertNotIn("IShellItemImageFactory",app)
  self.assertNotIn("SHGetFileInfoW",app)
 def test_bounded_worker_and_stale_route_guards_preserved(self):
  client=src("src/base/shell_thumbnail_core.cpp")
  for token in ('timeoutMs<200','timeoutMs>10000','requestedPixels<16',
                'requestedPixels>128','GetTickCount64',
                'PeekNamedPipe','TerminateProcess(process.value',
                'filename()!=L"FlyShellIsolationHelper.exe"',
                'width>128','height>128'):
   self.assertIn(token,client)
  app=src("app/winui/MainWindow.xaml.cpp")
  worker=src("app/winui/file_detail_controller.cpp")
  for token in ('thumbnailBudget<4','request.viewMode==FileViewMode::MediumIcons',
                'fxfile::thumbnail::query('):
   self.assertIn(token,worker)
  for token in ('L"Windows Shell image thumbnail"',
                'ActiveWindowTab().fileLists[side].accepts('):
   self.assertIn(token,app)
  template=src("app/winui/flyExplorer.project-template.xml")
  self.assertIn("shell_thumbnail_core.cpp",template)
if __name__=="__main__":unittest.main()

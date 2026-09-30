"""Bounded shell image thumbnail safety and render contracts."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[2]
def src(name):return (R/name).read_text(encoding="utf-8")
class ThumbnailContract(unittest.TestCase):
 def test_thumbnail_handler_stays_in_one_shot_owned_shell_child(self):
  helper=src("experiments/phase6_winui_shell/isolation/FlyShellIsolationHelper.cpp")
  for token in ('L"--file-thumbnail"','GetFileAttributesW(part.c_str())',
                'IShellItemImageFactory','SIIGBF_THUMBNAILONLY',
                'GetDIBits','exactWrite(output,pixels.data()'):
   self.assertIn(token,helper)
  app=src("experiments/phase6_winui_shell/MainWindow.xaml.cpp")
  self.assertNotIn("IShellItemImageFactory",app)
  self.assertNotIn("SHGetFileInfoW",app)
 def test_bounded_worker_and_stale_route_guards_preserved(self):
  client=src("src/base/shell_thumbnail_core.cpp")
  for token in ('timeoutMs<200','timeoutMs>10000','GetTickCount64',
                'PeekNamedPipe','TerminateProcess(process.value',
                'filename()!=L"FlyShellIsolationHelper.exe"',
                'width>128','height>128'):
   self.assertIn(token,client)
  app=src("experiments/phase6_winui_shell/MainWindow.xaml.cpp")
  for token in ('thumbnailBudget<4','fxfile::thumbnail::query(',
                'L"Windows Shell image thumbnail"',
                'mFileLists[side].accepts(ticket,route,tab)'):
   self.assertIn(token,app)
  template=src("experiments/phase6_winui_shell/FlyExplorerWinUIShell.project-template.xml")
  self.assertIn("shell_thumbnail_core.cpp",template)
if __name__=="__main__":unittest.main()

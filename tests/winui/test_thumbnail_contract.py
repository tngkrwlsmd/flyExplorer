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
 def test_network_and_removable_thumbnail_validation_stays_inside_owned_child(self):
  client=src("src/base/shell_thumbnail_core.cpp")
  helper=src("app/winui/helper/FlyShellIsolationHelper.cpp")
  self.assertIn("thumbnailCandidate",client)
  self.assertNotIn("GetDriveTypeW",client)
  self.assertNotIn("GetFileAttributesW",client)
  self.assertIn(r'value.rfind(L"\\\\?\\",0)==0',client)
  self.assertIn(r'value.rfind(L"\\\\.\\",0)==0',client)
  self.assertIn(
      "fxfile::shelltransfer::transferDriveRoot(source,root)",helper)
  self.assertIn("driveType!=DRIVE_FIXED&&driveType!=DRIVE_REMOVABLE&&",helper)
  self.assertIn("driveType!=DRIVE_REMOTE",helper)
  self.assertIn("GetFileAttributesW(part.c_str())",helper)
  self.assertIn("GetFileAttributesExW(path.c_str()",helper)

 def test_virtual_provider_thumbnail_stays_in_exact_owned_visual_helper(self):
  assoc=src("src/base/shell_assoc_type_core.cpp")
  helper=src("app/winui/helper/FlyShellIsolationHelper.cpp")
  worker=src("app/winui/file_detail_controller.cpp")
  wire=src("src/base/shell_visual_wire.h")
  for token in ("thumbnailHints","kMaxThumbnailItems",
                "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
                "PROC_THREAD_ATTRIBUTE_HANDLE_LIST"):
   self.assertIn(token,assoc)
  for token in ("SHCreateItemFromIDList(","IShellItemImageFactory",
                "SIIGBF_THUMBNAILONLY",
                "thumbnailWidth,thumbnailHeight",
                "static_cast<std::uint32_t>(thumbnail.size())"):
   self.assertIn(token,helper)
  for token in ("shellThumbnailHints","shellVisual.thumbnailBgra",
                "request.shellProviderRoot"):
   self.assertIn(token,worker)
  for token in ("kMaxThumbnailItems=4","kWantThumbnail=1u",
                "thumbnailPixelBytes"):
   self.assertIn(token,wire)

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
  for token in ('thumbnailBudget<4','request.viewMode==FileViewMode::MediumIcons||',
                'request.viewMode==FileViewMode::LargeIcons',
                'fxfile::thumbnail::query('):
   self.assertIn(token,worker)
  for token in ('L"Windows Shell image thumbnail"',
                'ActiveWindowTab().fileLists[side].accepts('):
   self.assertIn(token,app)
  template=src("app/winui/flyExplorer.project-template.xml")
  self.assertIn("shell_thumbnail_core.cpp",template)
if __name__=="__main__":unittest.main()

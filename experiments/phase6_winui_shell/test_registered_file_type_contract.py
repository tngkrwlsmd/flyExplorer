"""Isolated OS-registered file types: bounded one-shot child, never UI Shell extension."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/"experiments"/"phase6_winui_shell"
def source(path):return (ROOT/path).read_text(encoding="utf-8")
class FileTypeContract(unittest.TestCase):
 def test_same_exact_owned_helper_has_safe_extension_protocol(self):
  helper=source("experiments/phase6_winui_shell/isolation/FlyShellIsolationHelper.cpp")
  native=source("src/base/shell_assoc_type_core.cpp")
  for item in ('L"--file-types"','SHGFI_USEFILEATTRIBUTES|SHGFI_TYPENAME',
               'WriteFile(output,line.data()', 'argc>26'):
   self.assertIn(item,helper)
  for item in ('safeExtension','input.size()>24','timeoutMs<100',
               'timeoutMs>10000','GetTickCount64','PeekNamedPipe',
               'TerminateProcess(process.h','MB_ERR_INVALID_CHARS'):
   self.assertIn(item,native)
  self.assertIn('filename()!=L"FlyShellIsolationHelper.exe"',native)
  for name in ('SHGFI_ICON|SHGFI_SMALLICON','DrawIconEx',
               'DestroyIcon(info.hIcon)','CryptBinaryToStringA'):
   self.assertIn(name,helper)
  for name in ('queryVisuals','CryptStringToBinaryA','required==1024'):
   self.assertIn(name,native)
 def test_app_uses_one_background_batch_with_generic_fallback(self):
  app=source("experiments/phase6_winui_shell/MainWindow.xaml.cpp")
  self.assertIn('std::thread([side,tab,route,ticket,cancel,paths=',app)
  self.assertIn('fxfile::filetype::queryVisuals(',app)
  self.assertIn('if(!fxfile::filetype::safeExtension(ext))continue;',app)
  self.assertIn('entry.typeLabel',app)
  self.assertNotIn('SHGetFileInfoW',app)
  self.assertIn("iconMeta->thumbnailBgra",app)
  self.assertIn("thumbnailBudget<4",app)
  self.assertIn("fxfile::thumbnail::query(",app)
  self.assertIn("WriteableBitmap pixels(",app)
  self.assertIn("IBufferByteAccess",app)
  self.assertIn("recover.size()>=2",app)
  self.assertIn("visualHelper,{ext},1350",app)
  self.assertIn("Windows system registered file icon",app)
  project=source("experiments/phase6_winui_shell/FlyExplorerWinUIShell.project-template.xml")
  self.assertIn('shell_assoc_type_core.cpp',project)
class RealFileListColumnContract(unittest.TestCase):
 def test_name_type_size_date_columns_and_icon_do_not_break_uia(self):
  xml=(A/"MainWindow.xaml").read_text(encoding="utf-8")
  impl=(A/"MainWindow.xaml.cpp").read_text(encoding="utf-8")
  state=(A/"file_list_state.h").read_text(encoding="utf-8")
  for item in ("LeftNameWidthSlider","RightNameWidthSlider",
               "OnNameColumnWidthChanged","Windows \uC720\uD615"):
   self.assertIn(item,xml)
  for item in ("mColumnControlsReady","nameColumnWidth","FontIcon glyph;",
               "Grid::SetColumn(field,col);","AutomationProperties::SetName(",
               "OnNameColumnWidthChanged("):
   self.assertIn(item,impl)
  self.assertIn("double nameColumnWidth=168.0",state)
  owned=(A/"test_m22_gui.py").read_text(encoding="utf-8")
  for token in ("GetDpiForWindow","SystemParametersInfoW",
                "REAL_M24_OWNED_FILE_ROW_AND_COLUMN_ACCESSIBLE_NAMES"):
   self.assertIn(token,owned)
  self.assertNotIn('"?.txt"',owned)

if __name__=="__main__":unittest.main()

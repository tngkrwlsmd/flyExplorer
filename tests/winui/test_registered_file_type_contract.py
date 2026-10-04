"""Isolated OS-registered file types: bounded one-shot child, never UI Shell extension."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/"app"/"winui"
def source(path):return (ROOT/path).read_text(encoding="utf-8")
class FileTypeContract(unittest.TestCase):
 def test_same_exact_owned_helper_has_safe_extension_protocol(self):
  helper=source("app/winui/helper/FlyShellIsolationHelper.cpp")
  native=source("src/base/shell_assoc_type_core.cpp")
  for item in ('L"--file-types"','SHGFI_USEFILEATTRIBUTES|SHGFI_TYPENAME',
               'WriteFile(output,line.data()', 'requestVisuals?27:26'):
   self.assertIn(item,helper)
  for item in ('safeExtension','input.size()>24','timeoutMs<100',
               'timeoutMs>10000','GetTickCount64','PeekNamedPipe',
               'TerminateProcess(process.h','MB_ERR_INVALID_CHARS'):
   self.assertIn(item,native)
  self.assertIn('filename()!=L"FlyShellIsolationHelper.exe"',native)
  for name in ('SHGFI_ICON','SHGFI_SMALLICON','SHGFI_LARGEICON',
               'L".flyfolder"','visualPixels','DrawIconEx',
               'DestroyIcon(info.hIcon)','CryptBinaryToStringA'):
   self.assertIn(name,helper)
  for name in ('queryVisuals','requestedPixels','CryptStringToBinaryA',
               'const auto expected=requestedPixels*requestedPixels*4'):
   self.assertIn(name,native)
 def test_app_uses_one_background_batch_with_generic_fallback(self):
  app=source("app/winui/MainWindow.xaml.cpp")
  worker=source("app/winui/file_detail_controller.cpp")
  self.assertIn('std::thread([',worker)
  self.assertIn('fxfile::filetype::queryVisuals(',worker)
  self.assertIn('if(!fxfile::filetype::safeExtension(ext))continue;',worker)
  self.assertIn('entry.typeLabel',worker)
  self.assertNotIn('SHGetFileInfoW',worker)
  self.assertIn("iconMeta->thumbnailBgra",app)
  self.assertIn("thumbnailBudget<4",worker)
  self.assertIn("fxfile::thumbnail::query(",worker)
  self.assertIn("WriteableBitmap pixels(",app)
  self.assertIn("IBufferByteAccess",app)
  self.assertIn("recover.size()>=2",worker)
  self.assertIn("visualHelper,{ext},1350",worker)
  self.assertIn("Windows system registered file icon",app)
  self.assertIn("Windows Shell folder icon",app)
  self.assertIn('extensions{L".flyfolder"}',worker)
  self.assertIn("RasterizationScale()",app)
  self.assertIn("request.viewMode==FileViewMode::MediumIcons||",worker)
  self.assertIn("request.viewMode==FileViewMode::LargeIcons",worker)
  project=source("app/winui/flyExplorer.project-template.xml")
  self.assertIn('shell_assoc_type_core.cpp',project)
class RealFileListColumnContract(unittest.TestCase):
 def test_name_type_size_date_columns_and_icon_do_not_break_uia(self):
  xml=(A/"MainWindow.xaml").read_text(encoding="utf-8")
  impl=(A/"MainWindow.xaml.cpp").read_text(encoding="utf-8")
  state=(A/"file_list_state.h").read_text(encoding="utf-8")
  for item in ("LeftNameWidthSlider","RightNameWidthSlider",
               "OnNameColumnWidthChanged","OnDetailColumnResizeDragDelta",
               "LeftNameHeaderColumn","RightNameHeaderColumn",
               "LeftNameColumnResizeThumb","LeftTypeColumnResizeThumb",
               "LeftSizeColumnResizeThumb","RightNameColumnResizeThumb",
               "RightTypeColumnResizeThumb","RightSizeColumnResizeThumb"):
   self.assertIn(item,xml)
  import xml.etree.ElementTree as ET
  root=ET.parse(A/"MainWindow.xaml").getroot()
  labels={value for element in root.iter() for value in element.attrib.values()}
  for label in ("\uc774\ub984","\uc720\ud615","\ud06c\uae30","\uc218\uc815 \ub0a0\uc9dc"):
   self.assertIn(label,labels)
  for item in ("mColumnControlsReady","nameColumnWidth","typeColumnWidth",
               "sizeColumnWidth","FontIcon glyph;",
               "Grid::SetColumn(field,col);","AutomationProperties::SetName(",
               "OnNameColumnWidthChanged(","OnDetailColumnResizeDragDelta(",
               "grid.ColumnDefinitions().GetAt(column).Width(widths[column])"):
   self.assertIn(item,impl)
  self.assertIn("double nameColumnWidth=168.0",state)
  self.assertIn("double typeColumnWidth=180.0",state)
  self.assertIn("double sizeColumnWidth=80.0",state)
  owned=(ROOT/"tests/winui/test_m22_gui.py").read_text(encoding="utf-8")
  for token in ("GetDpiForWindow","SystemParametersInfoW",
                "REAL_M24_OWNED_FILE_ROW_AND_COLUMN_ACCESSIBLE_NAMES"):
   self.assertIn(token,owned)
  self.assertNotIn('"?.txt"',owned)
  resize=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text(
      encoding="utf-8")
  for token in ("LeftNameColumnResizeThumb","LeftTypeColumnResizeThumb",
                "LeftSizeColumnResizeThumb","mouse.press(button=\"left\"",
                "OWNED_DETAIL_COLUMN_NAME_RESIZE",
                "OWNED_DETAIL_COLUMN_TYPE_RESIZE",
                "OWNED_DETAIL_COLUMN_SIZE_RESIZE"):
   self.assertIn(token,resize)

if __name__=="__main__":unittest.main()

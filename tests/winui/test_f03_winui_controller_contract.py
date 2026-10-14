"""F03: opt-in text UI bridge remains bounded and fails closed on stale panes."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app/winui"
MAIN=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8")
ROUTER=(APP/"m24_preview.cpp").read_text(encoding="utf-8")
CONTROLLER=(APP/"preview_controller.cpp").read_text(encoding="utf-8")
HEADER=(APP/"MainWindow.xaml.h").read_text(encoding="utf-8")
XAML=(APP/"MainWindow.xaml").read_text(encoding="utf-8")

class F03WinUIControllerContract(unittest.TestCase):
    def test_no_implicit_reads_in_existing_details_pane(self):
        self.assertIn('mTextPreviewEnabled=false',HEADER)
        self.assertIn('Click="OnToggleTextPreview"',XAML)
        self.assertIn('TextPreviewStatus',XAML)
        self.assertIn('TextPreviewBody',XAML)
        self.assertIn('if(!mTextPreviewEnabled||!ActiveWindowTab().fileInfoPaneVisible)return;',ROUTER)
        self.assertIn('mTextPreviewEnabled=!mTextPreviewEnabled',ROUTER)
        self.assertIn('QueueTextPreview();',MAIN)
        self.assertIn('mTextPreviewController.prepareForClose();',MAIN)
        self.assertIn('CancelTextPreview();',MAIN)

    def test_background_io_only_and_exact_route_selection(self):
        for token in ('std::thread(', 'GetFileAttributesExW(', 'GetDriveTypeW(',
                      'previewpolicy::Kind::Text', 'previewsupervisor::run(',
                      'ticket.cancel->load()', 'gate_.begin('):
            self.assertIn(token,CONTROLLER)
        for forbidden in ('GetFileAttributesExW(', 'CreateProcessW(', 'ReadFile(',
                          'std::filesystem::file_size(', 'ShellExecute'):
            self.assertNotIn(forbidden,ROUTER)
        for token in ('renderedLogical', 'renderedPaths', 'indexedItem(',
                      'mTextPreviewController.accepts(result.ticket)',
                      'key.selectedIdentity', 'key.generation',
                      'key.window', 'mWorkspace.activeIndex()'):
            self.assertIn(token,ROUTER)
        self.assertIn('files.renderedPaths[slot]!=key.selectedIdentity',ROUTER)

    def test_build_and_xaml_structure(self):
        tree=ET.parse(APP/"flyExplorer.project-template.xml")
        compiles={x.get("Include","").replace("\\","/")
                  for x in tree.iter() if x.tag.endswith("ClCompile")}
        for unit in ("preview_controller.cpp","m24_preview.cpp"):
            self.assertIn(unit,compiles)
        root=ET.fromstring(XAML)
        ns={"x":"http://schemas.microsoft.com/winfx/2006/xaml"}
        by_name={n.get("{http://schemas.microsoft.com/winfx/2006/xaml}Name"):n
                 for n in root.iter()}
        for name in ("TextPreviewToggleButton","TextPreviewStatus","TextPreviewBody"):
            self.assertIn(name,by_name)

if __name__=="__main__":
    unittest.main()

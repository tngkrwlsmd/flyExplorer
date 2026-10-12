"""F01-A: per-pane display options, view and selection identity contracts."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
XNAME="{http://schemas.microsoft.com/winfx/2006/xaml}Name"

def body(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class FileDisplayOptionsContract(unittest.TestCase):
    def test_view_menu(self):
        doc=ET.parse(ROOT/"app/winui/FileToolbar.xaml")
        nodes={e.get(XNAME):e for e in doc.iter() if e.get(XNAME)}
        for key,handler in (("ViewCheckboxesItem","OnViewCheckboxes"),
                            ("ViewCompactRowsItem","OnViewCompactRows"),
                            ("ViewFileExtensionsItem","OnViewFileExtensions")):
            node=nodes[key]
            self.assertTrue(node.tag.endswith("ToggleMenuFlyoutItem"))
            self.assertEqual(node.get("Click"),handler)
            self.assertEqual(node.get("IsChecked"),
                             "True" if key=="ViewFileExtensionsItem" else "False")
            self.assertTrue(node.get("Text"))

    def test_pane_ownership_and_file_identity(self):
        state=body("app/winui/file_list_state.h")
        self.assertIn("bool showSelectionCheckboxes=false;",state)
        self.assertIn("bool compactRows=false;",state)
        self.assertIn("bool showFileExtensions=true;",state)
        main=body("app/winui/MainWindow.xaml.cpp")
        toggler=main.split("void MainWindow::ToggleListDisplay(",1)[1].split(
            "void MainWindow::UpdateViewPresentation(",1)[0]
        for token in ("ActiveWindowTab().model.activePane", "fileLists[side]",
                      "FillFiles(side)", "UpdateSelectionChrome()", "UpdateFooterSummary()"):
            self.assertIn(token,toggler)
        for forbidden in ("QueuePidl(", "PersistPreferences(", "RunTransfer("):
            self.assertNotIn(forbidden,toggler)
        self.assertIn("view.IsMultiSelectCheckBoxEnabled(display.showSelectionCheckboxes);",main)
        portion=main.split("if(state.compactRows &&",1)[1].split("if(decoratedRule)",1)[0]
        self.assertIn("FileViewMode::Details",portion)
        self.assertIn("FileViewMode::List",portion)
        self.assertIn("row.MinHeight(26);",portion)
        self.assertIn("state.renderedPaths.push_back(itemParsing)",main)
        self.assertIn("view.SelectedItems().Append(row)",main)

    def test_menu_state_synced_when_switching_active_pane(self):
        impl=body("app/winui/MainWindow.xaml.cpp")
        self.assertEqual(impl.count("SetListDisplayState("),4)
        self.assertIn("fileBar()->SetListDisplay([nativeWeak]",impl)
        self.assertIn("ActiveWindowTab().fileLists[side].compactRows",impl)
        self.assertIn("ActiveWindowTab().fileLists[side].showFileExtensions",impl)
        self.assertIn("void ToggleListDisplay(int option);",
                      body("app/winui/MainWindow.xaml.h"))
        toolbar=body("app/winui/FileToolbar.xaml.cpp")
        for needle in ("ViewCheckboxesItem().IsChecked(", "ViewCompactRowsItem().IsChecked(",
                       "ViewFileExtensionsItem().IsChecked(", "listDisplay_(0)",
                       "listDisplay_(1)", "listDisplay_(2)"):
            self.assertIn(needle,toolbar)

    def test_native_filename_extension_display_is_not_identity(self):
        source=body("app/winui/file_list_state.h")
        main=body("app/winui/MainWindow.xaml.cpp")
        for name in ('L"notes.txt"','L"archive.tar.gz"','L".gitignore"',
                     'L"name."','L"한글.문서"','L"virtual.pdf"'):
            self.assertIn("static_assert(visibleFileName("+name,source)
        self.assertIn("constexpr std::wstring_view visibleFileName(",source)
        self.assertIn("filesystemAt(index),state.showFileExtensions",main)
        self.assertEqual(main.count("filename.Text(hstring(displayName));"),2)
        self.assertIn('label+=L" | 실제 파일 이름: "+itemLabel;',main)
        self.assertIn("state.renderedPaths.push_back(itemParsing)",main)
        self.assertIn("fxfile::filterrules::Store::matches(itemLabel",main)
        self.assertIn("else state.showFileExtensions=!state.showFileExtensions;",main)
        toggler=main.split("void MainWindow::ToggleListDisplay(",1)[1].split(
            "void MainWindow::UpdateViewPresentation(",1)[0]
        for forbidden in ("QueuePidl(", "PersistPreferences(", "RunTransfer(",
                          "mShellNavigation->"):
            self.assertNotIn(forbidden,toggler)

if __name__=="__main__":
    unittest.main()

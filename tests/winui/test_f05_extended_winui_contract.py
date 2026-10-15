"""F05 WinUI mode bridge contract; source-only, not a GUI acceptance."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
XAML=(ROOT/'app/winui/FileToolbar.xaml').read_text(encoding='utf-8')
WINDOW=(ROOT/'app/winui/MainWindow.xaml.cpp').read_text(encoding='utf-8')
HEADER=(ROOT/'app/winui/file_list_state.h').read_text(encoding='utf-8')
BAR=(ROOT/'app/winui/FileToolbar.xaml.cpp').read_text(encoding='utf-8')
class F05ExtendedWinUIContract(unittest.TestCase):
    def test_four_explicit_menu_choices(self):
        tree=ET.fromstring(XAML)
        names={n.attrib.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name') for n in tree.iter()}
        for name in ('ViewGroupByTypeItem','ViewGroupByNameItem',
                     'ViewGroupBySizeItem','ViewGroupByMonthItem'):
            self.assertIn(name,names)
        for index in range(1,5):
            self.assertIn('group_('+str(index)+')',BAR)
    def test_complete_model_and_original_shell_identity(self):
        for term in ('state.groupTabCache.switchTo(nextRoute,pane.active,side)',
                     'state.groupTabCache.onCompleteModel(metadataReady,complete)',
                     'files.groupTabCache.toggle(title)',
                     'projectByType(', 'filegroup::projectBy(',
                     'groupIndices.emplace(logical,index)',
                     'state.metadata[index]',
                     'state.renderedLogical.push_back(logical)',
                     'state.renderedPaths.push_back(itemParsing)',
                     'if(grouped&&groupPage.entries[visible].kind=='):
            self.assertIn(term,WINDOW)
        self.assertIn('filegroup::TabGrouping groupTabCache{}',HEADER)
    def test_no_global_os_user_setting_mutation_in_new_toggle(self):
        block=WINDOW.split('void MainWindow::ToggleGroupMode(int choice)',1)[1].split(
            'void MainWindow::UpdateViewPresentation(int side)',1)[0]
        for term in ('SetFileAttributes','DeleteFile','CreateFile',
                     'SystemParametersInfoW','SetProcessDpiAwarenessContext'):
            self.assertNotIn(term,block)
if __name__=='__main__':unittest.main()

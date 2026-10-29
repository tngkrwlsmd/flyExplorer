"""Owned selection menu wiring and safe current-projection mutation boundaries."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'app'/'winui'


class SelectionCommandsContract(unittest.TestCase):
    def body(self):
        return (APP/'m22_transfers.cpp').read_text(encoding='utf-8').split(
            'void MainWindow::ChangeFileSelection(bool invert){',1)[1].split(
            'void MainWindow::HandleFileShortcut(',1)[0]

    def test_menu_routes_clear_and_invert_without_reusing_background_click(self):
        x=ET.parse(APP/'FileToolbar.xaml').getroot()
        nodes={e.get('Click'):e for e in x.iter() if e.get('Click')}
        self.assertEqual(nodes['OnClearFileSelection'].get('Text'),'선택 해제')
        self.assertEqual(nodes['OnInvertFileSelection'].get('Text'),'표시된 항목 선택 반전')
        toolbar=(APP/'FileToolbar.xaml.cpp').read_text(encoding='utf-8')
        header=(APP/'FileToolbar.xaml.h').read_text(encoding='utf-8')
        window=(APP/'MainWindow.xaml.cpp').read_text(encoding='utf-8')
        for name,command,invert in [('OnClearFileSelection',18,'false'),
                                    ('OnInvertFileSelection',19,'true')]:
            self.assertIn('void '+name+'(',header)
            self.assertIn('FileToolbar::'+name+'(IInspectable const&,RoutedEventArgs const&){if(action_)action_('+str(command)+');}',toolbar)
            self.assertIn('command=='+str(command)+')ui->ChangeFileSelection('+invert+');',window)

    def test_stale_pending_or_modal_projection_cannot_change_selection(self):
        body=self.body();guard=body.split('std::vector<IInspectable> next;',1)[0]
        for token in ('mClosing||mPopulatingFileLists||mFileOperations.busy()',
                      'mFileOperations.pendingConfirmationToken()',
                      'side<0||side>1||(side==1&&!window.model.split)',
                      'pane.pending[tab]', 'shown.visibleTab!=tab',
                      'shown.visibleRoute!=pane.routeIds[tab]',
                      'shown.renderedFolder!=pane.tabs[tab].snapshot().parsingName',
                      'unbox_value<std::uint64_t>(view.Tag())!=window.identity'):
            self.assertIn(token,guard)
        self.assertNotIn('ActivatePane(',body)
        for forbidden in ('QueueNextFolderPage(', 'SelectAll(', 'RunTransfer(',
                          'PersistPreferences(', 'OpenFolder(', 'CreateFileW('):
            self.assertNotIn(forbidden,body)

    def test_complement_is_captured_before_clear_and_published_after_batch(self):
        body=self.body()
        before=body.split('view.SelectedItems().Clear();',1)[0]
        self.assertIn('if(invert){',before)
        self.assertIn('for(auto const& value:view.Items())',before)
        self.assertIn('if(!row||!row.Tag())continue;',before)
        self.assertIn('indexedItem(static_cast<std::size_t>(logical))',before)
        self.assertIn('if(!row.IsSelected())next.push_back(value);',before)
        self.assertIn('~Reset(){flag=false;}',before)
        self.assertIn('mPopulatingFileLists=true;',before)
        after=body.split('view.SelectedItems().Clear();',1)[1]
        self.assertTrue(after.lstrip().startswith('for(auto const& item:next)view.SelectedItems().Append(item);'))
        for token in ('UpdateSelectionChrome();','UpdateFooterSummary();',
                      'QueueTextPreview();','view.Focus('):
            self.assertEqual(after.count(token),1)
        self.assertLess(after.index('SelectedItems().Append(item)'),
                        after.index('UpdateFooterSummary();'))


if __name__=='__main__':
    unittest.main()

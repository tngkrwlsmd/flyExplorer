"""Copy-as-path has explicit input, current ownership and a text-only writer."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'app/winui'


class CopyPathsContract(unittest.TestCase):
    def test_explicit_file_menu_and_ctrl_shift_c_are_distinct_from_file_copy(self):
        code=(APP/'m22_transfers.cpp').read_text(encoding='utf-8')
        menu=code.split('menu.Items().Append(make(L"경로 복사"',1)[1].split('menu.Items().Append(make',1)[0]
        self.assertIn('localSelection',menu)
        self.assertIn('CopySelectedToWindowsClipboard(side,false,true)',menu)
        keys=code.split('void MainWindow::HandleFileShortcut(',1)[1]
        self.assertLess(keys.index('if(ctrl&&shift&&!alt&&vk==Windows::System::VirtualKey::C)'),
                        keys.index('if(ctrl&&(vk==Windows::System::VirtualKey::C||'))
        self.assertIn('CopySelectedToWindowsClipboard(side,false,true);args.Handled(true);return;',keys)

    def test_copy_rechecks_exact_presentation_and_live_app_window(self):
        body=(APP/'m22_transfers.cpp').read_text(encoding='utf-8').split(
            'bool MainWindow::CopySelectedToWindowsClipboard(',1)[1].split(
            'void MainWindow::PasteFromWindowsClipboard()',1)[0]
        for token in ('mFileOperations.pendingConfirmationToken()',
                      'window.model.activePane!=side','shown.visibleTab!=tab',
                      'shown.visibleRoute!=pane.routeIds[tab]',
                      'shown.renderedFolder!=pane.tabs[tab].snapshot().parsingName',
                      'unbox_value<std::uint64_t>(view.Tag())!=window.identity',
                      'ownerPid!=::GetCurrentProcessId()',
                      'pathsOnly?fxfile::shellclipboard::writePathsText(hwnd,item):',
                      'fxfile::shellclipboard::write(hwnd,item)'):
            self.assertIn(token,body)
        self.assertLess(body.index('ownerPid!=::GetCurrentProcessId()'),
                        body.index('writePathsText(hwnd,item)'))
        self.assertNotIn('EmptyClipboard(',body)

    def test_text_writer_prepares_payload_before_mutation_and_transfers_ownership(self):
        code=(ROOT/'src/base/shell_clipboard_core.cpp').read_text(encoding='utf-8')
        body=code.split('DWORD writePathsText(',1)[1].split('DWORD read(',1)[0]
        for token in ('payload.move||!valid(payload)', 'formatQuotedPaths(',
                      'GlobalAlloc(GMEM_MOVEABLE,bytes)', 'text.size()+1',
                      'SetClipboardData(CF_UNICODETEXT,memory)', 'else memory=nullptr;',
                      'if(memory)::GlobalFree(memory)', 'ERROR_WRITE_FAULT'):
            self.assertIn(token,body)
        self.assertLess(body.index('std::memcpy(dest,text.c_str(),bytes)'),
                        body.index('::OpenClipboard(owner)'))
        self.assertNotIn('CF_HDROP',body)
        self.assertNotIn('DROPEFFECT',body)
        tree=ET.parse(APP/'flyExplorer.project-template.xml')
        self.assertTrue(any(e.get('Include','').replace('\\','/').endswith('/quoted_paths_text.h') for e in tree.iter()))


if __name__=='__main__':
    unittest.main()

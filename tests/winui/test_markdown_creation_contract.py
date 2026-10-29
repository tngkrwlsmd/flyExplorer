"""Markdown creation must use the existing anchored, no-replace file command."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'app'/'winui'


class MarkdownCreationContract(unittest.TestCase):
    def test_toolbar_background_and_name_editor_share_command_kind(self):
        root=ET.parse(APP/'FileToolbar.xaml').getroot()
        menu=next(n for n in root.iter() if n.get('Click')=='OnNewMarkdownFileMenu')
        self.assertEqual(menu.get('Text'),'Markdown 문서 (.md)')
        bar=(APP/'FileToolbar.xaml.cpp').read_text(encoding='utf-8')
        self.assertIn('OnNewMarkdownFileMenu(IInspectable const&,RoutedEventArgs const&){if(action_)action_(21);}',bar)
        self.assertIn('pendingNameAction_==3?20:',bar)
        self.assertIn('(action==1||action==2||action==3)&&!isFolder',bar)
        window=(APP/'MainWindow.xaml.cpp').read_text(encoding='utf-8')
        for command,method in [(20,'ExecuteFileCommand'),(21,'BeginFileNameCommand')]:
            fragment=window.split('else if(command=='+str(command)+')',1)[1].split('else if',1)[0]
            self.assertIn(method+'(',fragment)
            self.assertIn('Kind::CreateMarkdownFile',fragment)
        source=(APP/'m21_commands.cpp').read_text(encoding='utf-8')
        self.assertIn('Kind::CreateMarkdownFile?3:',source)
        self.assertIn('initial=L"새 Markdown 문서.md";',source)
        self.assertIn('validMarkdownDocumentLeaf(request.name)',source)
        self.assertIn('새 Markdown 문서를 만들었습니다.',source)
        self.assertLess(source.index('validMarkdownDocumentLeaf(request.name)'),
                        source.index('mFileOperations.startFileCommand('))
        background=(APP/'m22_transfers.cpp').read_text(encoding='utf-8').split(
            'create.Items().Append(make(L"Markdown 문서 (.md)"',1)[1].split('menu.Items().Append(create)',1)[0]
        self.assertIn('localFolder',background)
        self.assertIn('BeginFileNameCommand(fxfile::filecommand::Kind::CreateMarkdownFile)',background)

    def test_markdown_and_text_suffixes_share_only_the_safe_creation_path(self):
        native=(ROOT/'src/base/file_command_core.cpp').read_text(encoding='utf-8')
        validator=native.split('bool validMarkdownDocumentLeaf(',1)[1].split('Result execute(',1)[0]
        for token in ('validLeaf(name)&&name.size()>3', 'name.size()-3,3,L".md",3,TRUE'):
            self.assertIn(token,validator)
        branch=native.split('if(task.kind==Kind::CreateTextFile||task.kind==Kind::CreateMarkdownFile)',1)[1].split('if(task.kind!=Kind::RenameSelected)',1)[0]
        for token in ('validTextDocumentLeaf(task.name)', 'validMarkdownDocumentLeaf(task.name)',
                      'FILE_ATTRIBUTE_REPARSE_POINT','CREATE_NEW', '::CreateFileW(',
                      'drive!=DRIVE_FIXED&&drive!=DRIVE_REMOVABLE'):
            self.assertIn(token,branch)
        self.assertNotIn('CREATE_ALWAYS',native)
        self.assertNotIn('WriteFile(',branch)
        fixture=(ROOT/'tests/winui/m21/m21_native_fixture.cpp').read_text(encoding='utf-8')
        for marker in ('create_empty_unicode_markdown_document','markdown_never_overwrites_existing',
                       'markdown_case_insensitive_extension','markdown_rejects_unsafe_or_other_suffix_names'):
            self.assertIn(marker,fixture)


if __name__=='__main__':
    unittest.main()

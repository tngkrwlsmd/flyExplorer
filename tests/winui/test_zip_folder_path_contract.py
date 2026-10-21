"""F08 one-root ZIP path containment source contracts. NOT EXECUTED."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def source(p):
    return (R/p).read_text(encoding="utf-8-sig")
class SingleRootZipContracts(unittest.TestCase):
    def test_only_one_root_and_one_leaf(self):
        c=source("src/base/zip_store_batch_extractor.h")
        for token in (
            "value.find(L'/',slash+1)",
            "flatName(root)&&flatName(leaf)",
            "rootMode!=!entryRoot.empty()",
            "archiveRoot,entryRoot",
            "zipinspect::detail::same(previous.name,entryLeaf)",
            "staging.nestedRoot",
            "staging.nestedOwned=true;",
            "if(!nestedOwned)return;",
            "CreateDirectoryW(staging.nestedRoot.c_str(),nullptr)",
            "if(!nestedRoot.empty())::RemoveDirectoryW(nestedRoot.c_str())",
            "!(child&FILE_ATTRIBUTE_DIRECTORY)",
            "(child&FILE_ATTRIBUTE_REPARSE_POINT)",
            "CreateDirectoryW(staging.path.c_str(),nullptr)",
            "MoveFileExW(staging.path.c_str(),target.c_str()",
        ):
            self.assertIn(token,c)
        self.assertLess(c.index("detail::memberPath(name,entryRoot,entryLeaf)"),
                        c.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(c.index("crc32(member.content)!=checksum"),
                        c.index("GetTempFileNameW(parent.c_str()"))
        self.assertNotIn("std::filesystem::remove_all(",c)

    def test_folder_zip_ui_exact_origin_and_cancel(self):
        u=source("app/winui/m22_transfers.cpp")
        h=source("app/winui/MainWindow.xaml.h")
        method=u.split("void MainWindow::CreateSelectedFolderZip(int side)",1)[1].split(
            "void MainWindow::CreateSelectedBatchZip(int side,bool preferDeflate)",1)[0]
        for t in (
            "view.SelectedItems().Size()!=1",
            "!item->isFolder()",
            "createFolder(",
            "mZipBatchCreationBusy=true",
            "mZipBatchCancel=cancel",
            "active.identity!=identity",
            "pane.routeIds[tab]!=route",
            "pane.filesystemPaths[tab]!=folder",
            "NavigationAction::Refresh",
        ):
            self.assertIn(t,method)
        self.assertIn("const bool canCreateFolderZip=",u)
        self.assertIn('make(L"폴더 ZIP으로 묶기 (하위 폴더 1개 이하, 2~8개 파일)"',u)
        self.assertIn("void CreateSelectedFolderZip(int side);",h)
if __name__=="__main__":
    unittest.main()

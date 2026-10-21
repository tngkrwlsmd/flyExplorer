"""F08 bounded one-root/three-child ZIP path containment contracts.
Source-only expectations; NOT EXECUTED in this change.
"""
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[2]
def source(path):
    return (R/path).read_text(encoding="utf-8-sig")

class SingleRootZipContracts(unittest.TestCase):
    def test_bounded_member_path_and_nonrecursive_staging(self):
        c=source("src/base/zip_store_batch_extractor.h")
        checks=(
            "value.find(L'/',second+1)",
            "flatName(root)&&flatName(child)&&flatName(leaf)",
            "rootMode!=!entryRoot.empty()",
            "archiveRoot,entryRoot",
            "archiveChildren.push_back(entryChild)",
            "archiveChildren.size()>=",
            "previous.name,entryChild",
            "previous.child,entryChild",
            "previous.name,entryLeaf",
            "staging.nestedRoot",
            "staging.nestedChildren",
            "staging.nestedOwned=true;",
            "++staging.createdChildren;",
            "if(!nestedOwned){",
            "previous.name,entryChild",
            "archiveChildren.begin(),archiveChildren.end()",
            "for(std::size_t i=0;i<createdChildren;++i)",
            "CreateDirectoryW(staging.nestedRoot.c_str(),nullptr)",
            "CreateDirectoryW(childPath.c_str(),nullptr)",
            "RemoveDirectoryW(nestedChildren[i-1].c_str())",
            "RemoveDirectoryW(nestedRoot.c_str())",
            "MoveFileExW(staging.path.c_str(),target.c_str()",
        )
        for token in checks:
            self.assertIn(token,c)
        self.assertLess(c.index("detail::memberPath("),
                        c.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(c.index("previous.name,entryChild"),
                        c.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(c.index("crc32(member.content)!=checksum"),
                        c.index("GetTempFileNameW(parent.c_str()"))
        self.assertNotIn("std::filesystem::remove_all(",c)

    def test_writer_explicit_single_child_enumeration(self):
        w=source("src/base/zip_store_batch_writer.h")
        checks=(
            "std::vector<std::wstring> allowedChildren",
            "kMaxChildFolders=3",
            "prior.child,child",
            "std::vector<std::wstring> childFolders",
            "childFolders.size()>=kMaxChildFolders",
            "for(auto const& childFolder:childFolders)",
            "FindFirstFileW(searchChild.c_str()",
            "nested.dwFileAttributes&",
            "childCount",
            "member.child=std::move(child)",
            "entryPrefix.push_back('/')",
            "member.name.insert(0,entryPrefix)",
            "rootLeaf.size()+1u+innerUnits+",
            "return createMany(files,cancellation,mode,folder)",
        )
        for token in checks:
            self.assertIn(token,w)
        self.assertLess(w.index("FindFirstFileW(searchChild.c_str()"),
                        w.index("return createMany(files,cancellation,mode,folder)"))

    def test_folder_ui_exact_origin_and_cancel(self):
        ui=source("app/winui/m22_transfers.cpp")
        hdr=source("app/winui/MainWindow.xaml.h")
        method=ui.split("void MainWindow::CreateSelectedFolderZip(int side)",1)[1].split(
            "void MainWindow::CreateSelectedBatchZip(int side,bool preferDeflate)",1)[0]
        for token in (
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
            self.assertIn(token,method)
        self.assertNotIn("const bool canCreateFolderZip=",ui)
        self.assertNotIn('make(L"폴더 ZIP으로 묶기 (하위 폴더 최대 3개, 파일 2~8개)"',ui)
        self.assertIn('make(L"Windows 탐색기에서 선택 열기"',ui)
        self.assertIn("void CreateSelectedFolderZip(int side);",hdr)

if __name__=="__main__":
    unittest.main()

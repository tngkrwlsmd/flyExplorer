"""File visual/detail worker lifecycle ownership after metadata separation."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class FileDetailControllerContract(unittest.TestCase):
    def test_controller_owns_detail_worker_lifecycle_without_xaml(self):
        header=read("app/winui/file_detail_controller.h")
        main_h=read("app/winui/MainWindow.xaml.h")
        main_cpp=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("class FileDetailController final",header)
        self.assertIn("void cancel(int side) noexcept",header)
        self.assertIn("void prepareForClose() noexcept",header)
        self.assertNotIn("Microsoft::UI::Xaml",header)
        self.assertNotIn("DispatcherQueue",header)
        self.assertIn("FileDetailController mFileDetails",main_h)
        self.assertNotIn("mDetailCancel",main_h)
        self.assertNotIn("mDetailCancel",main_cpp)
        self.assertIn("mFileDetails.prepareForClose()",main_cpp)
        self.assertIn("mFileDetails.cancel(side)",main_cpp)

    def test_worker_preserves_bounded_shell_visual_and_cancel_guards(self):
        impl=read("app/winui/file_detail_controller.cpp")
        for token in (
            "extensions.size()<24",
            "recover.size()>=2",
            "thumbnailBudget<4",
            "request.paths.size()>1200",
            "fxfile::filetype::queryVisuals(",
            "fxfile::thumbnail::query(",
            "if(cancelToken->load())return; // prevent stale visual child launch",
            "if(cancelToken->load())return;",
        ):
            self.assertIn(token,impl)
        for removed in ("entry.bytes=","entry.bytesLabel=",
                        "entry.modified=","entry.dateLabel=",
                        "entry.sizeKnown=","entry.dateKnown="):
            self.assertNotIn(removed,impl)

    def test_extensionless_dotfiles_match_sortable_metadata_type_fallback(self):
        from pathlib import PureWindowsPath
        worker=read("app/winui/file_detail_controller.cpp")
        metadata=read("app/winui/file_metadata_controller.cpp")
        self.assertIn("std::filesystem::path(path).extension().native()", metadata)
        # Visual description and the bounded Windows type lookup must use
        # the same filename-only extension rule as sortable metadata.
        self.assertIn(
            "auto ext=std::filesystem::path(path).extension().native();",
            worker.split('std::vector<std::wstring> extensions{L".flyfolder"};', 1)[1]
                  .split("std::unordered_map<std::wstring", 1)[0])
        self.assertIn(
            "auto ext=std::filesystem::path(path).extension().native();",
            worker.split("auto& entry=details[i];", 1)[1])
        self.assertIn("if(!fxfile::filetype::safeExtension(ext))continue;", worker)
        self.assertIn('entry.typeLabel=ext.size()>1&&ext.size()<=17?', worker)
        self.assertIn('ext.substr(1)+L" 파일":L"파일"', worker)
        self.assertIn("if(!ext.empty()){", worker)
        # Python's Windows path model mirrors the intended path cases;
        # real C++/Windows display remains a separate validation gate.
        cases={
            r"C:\owned\.gitignore": "",
            r"C:\owned\.env": "",
            r"C:\owned\.env.local": ".local",
            r"C:\owned\report.txt": ".txt",
            r"C:\owned\archive.tar.gz": ".gz",
            r"C:\owned\trailing.": ".",
            r"C:\parent.with.dot\readme": "",
        }
        for path, suffix in cases.items():
            with self.subTest(path=path):
                self.assertEqual(PureWindowsPath(path).suffix, suffix)

    def test_network_and_removable_details_use_snapshot_hints_and_isolated_thumbnail_path(self):
        header=read("app/winui/file_detail_controller.h")
        worker=read("app/winui/file_detail_controller.cpp")
        main=read("app/winui/MainWindow.xaml.cpp")
        for token in (
            "bool isolatedPathAccess=false",
            "std::vector<std::uint8_t> folderHints{}",
        ):
            self.assertIn(token,header)
        for token in (
            "request.isolatedPathAccess",
            "request.folderHints.size()!=request.paths.size()",
            "folder=request.folderHints[i]!=0",
            "thumbnailSizeEligible=request.isolatedPathAccess||",
        ):
            self.assertIn(token,worker)
        self.assertIn(
            "if(!::GetFileAttributesExW(",worker)
        self.assertIn(
            "if(!path.empty()&&!request.isolatedPathAccess){",worker)
        for token in (
            "shelltransfer::transferDriveRoot(folder,root)",
            "driveType==DRIVE_REMOVABLE||driveType==DRIVE_REMOTE||",
            "mOwnedNetworkDetailForce||mOwnedRemovableDetailForce",
            "request.isolatedPathAccess=isolatedPathAccess",
            "request.folderHints=std::move(folderHints)",
            "item.isFolder()?1u:0u",
        ):
            self.assertIn(token,main)

    def test_virtual_shell_provider_visuals_use_isolated_parsing_name_path(self):
        header=read("app/winui/file_detail_controller.h")
        worker=read("app/winui/file_detail_controller.cpp")
        main=read("app/winui/MainWindow.xaml.cpp")
        assoc=read("src/base/shell_assoc_type_core.cpp")
        helper=read("app/winui/helper/FlyShellIsolationHelper.cpp")
        wire=read("src/base/shell_visual_wire.h")
        for token in (
            "bool shellProviderRoot=false",
            "std::vector<std::wstring> shellParsingNames{}",
        ):
            self.assertIn(token,header)
        for token in (
            "queryShellItemVisuals(",
            "request.shellParsingNames",
            "shellThumbnailHints",
            "wantsShellThumbnail?request.thumbnailPixels:0u",
            "shellVisual.thumbnailBgra",
            "!folder&&!path.empty()&&!request.shellProviderRoot",
        ):
            self.assertIn(token,worker)
        for token in (
            "folder.empty()&&snapshot.folder.valid()",
            "shellParsingNames.push_back(shellProviderRoot?",
            "request.shellProviderRoot=shellProviderRoot",
            "request.shellParsingNames=std::move(shellParsingNames)",
        ):
            self.assertIn(token,main)
        for token in (
            "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "JOB_OBJECT_LIMIT_ACTIVE_PROCESS",
            'L"FlyShellIsolationHelper.exe"',
            '" --shell-item-visuals"',
            "TerminateJobObject",
        ):
            self.assertIn(token,assoc)
        for token in (
            'L"--shell-item-visuals"',
            "SHParseDisplayName(",
            "SHGFI_PIDL|SHGFI_TYPENAME|SHGFI_ICON",
        ):
            self.assertIn(token,helper)
        for token in (
            "kMaxItems=1200",
            "kMaxNameUnits=4096",
            "kMaxBodyBytes=8u*1024u*1024u",
            "kMaxLabelUnits=80",
            "kMaxThumbnailItems=4",
            "kWantThumbnail=1u",
        ):
            self.assertIn(token,wire)
        self.assertNotIn("IShellItemImageFactory",assoc)

    def test_mainwindow_keeps_live_state_acceptance_and_project_compiles_owner(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        project=read("app/winui/flyExplorer.project-template.xml")
        self.assertIn("mFileDetails.start(",main)
        self.assertIn("ActiveWindowTab().fileLists[side].accepts(",main)
        self.assertIn("pane.routeIds[tab]!=route",main)
        self.assertIn("pane.tabs[tab].snapshot().children.size()!=count",main)
        self.assertIn('<ClInclude Include="file_detail_controller.h" />',project)
        self.assertIn('<ClCompile Include="file_detail_controller.cpp">',project)

    def test_file_list_cache_has_one_current_owner_per_window_tab(self):
        state=read("app/winui/file_list_state.h")
        owner=read("app/winui/window_tab_state.h")
        main=read("app/winui/MainWindow.xaml.cpp")
        for token in ("sortMode","metadata","details","renderedLogical","renderedPaths",
                      "indexedNameProjection","epoch","invalidate()","isCurrent(","accepts("):
            self.assertIn(token,state)
        self.assertIn("std::array<fxfile::previewlist::PaneState,2> fileLists",owner)
        self.assertIn("listState.begin(route,tab)",main)
        self.assertIn("listState.isCurrent(",main)

if __name__=="__main__":
    unittest.main()

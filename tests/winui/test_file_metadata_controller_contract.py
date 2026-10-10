"""Sortable metadata is independent from Shell visual/detail work."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class FileMetadataControllerContract(unittest.TestCase):
    def test_metadata_controller_owns_bounded_worker_lifecycle(self):
        header=read("app/winui/file_metadata_controller.h")
        impl=read("app/winui/file_metadata_controller.cpp")
        main_h=read("app/winui/MainWindow.xaml.h")
        for token in (
            "class FileMetadataController final",
            "void cancel(int side) noexcept",
            "void prepareForClose() noexcept",
            "std::vector<fxfile::previewlist::FileMetadata> metadata",
        ):
            self.assertIn(token,header)
        self.assertNotIn("Microsoft::UI::Xaml",header)
        self.assertNotIn("DispatcherQueue",header)
        self.assertIn("kMaxCompleteModelEntries",impl)
        self.assertIn("GetFileAttributesExW",impl)
        self.assertIn("entry.typeKey=typeKey",impl)
        self.assertIn("entry.sizeKnown=true",impl)
        self.assertIn("entry.modified=modified",impl)
        self.assertIn("entry.dateKnown=modified!=0",impl)
        self.assertNotIn('GetDateFormatEx(L"ko-KR"',impl)
        self.assertNotIn('GetTimeFormatEx(L"ko-KR"',impl)
        self.assertNotIn("queryVisuals(",impl)
        self.assertNotIn("thumbnail::query(",impl)
        self.assertIn("FileMetadataController mFileMetadata",main_h)

    def test_indexed_local_metadata_budget_fails_closed(self):
        header=read("app/winui/file_metadata_controller.h")
        cpp=read("app/winui/file_metadata_controller.cpp")
        for token in (
            "kMaxIndexedMetadataEntries=25000",
            "kMaxIndexedMetadataPathUnits=12*1024*1024",
            "requireCompleteIndex=false",
        ):
            self.assertIn(token,header)
        self.assertIn("request.isolatedNetwork&&request.requireCompleteIndex",cpp)
        self.assertIn("path.size()>kMaxIndexedMetadataPathUnits-units",cpp)
        self.assertIn("if(requireCompleteIndex)return ERROR_INVALID_DATA;",cpp)
        self.assertIn("if(requireCompleteIndex&&!metadata[i].dateKnown)",cpp)

    def test_metadata_and_visual_cache_identity_are_separate(self):
        state=read("app/winui/file_list_state.h")
        for token in (
            "struct FileMetadata final",
            "std::wstring typeKey",
            "std::vector<FileMetadata> metadata",
            "beginMetadata(",
            "metadataCurrent(",
            "acceptsMetadata(",
            "invalidateMetadata()",
            "invalidateDetails()",
        ):
            self.assertIn(token,state)
        detail=state[state.index("struct FileDetail final"):
                     state.index("struct PaneState final")]
        self.assertNotIn("bytesLabel",detail)
        self.assertNotIn("dateLabel",detail)
        self.assertNotIn("sizeKnown",detail)
        self.assertNotIn("dateKnown",detail)

    def test_metadata_sort_never_silently_falls_back_to_name_order(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        transfers=read("app/winui/m22_transfers.cpp")
        for token in (
            "ScheduleFileMetadata(int side,bool force)",
            "mFileMetadata.start(",
            "residentMetadataReady=state.metadataCurrent(",
            "indexedMetadataReady=",
            "if(mode<=1||metadataReady)",
            "state.metadata[lhs].typeKey",
            "state.metadata[lhs]",
            "state.metadata[rhs]",
            "ScheduleFileMetadata(completed.side)",
            "snapshot.residentEndOffset()!=snapshot.nextOffset",
        ):
            self.assertIn(token,main)
        self.assertIn("if(state.indexedMetadataSort){",transfers)
        self.assertIn("pane.routeIds[pane.active],pane.active,session.nameIndex().size()",transfers)
        self.assertIn("전체 메타데이터 인덱스로 정렬했습니다.",transfers)
        self.assertIn("if(selection>1)",transfers)
        self.assertIn("ScheduleFileMetadata(side)",transfers)
        self.assertIn("정렬을 위해 파일 메타데이터를 준비하는 중입니다.",transfers)
        self.assertIn("정렬을 위해 전체 폴더 항목을 불러오는 중입니다.",transfers)
        self.assertIn("beyondComplete&&selection>1",transfers)

    def test_sortable_metadata_and_visual_detail_have_separate_network_isolation(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        helper_start=main.index("bool SupportsSortableMetadataDrive")
        helper_end=main.index("std::filesystem::path StartFolder",helper_start)
        helper=main[helper_start:helper_end]
        metadata_start=main.index("void MainWindow::ScheduleFileMetadata")
        detail_start=main.index("void MainWindow::ScheduleFileDetails",metadata_start)
        metadata=main[metadata_start:detail_start]
        detail_end=main.index("void MainWindow::",detail_start+10)
        details=main[detail_start:detail_end]
        self.assertIn("driveType==DRIVE_FIXED||driveType==DRIVE_REMOVABLE||",helper)
        self.assertIn("driveType==DRIVE_REMOTE",helper)
        self.assertIn("shelltransfer::transferDriveRoot(folder,root)",metadata)
        self.assertIn("request.isolatedNetwork=isolatedNetwork",metadata)
        self.assertIn("driveType==DRIVE_REMOTE||mOwnedMetadataForceIsolated",metadata)
        # Visual type/icon/thumbnail work has its own 1,200-item lifecycle
        # and isolated removable/network path; it does not reuse metadata results.
        self.assertIn(
            "driveType==DRIVE_REMOVABLE||driveType==DRIVE_REMOTE||",details)
        self.assertIn(
            "mOwnedNetworkDetailForce||mOwnedRemovableDetailForce",details)
        self.assertIn("request.isolatedPathAccess=isolatedPathAccess",details)
        self.assertIn("request.folderHints=std::move(folderHints)",details)

    def test_network_metadata_uses_exact_owned_bounded_helper(self):
        header=read("app/winui/file_metadata_controller.h")
        impl=read("app/winui/file_metadata_controller.cpp")
        helper=read("app/winui/helper/FlyShellIsolationHelper.cpp")
        wire=read("src/base/file_metadata_wire.h")
        for token in (
            "bool isolatedNetwork=false",
            "collectNetworkMetadata(",
            "FlyShellIsolationHelper.exe",
            "--file-metadata",
            "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "JOB_OBJECT_LIMIT_ACTIVE_PROCESS",
            "kNetworkMetadataInactivityMs=5000",
            "kNetworkMetadataCancelGraceMs=1200",
            "CreateEventW",
            "TerminateJobObject",
            "metadatawire::Record",
            "kMaxPathUnits=1024*1024",
        ):
            self.assertIn(token,header+impl+helper+wire)
        self.assertIn("GetFileAttributesExW",helper)
        self.assertIn("FILE_ATTRIBUTE_REPARSE_POINT",helper)
        self.assertIn(
            "request.count>fxfile::metadatawire::kMaxItems",helper)
        self.assertIn(
            "request.bodyBytes>fxfile::metadatawire::kMaxBodyBytes",helper)
        self.assertIn(
            "fxfile::metadatawire::checksum(body.data(),body.size())",helper)

    def test_owned_vm_sort_hook_is_double_gated_and_bounded(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        header=read("app/winui/MainWindow.xaml.h")
        for token in (
            "FLY_METADATA_SORT_OWNED_TEST",
            "FLY_METADATA_SORT_FORCE_ISOLATED_TEST",
            "mOwnedMetadataForceIsolated",
            "--metadata-sort-owned-mode",
            "mode==2||mode==3||mode==4",
            "RunOwnedMetadataSortTestIfReady()",
            "UpdateSort(mOwnedMetadataSortMode)",
            "mOwnedMetadataSortConsumed=true",
        ):
            self.assertIn(token,main)
        self.assertIn("int mOwnedMetadataSortMode=-1",header)
        self.assertIn("bool mOwnedMetadataSortConsumed=false",header)
        self.assertIn("bool mOwnedMetadataForceIsolated=false",header)

    def test_project_compiles_metadata_owner(self):
        project=read("app/winui/flyExplorer.project-template.xml")
        self.assertIn('<ClInclude Include="file_metadata_controller.h" />',project)
        self.assertIn('<ClCompile Include="file_metadata_controller.cpp">',project)
        self.assertIn('file_metadata_wire.h',project)

if __name__=="__main__":
    unittest.main()

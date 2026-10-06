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
        self.assertIn("entry.dateKnown=entry.modified!=0",impl)
        self.assertNotIn('GetDateFormatEx(L"ko-KR"',impl)
        self.assertNotIn('GetTimeFormatEx(L"ko-KR"',impl)
        self.assertNotIn("queryVisuals(",impl)
        self.assertNotIn("thumbnail::query(",impl)
        self.assertIn("FileMetadataController mFileMetadata",main_h)

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
            "metadataReady=state.metadataCurrent(",
            "if(mode<=1||metadataReady)",
            "state.metadata[lhs].typeKey",
            "state.metadata[lhs]",
            "state.metadata[rhs]",
            "ScheduleFileMetadata(completed.side)",
            "snapshot.residentEndOffset()!=snapshot.nextOffset",
        ):
            self.assertIn(token,main)
        self.assertIn("if(selection>1)",transfers)
        self.assertIn("ScheduleFileMetadata(side)",transfers)
        self.assertIn("정렬을 위해 파일 메타데이터를 준비하는 중입니다.",transfers)
        self.assertIn("정렬을 위해 전체 폴더 항목을 불러오는 중입니다.",transfers)
        self.assertIn("beyondComplete&&selection>1",transfers)

    def test_owned_vm_sort_hook_is_double_gated_and_bounded(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        header=read("app/winui/MainWindow.xaml.h")
        for token in (
            "FLY_METADATA_SORT_OWNED_TEST",
            "--metadata-sort-owned-mode",
            "mode==2||mode==3||mode==4",
            "RunOwnedMetadataSortTestIfReady()",
            "UpdateSort(mOwnedMetadataSortMode)",
            "mOwnedMetadataSortConsumed=true",
        ):
            self.assertIn(token,main)
        self.assertIn("int mOwnedMetadataSortMode=-1",header)
        self.assertIn("bool mOwnedMetadataSortConsumed=false",header)

    def test_project_compiles_metadata_owner(self):
        project=read("app/winui/flyExplorer.project-template.xml")
        self.assertIn('<ClInclude Include="file_metadata_controller.h" />',project)
        self.assertIn('<ClCompile Include="file_metadata_controller.cpp">',project)

if __name__=="__main__":
    unittest.main()

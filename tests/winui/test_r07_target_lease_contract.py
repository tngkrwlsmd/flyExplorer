"""R07-4 no-write/no-delete target lease remains non-authorizing and scoped."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class R07TargetLeaseContract(unittest.TestCase):
    def test_lease_is_noncopyable_and_unconnected_to_user_undo(self):
        header = source("src/base/file_command_core.h")
        for part in (
            "class RenameTargetLease final",
            "RenameTargetLease(RenameTargetLease const&) = delete",
            "RenameTargetLease& operator=(RenameTargetLease const&) = delete",
            "~RenameTargetLease() noexcept",
            "RenameRestoreObservation begin(",
            "RenameRestoreObservation recheck() const noexcept",
            "void reset() noexcept",
            "HANDLE handle_=INVALID_HANDLE_VALUE",
            "HANDLE parentHandle_=INVALID_HANDLE_VALUE",
            "FILE_ID_INFO parentId_{}",
        ):
            self.assertIn(part, header)
        app = source("app/winui/file_operation_controller.cpp")
        self.assertNotIn("RenameTargetLease", app)
        self.assertNotIn("UndoFile(", app)
        ui = source("app/winui/m22_transfers.cpp")
        self.assertNotIn("RenameTargetLease", ui)
        self.assertNotIn("UndoFile(", ui)

    def test_handle_is_read_only_and_blocks_new_writers_or_deletes(self):
        body = source("src/base/file_command_core.cpp").split(
            "RenameTargetLease::~RenameTargetLease()", 1)[1].split(
            "\nbool validLeaf(", 1
        )[0]
        for part in (
            "RenameTargetLease::reset() noexcept",
            "::CloseHandle(handle_)",
            "::CloseHandle(parentHandle_)",
            "readDirectoryId(parentHandle_,parentId_)",
            "FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT",
            "sameDirectoryId(parentId_,lockedParent)",
            "sameDirectoryId(parentId_,visibleParent)",
            "RenameTargetLease::begin(",
            "reset();",
            "inspectRenameRestore(originalPath,renamed)",
            "FILE_READ_DATA|FILE_READ_ATTRIBUTES",
            "FILE_SHARE_READ,nullptr,OPEN_EXISTING",
            "FILE_FLAG_OPEN_REPARSE_POINT",
            "RenameTargetLease::recheck() const noexcept",
            "GetFileInformationByHandleEx(",
            "lockedId.VolumeSerialNumber!=expected_.volumeSerial",
            "std::equal(expected_.fileId.begin(),expected_.fileId.end()",
            "readRenameEvidence(target,visible)",
            "sameRenameEvidence(expected_,visible)",
            "::GetFileAttributesW(original.c_str())",
            "::GetLastError()!=ERROR_FILE_NOT_FOUND",
            "RenameRestoreObservation::OriginalOccupiedOrUnknown",
            "RenameRestoreObservation::MatchingSnapshotOnly",
        ):
            with self.subTest(part=part):
                self.assertIn(part, body)
        for forbidden in (
            "SetFileInformationByHandle(", "MoveFileW(", "MoveFileExW(",
            "DeleteFileW(", "RemoveDirectoryW(", "ReplaceFileW(",
            "GENERIC_WRITE", "FILE_WRITE_DATA", "CREATE_NEW",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body)

    def test_held_file_metadata_is_rechecked_before_path(self):
        body = source("src/base/file_command_core.cpp").split(
            "RenameRestoreObservation RenameTargetLease::recheck() const noexcept", 1
        )[1].split("\nbool validLeaf(", 1)[0]
        for token in (
            "FileAttributeTagInfo,&lockedTag",
            "FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT",
            "FileIdInfo,&lockedId",
            "lockedId.VolumeSerialNumber!=expected_.volumeSerial",
            "FileStandardInfo,&lockedStandard",
            "lockedStandard.Directory||lockedStandard.DeletePending",
            "lockedStandard.NumberOfLinks!=1",
            "lockedStandard.EndOfFile.QuadPart<0",
            "expected_.fileSize",
            "FileBasicInfo,&lockedBasic",
            "lockedBasic.LastWriteTime.QuadPart!=expected_.lastWriteTime",
            "return RenameRestoreObservation::TargetChangedOrUnavailable;",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)
        self.assertLess(body.index("FileStandardInfo,&lockedStandard"),
                        body.index("readRenameEvidence(target,visible)"))
        self.assertLess(body.index("FileBasicInfo,&lockedBasic"),
                        body.index("readRenameEvidence(target,visible)"))

    def test_original_name_not_reserved_and_lease_recheck_requires_identity(self):
        body = source("src/base/file_command_core.cpp").split(
            "RenameRestoreObservation RenameTargetLease::recheck() const noexcept", 1
        )[1].split("\nbool validLeaf(", 1)[0]
        positions = (
            "GetFileInformationByHandleEx(",
            "readRenameEvidence(target,visible)",
            "GetFileAttributesW(original.c_str())",
            "RenameRestoreObservation::MatchingSnapshotOnly",
        )
        for earlier, later in zip(positions, positions[1:]):
            self.assertLess(body.index(earlier), body.index(later))
        self.assertIn("if(comparison!=CSTR_LESS_THAN&&comparison!=CSTR_GREATER_THAN)", body)
        self.assertIn("return RenameRestoreObservation::UnsafePaths;", body)

    def test_owned_contention_fixture_and_policy_no_undo(self):
        native = source("tests/winui/m21/m21_native_fixture.cpp")
        for marker in (
            "r07_guard_acquires_and_rechecks_exact_identity",
            "r07_guard_denies_competing_writer_without_change",
            "r07_guard_denies_competing_delete_without_change",
            "r07_guard_rechecks_reoccupied_original_without_restoring",
            "r07_guard_denies_prior_writer_and_releases_cleanly",
            "r07_guard_parent_delete_access_not_assumed_blocked",
            "r07_guard_reset_releases_parent_directory_handle",
            "r07_guard_preexisting_parent_delete_is_not_authority",
            "ERROR_SHARING_VIOLATION",
            "FILE_WRITE_DATA",
            "DELETE,",
            "guard.reset();",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, native)
        self.assertIn("Directory DELETE access is not reliably excluded", native)
        self.assertIn("Neither outcome is permission to restore", native)
        wrapper = source("tests/winui/m21/test_native.py")
        self.assertIn("M21_NATIVE_SUMMARY 77 passed, 0 failed.", wrapper)
        policy = " ".join(
            source("docs/development/R07_UNDO_RECEIPT_POLICY_20261103.md").split()
        )
        for phrase in (
            "R07-4", "FILE_SHARE_READ", "원래 이름", "미구현",
            "핸들", "실제 Undo",
        ):
            self.assertIn(phrase, policy)


if __name__ == "__main__":
    unittest.main()

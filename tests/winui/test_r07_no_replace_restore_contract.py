"""R07-8 native no-replace restore is unwired and must fail closed.

These are source-level contract tests, NOT native execution or file recovery.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class R07NoReplaceRestoreContract(unittest.TestCase):
    def setUp(self):
        self.header = source("src/base/file_command_core.h")
        self.core = source("src/base/file_command_core.cpp")
        self.restore = self.core.split(
            "RenameRestoreWriteResult restoreRenameNoReplace(", 1
        )[1]

    def test_explicit_native_outcome_and_no_ui_or_history_wiring(self):
        for text in (
            "enum class RenameRestoreWriteStatus",
            "RejectedReceipt",
            "RejectedPaths",
            "OriginalOccupiedOrUnknown",
            "TargetChangedOrUnavailable",
            "AccessUnavailable",
            "NativeCallFailedUnknownState",
            "CommittedUnverified",
            "CommittedVerified",
            "bool nativeCallAttempted=false",
            "RenameRestoreWriteResult restoreRenameNoReplace(",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.header)
        for path in (
            "app/winui/file_operation_controller.h",
            "app/winui/file_operation_controller.cpp",
            "app/winui/m22_transfers.cpp",
            "app/winui/MainWindow.xaml.h",
        ):
            self.assertNotIn("restoreRenameNoReplace(", source(path))

    def test_identity_and_delete_access_precede_single_native_mutation(self):
        body = self.restore
        for text in (
            "inspectRenameRestore(originalPath,renamed)",
            "RenameRestoreObservation::MatchingSnapshotOnly",
            "safeRenameEvidenceParent(original)",
            "safeRenameEvidenceParent(target)",
            "FILE_READ_ATTRIBUTES|FILE_TRAVERSE",
            "FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT",
            "readDirectoryId(parent.h,retainedParent)",
            "target.c_str(),DELETE|FILE_READ_DATA|FILE_READ_ATTRIBUTES",
            "FILE_SHARE_READ,nullptr,OPEN_EXISTING",
            "FILE_FLAG_OPEN_REPARSE_POINT",
            "FileAttributeTagInfo,&tag",
            "FileIdInfo,&id",
            "FileStandardInfo,&standard",
            "standard.NumberOfLinks==1",
            "FileBasicInfo,&basic",
            "basic.LastWriteTime.QuadPart==renamed.renameEvidence.lastWriteTime",
            "readRenameEvidence(target,visible)",
            "sameRenameEvidence(renamed.renameEvidence,visible)",
            "sameDirectoryId(retainedParent,visible)",
        ):
            with self.subTest(text=text):
                self.assertIn(text, body)
        self.assertLess(body.index("inspectRenameRestore(originalPath,renamed)"),
                        body.index("target.c_str(),DELETE|FILE_READ_DATA"))
        self.assertLess(body.index("readRenameEvidence(target,visible)"),
                        body.index("::SetFileInformationByHandle("))

    def test_atomic_collision_refusal_uses_held_parent_and_never_overwrites(self):
        body = self.restore
        for text in (
            "validLeaf(leaf)",
            "parentPath!=target.parent_path()",
            "::GetFileAttributesW(original.c_str())",
            "originalError!=ERROR_FILE_NOT_FOUND",
            "info->ReplaceIfExists=FALSE;",
            "info->RootDirectory=parent.h;",
            "info->FileNameLength=nameBytes;",
            "std::memcpy(info->FileName,leaf.data(),nameBytes);",
            "item.h,FileRenameInfo,info",
        ):
            with self.subTest(text=text):
                self.assertIn(text, body)
        self.assertEqual(1, body.count("::SetFileInformationByHandle("))
        self.assertLess(body.index("originalError!=ERROR_FILE_NOT_FOUND"),
                        body.index("::SetFileInformationByHandle("))
        for text in (
            "MOVEFILE_REPLACE_EXISTING",
            "FILE_RENAME_FLAG_REPLACE_IF_EXISTS",
            "::MoveFileW(", "::MoveFileExW(",
            "::DeleteFileW(", "::RemoveDirectoryW(", "::ReplaceFileW(",
            "CREATE_ALWAYS",
        ):
            # The code can mention disallowed flag names only as comments.
            clean = "\n".join(
                line for line in body.splitlines()
                if not line.lstrip().startswith("//")
            )
            self.assertNotIn(text, clean)

    def test_committed_unverified_never_misreported_as_noop(self):
        body = self.restore
        for text in (
            "outcome.nativeCallAttempted=true;",
            "RenameRestoreWriteStatus::NativeCallFailedUnknownState",
            "nativeSucceeded=true;",
            "RenameRestoreWriteStatus::CommittedUnverified",
            "RenameRestoreWriteStatus::CommittedVerified",
            "readRenameEvidence(original,restored)",
            "sameRenameEvidence(renamed.renameEvidence,restored)",
            "oldTargetAttrs==INVALID_FILE_ATTRIBUTES",
            "oldTargetError==ERROR_FILE_NOT_FOUND",
            "return outcome;",
            "catch(...)",
        ):
            with self.subTest(text=text):
                self.assertIn(text, body)
        self.assertLess(body.index("outcome.nativeCallAttempted=true;"),
                        body.index("nativeSucceeded=true;"))
        self.assertLess(body.index("nativeSucceeded=true;"),
                        body.index("RenameRestoreWriteStatus::CommittedVerified"))
        # A post-commit observation failure must never trigger rollback.
        self.assertNotIn("::MoveFileW(", body)
        self.assertNotIn("::DeleteFileW(", body)

    def test_r07_read_only_lease_is_still_separate_from_restore_writer(self):
        lease = self.core.split("RenameTargetLease::~RenameTargetLease()", 1)[1].split(
            "\nbool validLeaf(", 1
        )[0]
        for token in (
            "FILE_READ_DATA|FILE_READ_ATTRIBUTES",
            "FILE_SHARE_READ,nullptr,OPEN_EXISTING",
            "readDirectoryId(parentHandle_,parentId_)",
        ):
            self.assertIn(token, lease)
        self.assertNotIn("DELETE|FILE_READ_DATA", lease)
        self.assertNotIn("::SetFileInformationByHandle(", lease)


if __name__ == "__main__":
    unittest.main()

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
                        body.index("status=native(item.h,&io,info,"))

    def test_atomic_same_parent_collision_refusal_without_absolute_path(self):
        body = self.restore
        for text in (
            "validLeaf(leaf)",
            "parentPath!=target.parent_path()",
            "::GetFileAttributesW(original.c_str())",
            "originalError!=ERROR_FILE_NOT_FOUND",
            "info->ReplaceIfExists=FALSE;",
            "info->Flags=0;",
            "info->RootDirectory=parent.h;",
            "info->FileNameLength=nameBytes;",
            "std::memcpy(info->FileName,leaf.data(),nameBytes);",
            "status=native(item.h,&io,info,",
            "static_cast<ULONG>(required),10u",
            '::GetProcAddress(ntdll,"NtSetInformationFile")',
        ):
            with self.subTest(text=text):
                self.assertIn(text, body)
        self.assertEqual(1, body.count("status=native(item.h,&io,info,"))
        self.assertLess(body.index("originalError!=ERROR_FILE_NOT_FOUND"),
                        body.index("status=native(item.h,&io,info,"))
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

    def test_null_root_is_forbidden_and_held_parent_identity_is_rechecked(self):
        body = self.restore
        for token in (
            "const std::wstring leaf=original.filename().native();",
            "validLeaf(leaf)",
            "parentPath!=target.parent_path()",
            "readDirectoryId(parent.h,retainedParent)",
            "sameDirectoryId(retainedParent,visible)",
            "parentStillVisible()",
            "info->RootDirectory=parent.h;",
            "info->Flags=0;",
            "info->FileNameLength=nameBytes;",
            "std::memcpy(info->FileName,leaf.data(),nameBytes);",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)
        # A NULL root with a bare leaf was observed redirecting the owned
        # file into the process working directory (Windows VM R07-10).
        self.assertNotIn("info->RootDirectory=nullptr;", body)
        self.assertNotIn("std::memcpy(info->FileName,original", body)
        self.assertNotIn("std::memcpy(info->FileName,target", body)
        self.assertLess(body.index("parentStillVisible()"),
                        body.index("status=native(item.h,&io,info,"))
        self.assertLess(body.index("parentStillVisible()", body.index("nativeSucceeded=true;")),
                        body.index("RenameRestoreWriteStatus::CommittedVerified"))

    def test_native_parent_anchored_call_has_no_win32_fallback(self):
        body=self.restore
        for token in (
            '"NtSetInformationFile"',
            '"RtlNtStatusToDosError"',
            "NativeIoStatusBlock io{};",
            "static_assert(sizeof(NativeIoStatusBlock)==sizeof(void*)*2)",
            "static_assert(offsetof(FILE_RENAME_INFO,RootDirectory)==8)",
            "static_assert(offsetof(FILE_RENAME_INFO,FileName)==20)",
            "std::vector<std::uint64_t> storage(",
            "info->ReplaceIfExists=FALSE;",
            "info->RootDirectory=parent.h;",
            "status=native(item.h,&io,info,",
            "static_cast<ULONG>(required),10u",
            "status!=0||io.Status!=0",
        ):
            with self.subTest(token=token):
                self.assertIn(token,body)
        self.assertEqual(1,body.count("status=native(item.h,&io,info,"))
        self.assertNotIn("::SetFileInformationByHandle(",body)
        self.assertNotIn("::MoveFileExW(",body)
        self.assertNotIn("info->RootDirectory=nullptr;",body)

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


    def test_owned_windows_fixture_checks_rejectors_and_file_identity(self):
        fixture = source("tests/winui/m21/m21_native_fixture.cpp")
        wrapper = source("tests/winui/m21/test_native.py")
        markers = (
            "r07_restore_owned_verified_rename_receipt",
            "r07_restore_rejects_unverified_receipt_without_mutation",
            "r07_restore_rejects_forged_file_id_without_mutation",
            "r07_restore_rejects_missing_target_without_mutation",
            "r07_restore_rejects_original_collision_preserves_bytes",
            "r07_restore_rejects_preexisting_writer_without_mutation",
            "r07_restore_owned_no_replace_commits_exact_file",
            "r07_restore_replay_rejected_and_original_preserved",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, fixture)
        self.assertIn("readId(restoreTarget,restoredBefore)", fixture)
        self.assertIn("readId(restoreOriginal,restoredAfter)", fixture)
        self.assertIn("std::memcmp(restoredBefore.FileId.Identifier,", fixture)
        self.assertIn("restoredBytes==ownedBytes", fixture)
        self.assertIn("retainedCollision==occupiedBytes", fixture)
        self.assertIn("rejectedWriter.status==WriteStatus::AccessUnavailable", fixture)
        self.assertIn("!rejectedWriter.nativeCallAttempted", fixture)
        self.assertIn("restored.status==WriteStatus::CommittedVerified", fixture)
        self.assertIn('M21_NATIVE_SUMMARY 79 passed, 0 failed.', wrapper)
        self.assertIn('M21_NATIVE_"+CFG+"_79_PASS', wrapper)
        self.assertIn("m21-native-owned-", wrapper)

    def test_fixture_only_mutates_its_generated_owned_directory(self):
        fixture = source("tests/winui/m21/m21_native_fixture.cpp")
        body = fixture.split(" // R07-8: exercise the isolated restore primitive ONLY", 1)[1].split(
            " req.kind=filecommand::Kind::CreateTextFile;", 1
        )[0]
        self.assertIn('const auto restoreOriginal=dir/L"r07-', body)
        self.assertIn('const auto restoreTarget=dir/L"r07-', body)
        self.assertIn("restoreReq.parent=dir.native();", body)
        self.assertIn("restoreReq.source=restoreOriginal.native();", body)
        self.assertIn("std::filesystem::remove(restoreOriginal); // fixture-owned collision only", body)
        self.assertNotIn("std::filesystem::remove_all(", body)
        self.assertNotIn("DeleteFileW(", body)
        self.assertNotIn("FILE_RENAME_FLAG_REPLACE_IF_EXISTS", body)
        self.assertNotIn("MOVEFILE_REPLACE_EXISTING", body)


    def test_parent_relocation_fixture_is_disposable_and_not_ui_wired(self):
        fixture = source("tests/winui/m21/m21_native_fixture.cpp")
        section = fixture.split(" // R07-13: simulate an external parent relocation", 1)[1].split(
            " // R07-11 independent native-ABI diagnostic.", 1
        )[0]
        for token in (
            'const auto priorParent=dir/L"r07-parent-origin";',
            'const auto movedParent=dir/L"r07-parent-relocated";',
            "std::filesystem::rename(priorParent,movedParent,moveError);",
            "if(moved)missingParent=filecommand::restoreRenameNoReplace(",
            "if(rebound)reboundResult=filecommand::restoreRenameNoReplace(",
            "missingParent.status==WriteStatus::RejectedPaths",
            "reboundResult.status==WriteStatus::TargetChangedOrUnavailable",
            "!missingParent.nativeCallAttempted",
            "!reboundResult.nativeCallAttempted",
            "retained==payload",
            "r07_restore_rejects_moved_parent_before_native_call",
            "r07_restore_rejects_rebound_parent_preserves_original_file",
        ):
            with self.subTest(token=token):
                self.assertIn(token, section)
        self.assertNotIn("std::filesystem::remove_all(", section)
        self.assertNotIn("::DeleteFileW(", section)
        self.assertNotIn("::MoveFileExW(", section)
        self.assertNotIn("restoreRenameNoReplace(", source("app/winui/file_operation_controller.cpp"))


if __name__ == "__main__":
    unittest.main()

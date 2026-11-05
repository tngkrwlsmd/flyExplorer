"""R07-2: read-only rename identity must never turn into Undo authority."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class RenameIdentityContract(unittest.TestCase):
    def test_result_owns_identity_without_changing_command_or_session(self):
        header = read("src/base/file_command_core.h")
        for token in (
            "struct RenameEvidence", "bool verified=false",
            "std::uint64_t volumeSerial=0",
            "std::array<unsigned char,16> fileId{}",
            "std::uint64_t fileSize=0", "std::int64_t lastWriteTime=0",
            "RenameEvidence renameEvidence{}",
        ):
            self.assertIn(token, header)
        controller = read("app/winui/file_operation_controller.cpp")
        self.assertIn("value.result=fxfile::filecommand::execute(request)", controller)
        self.assertIn("value.originalRenameSource=std::move(originalRenameSource)", controller)
        self.assertNotIn("UndoFile(", controller)
        self.assertNotIn("RedoFile(", controller)

    def test_read_only_fixed_drive_non_reparse_128bit_probe(self):
        source = read("src/base/file_command_core.cpp")
        probe = source.split("bool safeRenameEvidenceParent(", 1)[1].split(
            "bool sameRenameEvidence(", 1)[0]
        for token in (
            "file.lexically_normal()!=file",
            "::GetDriveTypeW(root.c_str())!=DRIVE_FIXED",
            "FILE_ATTRIBUTE_REPARSE_POINT",
            "FILE_ATTRIBUTE_DIRECTORY",
            "GetFileAttributesW(current.c_str())",
            "FILE_READ_ATTRIBUTES",
            "FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE",
            "OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT",
            "FileAttributeTagInfo", "FileIdInfo",
            "FileStandardInfo", "FileBasicInfo",
            "standard.NumberOfLinks==1",
            "standard.EndOfFile.QuadPart>=0",
            "::CloseHandle(handle)",
            "identity.FileId.Identifier",
            "evidence.lastWriteTime=basic.LastWriteTime.QuadPart",
        ):
            with self.subTest(token=token):
                self.assertIn(token, probe)
        for forbidden in ("GENERIC_WRITE", "FILE_WRITE_DATA",
                          "CREATE_ALWAYS", "TRUNCATE_EXISTING"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, probe)

    def test_identity_issued_only_after_successful_same_file_rename(self):
        cpp = read("src/base/file_command_core.cpp")
        method = cpp.split("if(task.kind!=Kind::RenameSelected)", 1)[1]
        source_order = (
            "RenameEvidence before{}",
            "safeRenameEvidenceParent(src)",
            "readRenameEvidence(src,before)",
            "::MoveFileW(src.c_str(),target.c_str())",
            "result.error=ERROR_SUCCESS",
            "safeRenameEvidenceParent(target)",
            "readRenameEvidence(target,after)",
            "sameRenameEvidence(before,after)",
            "result.renameEvidence=after",
        )
        for a, b in zip(source_order, source_order[1:]):
            self.assertLess(method.index(a), method.index(b))
        compare = cpp.split("bool sameRenameEvidence(", 1)[1].split(
            "} // namespace", 1)[0]
        for member in (
            "before.verified&&after.verified",
            "before.volumeSerial==after.volumeSerial",
            "before.fileId==after.fileId",
            "before.fileSize==after.fileSize",
            "before.lastWriteTime==after.lastWriteTime",
        ):
            self.assertIn(member, compare)
        self.assertIn("else result.error=::GetLastError();", method)
        self.assertNotIn("MOVEFILE_REPLACE_EXISTING", method)
        self.assertNotIn("MoveFileExW(", method)

    def test_owned_native_checks_cover_positive_and_collision(self):
        native = read("tests/winui/m21/m21_native_fixture.cpp")
        for token in (
            "r07_regular_file_receipt_verified",
            "r07_128bit_file_id_volume_and_size_match",
            "r07_conflict_does_not_issue_receipt_or_overwrite",
            "GetFileInformationByHandleEx(",
            "priorId.VolumeSerialNumber==currentId.VolumeSerialNumber",
            "!failedRename.renameEvidence.verified",
            '!renamedFolder.renameEvidence.verified',
        ):
            self.assertIn(token, native)
        harness = read("tests/winui/m21/test_native.py")
        self.assertIn("M21_NATIVE_SUMMARY 69 passed, 0 failed.", harness)
        self.assertIn("M21_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED", harness)

    def test_undo_or_redo_still_not_exposed(self):
        menu = read("app/winui/m22_transfers.cpp")
        shortcuts = menu.split("void MainWindow::HandleFileShortcut(", 1)[1]
        self.assertNotIn('L"실행 취소"', menu)
        self.assertNotIn("UndoFile(", shortcuts)
        self.assertNotIn("RedoFile(", shortcuts)
        policy = read("docs/development/R07_UNDO_RECEIPT_POLICY_20261103.md")
        for term in ("R07-2", "읽기 전용", "파일 ID", "재분석", "NOT TESTED",
                     "파일 쓰기 허가가 아니다"):
            self.assertIn(term, policy)


if __name__ == "__main__":
    unittest.main()

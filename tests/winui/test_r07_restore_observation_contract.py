"""R07-3 pre-undo read-only observation; NO authority to restore a file."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class R07RestoreObservationContract(unittest.TestCase):
    def test_explicit_non_authorizing_result_enum(self):
        header = read("src/base/file_command_core.h")
        for token in (
            "enum class RenameRestoreObservation",
            "UnverifiedReceipt",
            "UnsafePaths",
            "OriginalOccupiedOrUnknown",
            "TargetChangedOrUnavailable",
            "MatchingSnapshotOnly",
            "RenameRestoreObservation inspectRenameRestore(",
            "std::wstring const& originalPath,Result const& renamed",
        ):
            with self.subTest(token=token):
                self.assertIn(token, header)
        self.assertIn("NOT undo authorization", header)
        self.assertNotIn("undo(", header)

    def test_fail_closed_original_and_target_checks(self):
        code = read("src/base/file_command_core.cpp")
        body = code.split("RenameRestoreObservation inspectRenameRestore(", 1)[1].split(
            "bool validLeaf(", 1)[0]
        for token in (
            "renamed.error!=ERROR_SUCCESS||!renamed.renameEvidence.verified",
            "original.lexically_normal()!=original",
            "target.lexically_normal()!=target",
            "original.parent_path()!=target.parent_path()",
            "!validLeaf(original.filename().native())",
            "!validLeaf(target.filename().native())",
            "::CompareStringOrdinal(original.c_str(),-1,target.c_str(),-1,TRUE)",
            "!safeRenameEvidenceParent(original)",
            "!safeRenameEvidenceParent(target)",
            "::GetFileAttributesW(original.c_str())",
            "::GetLastError()!=ERROR_FILE_NOT_FOUND",
            "RenameRestoreObservation::OriginalOccupiedOrUnknown",
            "readRenameEvidence(target,current)",
            "sameRenameEvidence(renamed.renameEvidence,current)",
            "RenameRestoreObservation::TargetChangedOrUnavailable",
            "RenameRestoreObservation::MatchingSnapshotOnly",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)
        self.assertLess(
            body.index("::GetFileAttributesW(original.c_str())"),
            body.index("readRenameEvidence(target,current)"),
        )
        self.assertLess(
            body.index("readRenameEvidence(target,current)"),
            body.index("RenameRestoreObservation::MatchingSnapshotOnly"),
        )
        for forbidden in (
            "MoveFileW(", "MoveFileExW(", "DeleteFileW(", "CreateDirectoryW(",
            "RemoveDirectoryW(", "SetFileInformationByHandle(",
            "FILE_WRITE_DATA", "GENERIC_WRITE", "REPLACE_EXISTING",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body)

    def test_no_ui_binding_or_restoration_request_was_added(self):
        app = read("app/winui/file_operation_controller.cpp")
        ui = read("app/winui/m21_commands.cpp")
        self.assertNotIn("inspectRenameRestore(", app)
        self.assertNotIn("inspectRenameRestore(", ui)
        for forbidden in ("UndoFile(", "RedoFile("):
            self.assertNotIn(forbidden, app)
            self.assertNotIn(forbidden, ui)

    def test_owned_native_adversarial_observations_present(self):
        native = read("tests/winui/m21/m21_native_fixture.cpp")
        required = (
            "r07_preflight_snapshot_matches_without_restoring",
            "r07_preflight_rejects_unverified_receipt",
            "r07_preflight_rejects_other_parent_and_same_name",
            "r07_preflight_rejects_reoccupied_source_preserves_files",
            "r07_preflight_rejects_changed_file_id",
            "r07_preflight_rejects_missing_target",
            "r07_preflight_rejects_external_content_change",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertIn(name, native)
        wrapper = read("tests/winui/m21/test_native.py")
        self.assertIn("M21_NATIVE_SUMMARY 60 passed, 0 failed.", wrapper)
        self.assertIn("M21_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED", wrapper)

    def test_policy_requires_atomic_protection_before_real_undo(self):
        policy = " ".join(
            read("docs/development/R07_UNDO_RECEIPT_POLICY_20261103.md").split()
        )
        for term in (
            "R07-3", "읽기 전용", "ERROR_FILE_NOT_FOUND",
            "MatchingSnapshotOnly", "열린 핸들 기반 경합 방지",
            "아직 미구현", "Undo", "Redo",
        ):
            with self.subTest(term=term):
                self.assertIn(term, policy)


if __name__ == "__main__":
    unittest.main()

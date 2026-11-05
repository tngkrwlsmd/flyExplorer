"""R07-11: 네이티브 루트 핸들 진단은 테스트 전용 파일에만 한정한다."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8-sig")


class R07NativeParentProbeContract(unittest.TestCase):
    def test_native_class_ten_is_test_only_and_parent_anchored(self):
        fixture = read("tests/winui/m21/m21_native_fixture.cpp")
        body = fixture.split(" // R07-11 independent native-ABI diagnostic.", 1)[1].split(
            " req.kind=filecommand::Kind::CreateTextFile;", 1
        )[0]
        for marker in (
            'const auto probeSource=dir/L"r07-nt-probe-source.txt";',
            'const auto probeDest=dir/L"r07-nt-probe-renamed.txt";',
            '"NtSetInformationFile"',
            "FILE_TRAVERSE|FILE_READ_ATTRIBUTES",
            "FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT",
            "info->ReplaceIfExists=FALSE;",
            "info->RootDirectory=nativeParent;",
            "info->FileNameLength=nameBytes;",
            "static_cast<ULONG>(required),10u",
            "probeBefore.VolumeSerialNumber==probeAfter.VolumeSerialNumber",
            "std::memcmp(probeBefore.FileId.Identifier,",
            "collisionBytes==\"r07-nt-collision\"",
            "nativeCollision!=0",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, body)
        self.assertNotIn("RootDirectory=nullptr", body)
        self.assertNotIn("MOVEFILE_REPLACE_EXISTING", body)
        self.assertNotIn("::MoveFileExW(", body)
        self.assertNotIn("::DeleteFileW(", body)
        self.assertNotIn("std::filesystem::remove_all(", body)

    def test_probe_is_only_diagnostic_and_not_an_acceptance_gate(self):
        fixture = read("tests/winui/m21/m21_native_fixture.cpp")
        wrapper = read("tests/winui/m21/test_native.py")
        probe = fixture.split(" // R07-11 independent native-ABI diagnostic.", 1)[1].split(
            " req.kind=filecommand::Kind::CreateTextFile;", 1
        )[0]
        self.assertIn('std::printf("M21_DIAG_R07_NT ', probe)
        self.assertNotIn('chk(', probe)
        self.assertIn('M21_NATIVE_SUMMARY 79 passed, 0 failed.', wrapper)
        self.assertIn('"M21_DIAG_R07_NT"', wrapper)
        self.assertNotIn("NtSetInformationFile", read("src/base/file_command_core.cpp"))
        self.assertNotIn("NtSetInformationFile", read("app/winui/file_operation_controller.cpp"))


if __name__ == "__main__":
    unittest.main()

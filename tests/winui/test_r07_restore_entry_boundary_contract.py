"""R07-23D 선행 안전 계약: 복원 조합은 테스트 전용 진입점 검증 전까지 사용자에게 노출하지 않는다.

이 검사는 소스 연결 범위만 확인한다. WinUI 런타임·실제 파일 복원을 실행하지 않는다.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "app/winui/MainWindow.xaml.h"
SOURCE = ROOT / "app/winui/m21_commands.cpp"
XAML = ROOT / "app/winui/MainWindow.xaml"
NAME = "StartPendingRenameRestoreForCurrentOwner"


class RestoreEntryBoundaryContract(unittest.TestCase):
    def test_composition_is_private_and_not_a_xaml_event(self):
        header = HEADER.read_text(encoding="utf-8-sig")
        declaration = header.index(NAME + "(")
        self.assertLess(header.rfind("private:", 0, declaration), declaration)
        self.assertNotIn("public:", header[header.rfind("private:", 0, declaration):declaration])
        self.assertNotIn(NAME, XAML.read_text(encoding="utf-8-sig"))

    def test_composition_has_no_user_command_call_site(self):
        source = SOURCE.read_text(encoding="utf-8-sig")
        # The definition plus one call compiled only into the explicit
        # owned-runtime validation binary are permitted. Normal builds and
        # all user command surfaces contain no call site.
        self.assertEqual(len(re.findall(r"\b" + NAME + r"\s*\(", source)), 2)
        call = source.rindex(NAME + "(")
        guard = source.rfind(
            "#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)", 0, call
        )
        end = source.find("#endif", call)
        self.assertGreater(guard, 0)
        self.assertGreater(end, call)
        body = source.split("MainWindow::" + NAME + "(", 1)[1].split(
            "bool MainWindow::RestoreCompletionContextCurrent(", 1
        )[0]
        self.assertIn("mFileOperations.takeRenameRestoreCandidate(liveContext)", body)
        self.assertIn("mFileOperations.startTakenRenameRestoreAsync(", body)
        self.assertLess(
            body.index("takeRenameRestoreCandidate(liveContext)"),
            body.index("startTakenRenameRestoreAsync("),
        )
        self.assertIn("std::move(*taken)", body)
        self.assertNotIn("OnUndo", source)
        self.assertNotIn("OnRedo", source)


if __name__ == "__main__":
    unittest.main()

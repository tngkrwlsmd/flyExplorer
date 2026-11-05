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
NAME = "StartTakenRenameRestoreForCurrentOwner"


class RestoreEntryBoundaryContract(unittest.TestCase):
    def test_composition_is_private_and_not_a_xaml_event(self):
        header = HEADER.read_text(encoding="utf-8-sig")
        declaration = header.index(NAME + "(")
        self.assertLess(header.rfind("private:", 0, declaration), declaration)
        self.assertNotIn("public:", header[header.rfind("private:", 0, declaration):declaration])
        self.assertNotIn(NAME, XAML.read_text(encoding="utf-8-sig"))

    def test_composition_has_no_user_command_call_site(self):
        source = SOURCE.read_text(encoding="utf-8-sig")
        # A declaration and a single method definition are permitted; no
        # call from a toolbar, menu, keyboard or file-command handler.
        self.assertEqual(len(re.findall(r"\b" + NAME + r"\s*\(", source)), 1)
        self.assertIn("mFileOperations.startTakenRenameRestoreAsync(", source)
        self.assertNotIn("OnUndo", source)
        self.assertNotIn("OnRedo", source)


if __name__ == "__main__":
    unittest.main()

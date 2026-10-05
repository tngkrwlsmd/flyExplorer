"""Current Korean localization and resource consistency contracts."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"
XUID = "{http://schemas.microsoft.com/winfx/2006/xaml}Uid"


def text(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class LocalizationContracts(unittest.TestCase):
    def test_primary_shell_controls_keep_korean_defaults(self):
        def values(path):
            root = ET.parse(ROOT / path).getroot()
            return "\n".join(
                value for element in root.iter() for value in element.attrib.values() if value
            )

        header = values("app/winui/ShellHeader.xaml")
        nav = values("app/winui/NavigationSidebar.xaml")
        main = values("app/winui/MainWindow.xaml") + "\n" + values(
            "app/winui/FileToolbar.xaml"
        )
        for word in ("테마: 시스템", "시스템", "라이트", "다크"):
            self.assertIn(word, header)
        for word in ("탐색", "내 PC", "문서"):
            self.assertIn(word, nav)
        for word in ("파일 작업", "새 폴더", "이름 변경"):
            self.assertIn(word, main)

    def test_runtime_theme_and_drag_messages_are_real_korean(self):
        shell = text("app/winui/ShellHeader.xaml.cpp")
        drag = text("app/winui/m23_drag.cpp")
        for word in ("테마: 시스템", "테마: 라이트", "테마: 다크"):
            self.assertIn(word, shell)
        for word in (
            "원본 폴더가 변경됐습니다",
            "최대 32개",
            "파일 놓기 데이터를 읽지 못했습니다",
        ):
            self.assertIn(word, drag)
        self.assertNotIn("??:", shell)
        self.assertNotIn('StatusText().Text(L"?', drag)

    def test_resw_matches_static_xaml_fallbacks(self):
        resources = ET.parse(APP / "Strings/ko-KR/Resources.resw").getroot()
        lookup = {
            entry.get("name"): entry.findtext("value")
            for entry in resources.findall("data")
        }
        found = 0
        for name in ("MainWindow.xaml", "FileToolbar.xaml", "NavigationSidebar.xaml"):
            page = ET.parse(APP / name).getroot()
            for control in page.iter():
                uid = control.get(XUID)
                if not uid:
                    continue
                for attribute in ("Content", "Header", "PlaceholderText"):
                    key = uid + "." + attribute
                    if key in lookup and control.get(attribute) is not None:
                        self.assertEqual(lookup[key], control.get(attribute), key)
                        found += 1
        self.assertGreaterEqual(found, 7)

    def test_project_is_utf8_and_korean_default_language(self):
        project = text("app/winui/flyExplorer.project-template.xml")
        self.assertIn("/bigobj /utf-8", project)
        self.assertEqual(1, project.count("<DefaultLanguage>ko-KR</DefaultLanguage>"))
        self.assertNotIn("<DefaultLanguage>en-US</DefaultLanguage>", project)


if __name__ == "__main__":
    unittest.main()

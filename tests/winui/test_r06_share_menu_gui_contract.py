"""R06 actual WinUI file context menu: focused ownership and evidence contract."""
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "winui"))
from run_checks import r06_share_menu_evidence_ok


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class R06OwnedShareMenuContract(unittest.TestCase):
    def test_owned_context_menu_source_and_shell_entry_parse(self):
        paths = ("tests/winui/test_r06_share_menu_gui.py",
                 "tests/winui/test_shell_gui.py",
                 "tools/winui/run_checks.py")
        for path in paths:
            with self.subTest(path=path):
                ast.parse(read(path), filename=path)
        shell = read(paths[1])
        self.assertIn('if os.environ.get("FLY_R06_SHARE_MENU_ONLY")=="YES":', shell)
        self.assertIn("r06_share_menu(win=win,element=element", shell)
        self.assertIn("owned=owned,owned_pid=p.pid", shell)
        self.assertIn("R06_GUI_FOCUSED_OWNED_MENU_PASS=True", shell)

    def test_exact_selection_menu_and_no_system_share_automation(self):
        script = read("tests/winui/test_r06_share_menu_gui.py")
        for marker in (
            'DIRECT = "Windows 공유 창 열기 (파일 1개)"',
            'FALLBACK = "공유 옵션: Windows 탐색기에서 선택"',
            "source.read_bytes() == original",
            "original_names",
            "foreground_owned()",
            "top.element_info.process_id != owned_pid",
            "peer.element_info.process_id != owned_pid",
            "direct.is_enabled() is direct_enabled",
            "assert fallback.is_enabled()",
            "second.iface_selection_item.AddToSelection()",
            "assert row(source.name).is_selected() and row(folder.name).is_selected()",
            'keyboard.send_keys("{ESC}")',
            "assert_menu(True)", "assert_menu(False)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)
        for forbidden in (
            "ShowShareUI", "DataTransferManager", "DataRequested",
            "SetStorageItems", "ShareSelectedWithWindows",
            "RevealSelectedInWindowsExplorer", ".invoke()", "os.system(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, script)

    def test_real_gui_markers_and_negative_cases(self):
        runner = read("tools/winui/run_checks.py")
        self.assertIn('"share-menu",', runner)
        self.assertIn('if area == "share-menu":', runner)
        self.assertIn('gui_env["FLY_R06_SHARE_MENU_ONLY"] = "YES"', runner)
        self.assertIn('if not rc and area == "share-menu":', runner)
        self.assertIn("if not r06_share_menu_evidence_ok(body):", runner)
        script = read("tests/winui/test_r06_share_menu_gui.py")
        required = (
            "R06_GUI_SINGLE_FILE_DIRECT_AND_FALLBACK_ENABLED=PASS",
            "R06_GUI_FOLDER_DIRECT_DISABLED_FALLBACK_ENABLED=PASS",
            "R06_GUI_MULTI_SELECTION_DIRECT_DISABLED_FALLBACK_ENABLED=PASS",
            "R06_GUI_OWNED_ORIGINALS_PRESERVED_NO_SHARE_ACTION_INVOKED=PASS",
            "R06_GUI_FOCUSED_OWNED_MENU_PASS=True",
            "OWNED_WINUI_SHELL_EXIT 0",
            "ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True",
            "OWNED_SYNTHETIC_FIXTURE_REMOVED True",
            "LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT 6",
        )
        body = "\n".join(required) + "\n"
        self.assertTrue(r06_share_menu_evidence_ok(body))
        for line in required:
            with self.subTest(missing=line):
                self.assertFalse(r06_share_menu_evidence_ok(
                    body.replace(line + "\n", "", 1)))
        self.assertFalse(r06_share_menu_evidence_ok(
            body.replace("PRESENT 6", "PRESENT unknown")))
        self.assertFalse(r06_share_menu_evidence_ok(
            body + "Traceback (most recent call last)\n"))
        for marker in required[:4]:
            self.assertIn(marker, script)


if __name__ == "__main__":
    unittest.main()

"""Narrow regression: retired MFC-era sources do not re-enter WinUI builds."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
REMOVED = ["conf_file.cpp","conf_file.h","conf_file_ex.h","crc32.c","crc32.h","def.h","def_win.h","env_path.cpp","env_path.h","fnmatch.cpp","fnmatch.h","format_string_table.cpp","format_string_table.h","getopt.c","getopt.h","hash-internal.h","inttypes.h","language_pack.cpp","language_pack.h","language_table.cpp","language_table.h","md5.c","md5.h","pattern.h","pidl_win.cpp","pidl_win.h","sha.c","sha.h","shell_enumerator.h","shell_enumerator_win.cpp","shell_item.h","shell_item_win.cpp","stdint.h","string_table.cpp","string_table.h","xml.cpp","xml.h","shell_async_worker.cpp","shell_async_worker.h"]

class RetiredLegacySourceContract(unittest.TestCase):
    def test_removed_legacy_source_has_no_live_checkout_files(self):
        root = ROOT / "src" / "base"
        self.assertEqual([], [name for name in REMOVED if (root / name).exists()])

    def test_shell_supervisor_uses_own_action_contract(self):
        hdr = (ROOT / "src/base/shell_isolated_supervisor.h").read_text(encoding="utf-8")
        action = (ROOT / "src/base/navigation_action.h").read_text(encoding="utf-8")
        self.assertIn('#include "navigation_action.h"', hdr)
        self.assertIn("enum class NavigationAction", action)
        for token in ("Open", "Back", "Forward", "Up", "Refresh", "Continue"):
            self.assertIn(token, action)
        projects = [ROOT / "app/winui/flyExplorer.project-template.xml",
                    ROOT / "app/winui/helper/FlyShellIsolationHelper.project-template.xml"]
        for project in projects:
            contents = project.read_text(encoding="utf-8")
            for name in REMOVED:
                self.assertNotIn(name, contents, (project, name))

    def test_legacy_third_party_credits_are_retired_not_active_nuget_notices(self):
        credits = (ROOT / "CREDITS").read_text(encoding="utf-8")
        for obsolete in ("GFL SDK/GflAx", "CResizingDialog", "CButtonST"):
            self.assertNotIn(obsolete, credits)
        self.assertIn("Microsoft Fluent UI System Icons", credits)
        self.assertTrue((ROOT / "packaging/licenses/nuget").is_dir())

if __name__ == "__main__":
    unittest.main()

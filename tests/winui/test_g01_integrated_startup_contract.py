"""G01: integrated pre-start fixture, one bounded left-pane oracle, no other GUI."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/winui"))
import run_checks


class G01IntegratedStartupContract(unittest.TestCase):
    def test_integrated_profile_is_owned_bounded_and_not_all_gui(self):
        cmd, env, max_seconds=run_checks.gui_command(
            "startup-integrated","Release",{"GITHUB_ACTIONS":"true"})
        self.assertEqual("test_shell_gui.py",Path(cmd[-1]).name)
        self.assertEqual(260,max_seconds)
        self.assertEqual("YES",env.get("FLY_G01_INTEGRATED_STARTUP_ONLY"))
        for feature in run_checks.OWNED_FLAGS:
            self.assertEqual("YES",env.get(feature),feature)
        self.assertEqual("YES",env.get("FLY_M20_OWNED_COLLAPSE_M19_PANELS"))
        self.assertEqual("YES",env.get("FLY_EP05_EXPLORER_HANDOFF"))
        for prohibited in run_checks.FAULT_FLAGS:
            if prohibited != "FLY_M20_OWNED_COLLAPSE_M19_PANELS":
                self.assertNotEqual("YES",env.get(prohibited),prohibited)
        self.assertIn("startup-integrated",run_checks.GUI_AREAS)
        self.assertNotEqual("all","startup-integrated")

    def test_startup_only_waits_for_actual_left_fixture_before_exiting(self):
        harness=(ROOT/"tests/winui/test_shell_gui.py").read_text("utf-8")
        self.assertIn('if G01_INTEGRATED_STARTUP_ONLY:',harness)
        self.assertIn('element("LeftFiles").descendants()',harness)
        self.assertIn('return matched and (not G01_INTEGRATED_STARTUP_ONLY or left_visible)',harness)
        self.assertIn('G01_INTEGRATED_STARTUP_GUI_PASS=True',harness)
        self.assertIn('raise SystemExit(0)',harness)
        self.assertIn('"UI-independent native core/helper was not active at startup",18',harness)
        self.assertIn('"left_fixture_visible":left_visible',harness)


if __name__=="__main__": unittest.main()

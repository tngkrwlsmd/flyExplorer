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
        baseline_cmd, baseline, _ = run_checks.gui_command(
            "core","Release",{"FLY_G01_INTEGRATED_STARTUP_ONLY":"YES"})
        self.assertEqual("test_shell_gui.py",Path(baseline_cmd[-1]).name)
        self.assertNotIn("FLY_G01_INTEGRATED_STARTUP_ONLY",baseline)
        runner=(ROOT/"tools/winui/run_checks.py").read_text("utf-8")
        self.assertIn("G01_INTEGRATED_STARTUP_GUI_PASS=True",runner)
        self.assertIn("G01_INTEGRATED_STARTUP_MARKER_MISSING",runner)
        self.assertIn('g01_startup_evidence_ok(body)',runner)
        self.assertIn('LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT ',runner)
        for marker in ("G01_FINAL_WINDOW_ADDRESS_FOCUS=PASS",
                       "G01_FINAL_WINDOW_CTRL_W_EXIT=0",
                       "OWNED_WINUI_SHELL_EXIT 0",
                       "LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True",
                       "OWNED_SYNTHETIC_FIXTURE_REMOVED True"):
            self.assertIn(marker,runner)

    def test_startup_only_waits_for_actual_left_fixture_before_exiting(self):
        harness=(ROOT/"tests/winui/test_shell_gui.py").read_text("utf-8")
        self.assertIn('if G01_INTEGRATED_STARTUP_ONLY:',harness)
        self.assertIn('element("LeftFiles").descendants()',harness)
        self.assertIn('return matched and (not G01_INTEGRATED_STARTUP_ONLY or left_visible)',harness)
        self.assertIn('G01_INTEGRATED_STARTUP_GUI_PASS=True',harness)
        self.assertIn('from pywinauto.keyboard import send_keys',harness)
        close_section=harness.split('print("G01_INTEGRATED_STARTUP_GUI_PASS=True"',1)[1]
        close_section=close_section.split('raise SystemExit(0)',1)[0]
        for fragment in ('send_keys("^l")',
                         'element("AddressBox").has_keyboard_focus()',
                         'foreground_pid.value==p.pid',
                         'G01_FINAL_WINDOW_ADDRESS_FOCUS=PASS',
                         'send_keys("^w")',
                         'p.poll() is not None',
                         'p.returncode==0',
                         'G01_FINAL_WINDOW_CTRL_W_EXIT=0'):
            self.assertIn(fragment,close_section)
        self.assertIn('raise SystemExit(0)',harness)
        self.assertIn('"UI-independent native core/helper was not active at startup",18',harness)
        self.assertIn('"left_fixture_visible":left_visible',harness)


    def test_g01_startup_gate_handles_real_sentinel_line(self):
        markers=(
            "G01_INTEGRATED_STARTUP_GUI_PASS=True",
            "G01_FINAL_WINDOW_ADDRESS_FOCUS=PASS",
            "G01_FINAL_WINDOW_CTRL_W_EXIT=0",
            "OWNED_WINUI_SHELL_EXIT 0",
            "LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT 6",
            "OWNED_SYNTHETIC_FIXTURE_REMOVED True",
        )
        body="\\n".join(markers)+"\\n"
        self.assertTrue(run_checks.g01_startup_evidence_ok(body))
        for missing in markers:
            self.assertFalse(run_checks.g01_startup_evidence_ok(
                "\\n".join(line for line in markers if line!=missing)))
        self.assertFalse(run_checks.g01_startup_evidence_ok(
            body.replace("True PRESENT 6","True PRESENT invalid")))
        self.assertFalse(run_checks.g01_startup_evidence_ok(
            body+"Traceback (most recent call last)\\n"))



if __name__=="__main__": unittest.main()

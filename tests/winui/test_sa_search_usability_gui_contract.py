"""SA01/SA02 focused GUI wiring and test-owned safety contract."""
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "winui"))
from run_checks import sa_search_usability_evidence_ok


def src(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class SearchUsabilityGuiContract(unittest.TestCase):
    def test_gui_sources_parse_and_use_owned_shell_lifecycle(self):
        paths = (
            "tests/winui/test_sa_search_usability_gui.py",
            "tests/winui/test_shell_gui.py",
            "tools/winui/run_checks.py",
        )
        for path in paths:
            with self.subTest(path=path):
                ast.parse(src(path), filename=path)
        shell = src(paths[1])
        self.assertIn('if os.environ.get("FLY_SA_SEARCH_USABILITY_ONLY")=="YES":', shell)
        self.assertIn('from test_sa_search_usability_gui import run as sa_search_probe', shell)
        self.assertIn("SA_SEARCH_USABILITY_FOCUSED_GUI_PASS=True", shell)
        self.assertIn("OWNED_SYNTHETIC_FIXTURE_REMOVED", shell)
        self.assertIn("LEGACY_USER_PROFILE_SENTINEL_UNCHANGED", shell)

    def test_sa01_sa02_real_controls_and_focused_oracle(self):
        gui = src("tests/winui/test_sa_search_usability_gui.py")
        for label in (
            "SearchPanelButton", "SearchModeBox", "SearchModeGuidanceText",
            "SearchRegexBox", "SearchCaseBox", "SearchContentBox",
            "SearchTargetBox", "SearchMatches", "SearchResultsSizeButton",
            "SearchCountText", "SearchLocateButton",
        ):
            with self.subTest(label=label):
                self.assertIn(label, gui)
        self.assertIn("left.is_relative_to(owned)", gui)
        self.assertIn('element("SearchRunButton").invoke()', gui)
        self.assertIn('scroll_to("SearchModeBox").select(1)', gui)
        self.assertIn('scroll_to("SearchModeBox").select(0)', gui)
        self.assertIn('label.invoke()', gui)
        self.assertIn("baseline + 55", gui)
        self.assertIn("검색 결과 1개", gui)
        self.assertIn("len(results()) == 1", gui)
        # A compact 960x519 owned window clips the SearchPanel's results.
        # Demand real ScrollPattern movement, not relaxed result assertions.
        self.assertIn('scroll.CurrentVerticallyScrollable', gui)
        self.assertIn('scroll.SetScrollPercent(-1, percent)', gui)
        self.assertIn('scroll_to("SearchMatches")', gui)
        self.assertIn('scroll_to("SearchCountText")', gui)
        self.assertIn('"검색 완료" in element("StatusText").window_text()', gui)
        self.assertIn('assert "검색 결과 1개" in count_text', gui)
        self.assertNotIn("indexer.exe", gui)
        self.assertNotIn("os.system(", gui)

    def test_dispatch_requires_independent_success_evidence(self):
        runner = src("tools/winui/run_checks.py")
        self.assertIn('"search-usability",', runner)
        self.assertIn('if area == "search-usability":', runner)
        self.assertIn('gui_env["FLY_SA_SEARCH_USABILITY_ONLY"] = "YES"', runner)
        self.assertIn('if not rc and area == "search-usability":', runner)
        for marker in (
            "SA01_GUI_DIRECT_GUIDANCE=PASS",
            "SA01_GUI_INDEXED_LIMITS_BEFORE_SUBMIT=PASS",
            "SA01_GUI_UNSUPPORTED_OPTIONS_LIVE=PASS",
            "SA01_GUI_MODE_RESTORE_WITHOUT_SEARCH=PASS",
            "SA02_GUI_EXPANDED_PRESERVED_RESULT=PASS",
            "SA02_GUI_COLLAPSED_PRESERVED_SELECTION=PASS",
            "SA_SEARCH_USABILITY_FOCUSED_GUI_PASS=True",
            "OWNED_WINUI_SHELL_EXIT 0",
            "LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True",
            "OWNED_SYNTHETIC_FIXTURE_REMOVED True",
        ):
            self.assertIn(marker, runner)
            self.assertIn(marker, src("tests/winui/test_sa_search_usability_gui.py") +
                          src("tests/winui/test_shell_gui.py") if marker.startswith("SA")
                          else runner)
        self.assertIn("def sa_search_usability_evidence_ok(body: str) -> bool:", runner)
        self.assertIn("if not sa_search_usability_evidence_ok(body):", runner)
        self.assertIn("LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT ", runner)
        self.assertIn("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True", runner)


    def test_replays_real_20261103_gui_proof_without_loosening_evidence(self):
        # Exact bounded markers observed in archived owned GUI #41628765731.
        # No screenshots, private paths or user-profile bytes are embedded.
        observed = (
            "REAL_WINUI_SHELL_CONTROLS 12 DUAL_PANES_AND_TABS=True",
            "ACTUAL_CPP_NATIVE_CORE_NULL_CONTRACT_LINKED True",
            "REAL_FILE_LIST_IN_LEFT_PANE True",
            "SA01_GUI_DIRECT_GUIDANCE=PASS",
            "SA02_GUI_EXPANDED_PRESERVED_RESULT=PASS",
            "SA02_GUI_COLLAPSED_PRESERVED_SELECTION=PASS",
            "SA01_GUI_INDEXED_LIMITS_BEFORE_SUBMIT=PASS",
            "SA01_GUI_UNSUPPORTED_OPTIONS_LIVE=PASS",
            "SA01_GUI_MODE_RESTORE_WITHOUT_SEARCH=PASS",
            "SA_SEARCH_USABILITY_FOCUSED_GUI_PASS=True",
            "OWNED_WINUI_SHELL_EXIT 0",
            "LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT 6",
            "ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True",
            "OWNED_SYNTHETIC_FIXTURE_REMOVED True",
        )
        body = "\n".join(observed) + "\n"
        self.assertTrue(sa_search_usability_evidence_ok(body))
        for line in observed[3:]:
            with self.subTest(missing=line):
                self.assertFalse(sa_search_usability_evidence_ok(
                    body.replace(line + "\n", "", 1)))
        self.assertFalse(sa_search_usability_evidence_ok(
            body.replace("PRESENT 6", "PRESENT not-a-count")))
        self.assertFalse(sa_search_usability_evidence_ok(
            body.replace("PRESENT 6", "")))
        self.assertFalse(sa_search_usability_evidence_ok(
            body + "Traceback (most recent call last)\n"))


if __name__ == "__main__":
    unittest.main()

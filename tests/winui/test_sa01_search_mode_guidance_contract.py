"""SA01: index-only restrictions are visible before submitting search."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
XAML = (ROOT / "app/winui/MainWindow.xaml").read_text(encoding="utf-8-sig")
HEADER = (ROOT / "app/winui/MainWindow.xaml.h").read_text(encoding="utf-8-sig")
FEATURE = (ROOT / "app/winui/m19_features.cpp").read_text(encoding="utf-8-sig")
CORE = (ROOT / "app/winui/m19_search.cpp").read_text(encoding="utf-8-sig")


class SearchModeGuidanceContract(unittest.TestCase):
    def test_guidance_is_in_search_panel_and_named_for_accessibility(self):
        root = ET.fromstring(XAML)
        name = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
        search = next(node for node in root.iter() if node.get(name) == "SearchPanel")
        children = {node.get(name): node for node in search.iter() if node.get(name)}
        hint = children["SearchModeGuidanceText"]
        self.assertEqual(hint.get("TextWrapping"), "Wrap")
        self.assertTrue(hint.get("AutomationProperties.Name"))
        self.assertIn("직접 탐색", hint.get("Text"))
        self.assertEqual(children["SearchModeBox"].get("SelectionChanged"),
                         "OnSearchModeCriteriaChanged")

    def test_index_unsupported_criteria_refresh_without_submitting(self):
        root = ET.fromstring(XAML)
        name = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
        controls = {node.get(name): node for node in root.iter() if node.get(name)}
        for field in ("SearchRegexBox", "SearchCaseBox", "SearchContentRegexBox"):
            self.assertEqual(controls[field].get("Checked"),
                             "OnSearchOptionCriteriaChanged")
            self.assertEqual(controls[field].get("Unchecked"),
                             "OnSearchOptionCriteriaChanged")
        self.assertEqual(controls["SearchTargetBox"].get("SelectionChanged"),
                         "OnSearchModeCriteriaChanged")
        self.assertEqual(controls["SearchContentBox"].get("TextChanged"),
                         "OnSearchContentCriteriaChanged")
        for method in ("OnSearchModeCriteriaChanged", "OnSearchOptionCriteriaChanged",
                       "OnSearchContentCriteriaChanged", "UpdateSearchModeGuidance"):
            self.assertIn("void " + method + "(", HEADER)
            self.assertIn("void MainWindow::" + method + "(", FEATURE)
        code = FEATURE.split("void MainWindow::UpdateSearchModeGuidance()", 1)[1].split(
            "void MainWindow::OnSearchModeCriteriaChanged(", 1)[0]
        for token in ("SearchModeBox().SelectedIndex()!=1", "SearchRegexBox().IsChecked()",
                      "SearchCaseBox().IsChecked()", "SearchTargetBox().SelectedIndex()!=0",
                      "SearchContentBox().Text().empty()", "SearchContentRegexBox().IsChecked()",
                      "현재 설정의 미지원 조건", "정규식·내용·대소문자 구분·폴더 대상 미지원"):
            self.assertIn(token, code)
        for forbidden in ("mSearchController.start(", "mSearchController.invalidate(",
                          "SearchMatches().Items().Clear()", "OpenFolder("):
            self.assertNotIn(forbidden, code)
        toggle = FEATURE.split("void MainWindow::OnToggleSearch(", 1)[1].split(
            "void MainWindow::OnRunSearch(", 1)[0]
        self.assertIn("UpdateSearchModeGuidance();", toggle)

    def test_core_remains_authoritative_for_invalid_index_options(self):
        core = CORE.split("SearchQueryValidation validateSearchQuery(", 1)[1].split(
            "bool sameSearchQuery(", 1)[0]
        for criterion in ("query.regex", "query.caseSensitive",
                          "query.kind!=SearchEntryKind::Files",
                          "!query.contentTerm.empty()", "query.contentRegex",
                          "SearchQueryValidation::InvalidIndexedCriteria"):
            self.assertIn(criterion, core)


if __name__ == "__main__":
    unittest.main()

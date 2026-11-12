"""SA02: expand only the search results viewport, retaining existing search ownership."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class SearchResultsExpandContract(unittest.TestCase):
    def test_toggle_is_inside_bounded_search_panel_with_compact_default(self):
        root = ET.fromstring(source("app/winui/MainWindow.xaml"))
        xname = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
        search = next(x for x in root.iter() if x.get(xname) == "SearchPanel")
        self.assertTrue(search.tag.endswith("}ScrollViewer"))
        self.assertEqual(search.get("MaxHeight"), "400")
        self.assertEqual(search.get("VerticalScrollBarVisibility"), "Auto")
        children = {x.get(xname): x for x in search.iter() if x.get(xname)}
        self.assertEqual(children["SearchMatches"].get("Height"), "64")
        button = children["SearchResultsSizeButton"]
        self.assertEqual(button.get("Content"), "결과 펼치기")
        self.assertEqual(button.get("Click"), "OnToggleSearchResults")
        self.assertIn("결과 선택", button.get("ToolTipService.ToolTip"))
        self.assertEqual(children["SearchMatches"].get("SelectionChanged"),
                         "OnSearchMatchSelectionChanged")
        self.assertIn("SearchLocateButton", children)

    def test_toggle_changes_height_and_label_without_invalidating_results(self):
        header = source("app/winui/MainWindow.xaml.h")
        cpp = source("app/winui/m19_features.cpp")
        self.assertIn("void OnToggleSearchResults(", header)
        method = cpp.split("void MainWindow::OnToggleSearchResults(", 1)[1].split(
            "void MainWindow::UpdateSearchModeGuidance()", 1)[0]
        for token in ("SearchPanel().Visibility()!=Visibility::Visible",
                      "compactHeight=64.0", "expandedHeight=160.0",
                      "SearchMatches().Height()<=compactHeight",
                      "SearchMatches().Height(expand?expandedHeight:compactHeight)",
                      "SearchResultsSizeButton().Content(",
                      'expand?L"결과 접기":L"결과 펼치기"'):
            self.assertIn(token, method)
        for forbidden in ("mSearchController.", "mSearchResultPaths",
                          "SearchMatches().Items()", "SearchMatches().SelectedIndex(",
                          "QueuePath(", "SearchContext()", "SearchRunButton()",
                          "SearchLocateButton()", "AppWindow().Resize("):
            self.assertNotIn(forbidden, method)

    def test_applied_nonempty_result_is_brought_into_bounded_view(self):
        cpp = source("app/winui/m19_features.cpp")
        completed = cpp.split("void MainWindow::OnSearchCompleted(", 1)[1].split(
            "std::wstring MainWindow::SelectedSearchMatchPath", 1)[0]
        gate = "if(accepted.disposition!=Disposition::Applied)return;"
        visible = "SearchPanel().Visibility()==Visibility::Visible"
        reveal = "SearchMatches().StartBringIntoView();"
        self.assertIn(gate, completed)
        self.assertIn("if(!completion.result.matches.empty()&&", completed)
        self.assertIn(visible, completed)
        self.assertIn("SearchMatches().UpdateLayout();", completed)
        self.assertIn(reveal, completed)
        self.assertLess(completed.index(gate), completed.index(reveal))
        self.assertLess(completed.index("items.Append(row);"),
                        completed.index(reveal))
        self.assertLess(completed.index(visible), completed.index(reveal))
        # No auto-reveal before accepting a valid search context.
        self.assertNotIn(reveal, completed[:completed.index(gate)])

    def test_file_panes_retain_minimum_height_with_scrolling(self):
        cpp = source("app/winui/m19_features.cpp")
        sized = cpp.split("void MainWindow::OnSearchPanelSizeChanged(", 1)[1].split(
            "void MainWindow::OnToggleSearchResults(", 1)[0]
        for marker in ("minimumFilePane=160.0", "root.ActualHeight()-chrome-minimumFilePane",
                       "0.0,400.0", "search.MaxHeight(maximum)"):
            self.assertIn(marker, sized)
        self.assertNotIn("AppWindow().Resize(", sized)
        xaml = source("app/winui/MainWindow.xaml")
        self.assertIn('Grid.Row="7"', xaml)
        self.assertIn('x:Name="LeftFiles"', xaml)
        self.assertIn('x:Name="RightFiles"', xaml)

    def test_search_matching_and_reveal_contract_remains_separate(self):
        feature = source("app/winui/m19_features.cpp")
        self.assertIn("mSearchController.accept(completion,live)", feature)
        self.assertIn("mSearchResultPaths=completion.result.matches;", feature)
        self.assertIn("SearchMatches().SelectedIndex()", feature)
        self.assertIn("QueuePath(mSearchResultContext.side,containingFolder)", feature)


if __name__ == "__main__":
    unittest.main()

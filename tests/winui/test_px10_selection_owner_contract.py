"""PX10: delayed WinUI selection events may not activate stale pane rows.

Source contracts only; they do not replace owned interactive GUI acceptance.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def read(relative):
    return (ROOT/relative).read_text(encoding="utf-8-sig")


class Px10SelectionOwnerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        main=read("app/winui/MainWindow.xaml.cpp")
        cls.handler=main.split(
            "void MainWindow::OnFileSelectionChanged(",1)[1].split(
            "void MainWindow::OnFileSelectionKeyUp(",1)[0]
        cls.fill=main.split(
            "void MainWindow::FillFiles(int side)",1)[1].split(
            "std::wstring MainWindow::WindowTabLabel(",1)[0]

    def test_delayed_selection_must_match_active_workspace_and_route(self):
        h=self.handler
        for guard in (
            "if(mPopulatingFileLists)return;",
            "visible.visibleRoute!=pane.routeIds[pane.active]",
            "visible.visibleTab!=pane.active",
            "ownedPresentation=view.Tag()&&",
            "winrt::unbox_value<std::uint64_t>(view.Tag())==",
            "ActiveWindowTab().identity;",
            "if(!ownedPresentation)return;",
        ):
            self.assertIn(guard,h)
        self.assertLess(h.index("if(!ownedPresentation)return;"),
                        h.index("for(auto const& candidate:view.SelectedItems())"))
        self.assertLess(h.index("if(!ownedPresentation)return;"),
                        h.index("ActivatePane(side);"))

    def test_only_a_current_rendered_file_can_activate_other_pane(self):
        h=self.handler
        self.assertIn("for(auto const& candidate:args.AddedItems())",h)
        self.assertIn("if(!row||!row.Tag())continue;",h)
        self.assertIn("view.Items().IndexOf(candidate,currentIndex)",h)
        self.assertLess(h.index("view.Items().IndexOf(candidate,currentIndex)"),
                        h.index("if(newlySelectedFile&&"))
        self.assertIn("if(newlySelectedFile&&ActiveWindowTab().model.activePane!=side)",h)
        # Group headings (without a file Tag) remain excluded.
        self.assertIn("if(row&&!row.Tag())nonFiles.push_back(candidate);",h)

    def test_rebuilt_selection_still_restores_identity_not_row_index(self):
        fill=self.fill
        for token in (
            "state.renderedFolder==snapshot.parsingName",
            "sameWindowTab=winrt::unbox_value<std::uint64_t>(view.Tag())",
            "for(auto const& old:view.SelectedItems())",
            "selected.push_back(renderedState.renderedPaths[position]);",
            "std::find(selected.begin(),selected.end(),itemParsing)",
            "view.SelectedItems().Append(row);",
            "view.Tag(winrt::box_value(ActiveWindowTab().identity));",
        ):
            self.assertIn(token,fill)
        self.assertLess(fill.index("mPopulatingFileLists=true;"),
                        fill.index("view.Items().Clear();"))
        self.assertLess(fill.index("view.Items().Clear();"),
                        fill.index("mPopulatingFileLists=false;"))


if __name__=="__main__":
    unittest.main()

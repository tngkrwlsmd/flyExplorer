"""F05 feature bridge contract: headings must never be native Shell rows."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
XAML=(ROOT/"app/winui/FileToolbar.xaml").read_text(encoding="utf-8")
TOOL_HEADER=(ROOT/"app/winui/FileToolbar.xaml.h").read_text(encoding="utf-8")
TOOL_CPP=(ROOT/"app/winui/FileToolbar.xaml.cpp").read_text(encoding="utf-8")
WINDOW_HEADER=(ROOT/"app/winui/MainWindow.xaml.h").read_text(encoding="utf-8")
WINDOW_CPP=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
STATE=(ROOT/"app/winui/file_list_state.h").read_text(encoding="utf-8")
TRANSFERS=(ROOT/"app/winui/m22_transfers.cpp").read_text(encoding="utf-8")


class F05WinUIGroupIntegrationContract(unittest.TestCase):
    def test_group_control_is_opt_in_and_routes_through_active_pane(self):
        root=ET.fromstring(XAML)
        x="{http://schemas.microsoft.com/winfx/2006/xaml}Name"
        control=next(e for e in root.iter() if e.get(x)=="ViewGroupByTypeItem")
        self.assertEqual(control.tag.rsplit("}",1)[-1],"ToggleMenuFlyoutItem")
        self.assertEqual(control.get("Click"),"OnViewGroupByType")
        for token in ("void SetGroup(", "void SetGroupState(",
                      "OnViewGroupByType(", "std::function<void(int)> group_"):
            self.assertIn(token,TOOL_HEADER)
        for token in ("FileToolbar::OnViewGroupByType(", "if(group_)group_(1);",
                      "FileToolbar::SetGroupState("):
            self.assertIn(token,TOOL_CPP)
        self.assertIn("void ToggleGroupByType();",WINDOW_HEADER)
        self.assertIn("ui->ToggleGroupMode(mode);",WINDOW_CPP)
        self.assertIn("state.groupByType=state.groupTabCache.enabled();",WINDOW_CPP)
        self.assertIn("state.viewMode!=FileViewMode::Details",WINDOW_CPP)

    def test_background_menu_reuses_group_modes_and_route_guard(self):
        background=TRANSFERS.split(
            "void MainWindow::ShowAppBackgroundContextMenu(",1)[1].split(
            "void MainWindow::OnFileRightTapped(",1)[0]
        for token in ('group.Text(L"분류 방법")',
                      'groupChoice(L"유형",1)', 'groupChoice(L"이름",2)',
                      'groupChoice(L"크기",3)', 'groupChoice(L"수정 월",4)',
                      "item.IsChecked(grouping&&groupMode==choiceIndex-1)",
                      "ui.ToggleGroupMode(choiceIndex)"):
            self.assertIn(token,background)
        self.assertIn("item.Click(guarded(",background)
        self.assertNotIn("groupTabCache.choose(",background)

    def test_route_and_complete_model_gate_before_grouping(self):
        for token in ("bool groupByType=false;", "CollapseState groupCollapse{}"):
            self.assertIn(token,STATE)
        for token in ("!snapshot.truncated", "metadataReady",
                      "!state.fullModelLimitReached",
                      "snapshot.baseOffset==0", "snapshot.nextOffset==items.size()",
                      "kMaximumIndexedItems", "projectByType(",
                      "filegroup::present(", "groupIndices.emplace(logical,index)",
                      "fileBar()->SetGroupState(0)"):
            self.assertIn(token,WINDOW_CPP)
        self.assertIn("groupRows.push_back({logical,filesystemAt(index)",WINDOW_CPP)

    def test_group_headings_are_nonfile_rows_and_selection_restored_by_identity(self):
        for token in ("EntryKind::Heading", "ListViewItem heading;",
                      "heading.IsTabStop(false);","heading.CanDrag(false);",
                      "heading.Content(disclosure);", "view.Items().Append(heading);",
                      "state.renderedLogical.push_back(logical);",
                      "state.renderedPaths.push_back(itemParsing);",
                      "if(row&&!row.Tag())nonFiles.push_back(candidate);",
                      "ui->mWorkspace.activeIndex()!=windowIndex",
                      "pane.routeIds[tab]!=route",
                      "files.groupTabCache.toggle(title)",
                      "UpdateSelectionChrome();"):
            self.assertIn(token,WINDOW_CPP)

    def test_no_filesystem_or_os_setting_changes_for_group_handler(self):
        block=WINDOW_CPP.split("void MainWindow::ToggleGroupByType()",1)[1].split(
            "void MainWindow::UpdateViewPresentation",1)[0]
        for bad in ("CreateFile", "DeleteFile", "SetFileAttributes",
                    "SystemParametersInfoW", "mShellNavigation->"):
            self.assertNotIn(bad,block)


if __name__=="__main__":
    unittest.main()

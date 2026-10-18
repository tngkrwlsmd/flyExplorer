"""F04-B opt-in tree must stay scoped to the current pane and safe local roots."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

class F04SidebarTreeContracts(unittest.TestCase):
    def test_opt_in_accessible_tree_and_existing_shortcuts(self):
        xaml=read("app/winui/NavigationSidebar.xaml")
        for required in ('x:Name="FolderTreeToggle"', 'Click="OnFolderTreeToggleClicked"',
                         'x:Name="FolderTreePanel" Visibility="Collapsed"',
                         'x:Name="FolderTreeView"', 'Expanding="OnTreeExpanding"',
                         'Collapsed="OnTreeCollapsed"', 'SelectionChanged="OnTreeSelectionChanged"',
                         'SelectionMode="Single"', 'AutomationProperties.Name="현재 폴더의 하위 폴더 트리"',
                         'x:Name="HomeButton"', 'x:Name="ThisPCButton"'):
            self.assertIn(required,xaml)

    def test_active_pane_route_and_worker_boundary(self):
        ui=read("app/winui/MainWindow.xaml.cpp")
        side=read("app/winui/NavigationSidebar.xaml.cpp")
        worker=read("app/winui/folder_tree_worker.h")
        for key in ("SetTreeCallbacks(", "pane.routeIds[pane.active]",
                    "pane.filesystemPaths[pane.active]", "model.activePane",
                    "SyncTreeContext()", "ui->OpenFolder(path)"):
            self.assertIn(key,ui)
        for key in ("mTreeGeneration", "mTreeCancel", "mTreeBusy",
                    "request.generation!=self->mTreeGeneration",
                    "!self->IsCurrentTreeOwner()", "std::thread(",
                    "enumerateFixedChildren", "HasUnrealizedChildren"):
            self.assertIn(key,side)
        for key in ("GetDriveTypeW", "DRIVE_FIXED", "FILE_ATTRIBUTE_REPARSE_POINT",
                    "FindFirstFileW", "FindNextFileW", "FindClose",
                    "kMaxChildrenPerNode", "kMaxVisited=4096",
                    "GetTickCount64", "FILE_ATTRIBUTE_HIDDEN"):
            self.assertIn(key,worker)
        self.assertIn("#include <winrt/Microsoft.UI.Xaml.Automation.h>",side)
        self.assertIn("next.path==mTreeOwner.path",side)
        self.assertIn("void NavigationSidebar::OnTreeSelectionChanged(",side)
        self.assertIn("sender.SelectedNode()",side)
        self.assertIn('GetEnvironmentVariableW(L"FLY_F04_TREE_ONLY"',side)
        self.assertIn('shell-owned-',side)
        for stage in ("F04_EVENT_ENTERED","F04_OWNER_REJECTED",
                      "F04_NODE_NULL","F04_PATH_REJECTED",
                      "F04_CURRENT_ROOT_SELECTED","F04_NAV_REQUESTED"):
            self.assertIn(stage,side)
        self.assertIn("path==mTreeOwner.path",side)
        self.assertIn("mTreeNavigate(path);",side)
        self.assertNotIn('ItemInvoked="OnTreeItemInvoked"',
                         read("app/winui/NavigationSidebar.xaml"))
        self.assertNotIn("OnTreeItemInvoked(",side)
        self.assertIn("cancel->load() || !self->IsCurrentTreeOwner()",side)
        self.assertIn("!self->mTreePending && self->IsCurrentTreeOwner()",side)
        self.assertIn("FLY_F04_TREE_ONLY", (ROOT / "tests/winui/test_shell_gui.py").read_text(encoding="utf-8"))
        harness = read("tests/winui/test_shell_gui.py")
        initial = harness.index('print("REAL_WINUI_SHELL_CONTROLS"')
        focus = harness.index('if os.environ.get("FLY_F04_TREE_ONLY")=="YES":', initial)
        standard = harness.index("startup_status=", initial)
        self.assertLess(focus, standard)
        focused = harness[focus:standard]
        self.assertIn('for name in ("LeftFiles","RightFiles"):', focused)
        self.assertIn('safe_click(element(ready))', focused)
        self.assertIn("F04_FOCUSED_READY_PANE=PASS", focused)
        self.assertIn('"UI-independent native core/helper was not active at startup"',
                      harness[standard:])

        self.assertIn('"folder-tree"', (ROOT / "tools/winui/run_checks.py").read_text(encoding="utf-8"))
        self.assertIn("capture(\"expanded\")", (ROOT / "tests/winui/test_f04_tree_gui.py").read_text(encoding="utf-8"))
        probe = (ROOT / "tests/winui/test_f04_tree_gui.py").read_text(encoding="utf-8")
        self.assertIn("def tree_visible():", probe)
        self.assertIn("return tree.exists(timeout=.2) and tree.is_visible()", probe)
        self.assertIn('x.element_info.control_type == "Text"', probe)
        self.assertIn('safe_click(row)', probe)
        self.assertIn('row.iface_selection_item.Select()', probe)
        self.assertIn('F04_DIAG_UIA_SELECTION_NAVIGATED=YES', probe)
        self.assertNotIn('safe_click(label)', probe)
        self.assertIn('except AssertionError as evidence_error:', probe)
        self.assertIn('F04_FAILURE_CAPTURE_SKIPPED=', probe)
        self.assertIn('F04_CLICK_DIAG_ROOT_STILL_ACTIVE=', probe)
        self.assertIn('F04_TREE_SELECTION_STAGE=', probe)
        self.assertIn('F04_TREE_UIA_SELECTED=', probe)
        runner = read("tools/winui/run_checks.py")
        self.assertIn('if code and label.startswith("gui-folder-tree-"):', runner)
        self.assertIn('"F04_TREE_SELECTION_STAGE="', runner)
        self.assertIn('"F04_TREE_UIA_SELECTED="', runner)
        self.assertIn('"F04_DIAG_UIA_SELECTION_NAVIGATED="', runner)
        self.assertIn('line.startswith(allowed)', runner)
        self.assertNotIn("assert toggle.exists(timeout=4) and not tree.is_visible()", probe)
        self.assertNotIn("GetFileAttributesW(",side)
        self.assertNotIn("FindFirstFileW(",side)
        self.assertNotIn("DeleteFile",worker)
        self.assertNotIn("ShellExecute",worker)

if __name__=="__main__":
    unittest.main()

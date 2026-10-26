"""Source-level contract for F2 rename selection without changing filesystem operations."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"


class RenameSelectionContract(unittest.TestCase):
    def test_file_stem_is_selected_without_last_extension(self):
        body = (APP / "FileToolbar.xaml.cpp").read_text(encoding="utf-8-sig")
        for token in (
            "BeginNameEdit(int action,hstring const& initial,bool isFolder)",
            "name.find_last_of(L'.')",
            "(action==1||action==2)&&!isFolder",
            "dot>0&&dot+1<name.size()",
            "box.Select(0,static_cast<int>(dot))",
            "else box.SelectAll()",
        ):
            self.assertIn(token, body)

    def test_folder_type_comes_from_indexed_item_not_filename_guess(self):
        commands = (APP / "m21_commands.cpp").read_text(encoding="utf-8-sig")
        header = (APP / "FileToolbar.xaml.h").read_text(encoding="utf-8-sig")
        self.assertIn("renameFolder=indexed->isFolder();", commands)
        self.assertIn("hstring(initial),renameFolder", commands)
        self.assertIn("hstring const& initial,bool isFolder", header)
        self.assertNotIn("std::filesystem::path(initial).extension()", commands)

    def test_rename_edit_captures_selected_source_and_workspace(self):
        header=(APP / "MainWindow.xaml.h").read_text(encoding="utf-8-sig")
        commands=(APP / "m21_commands.cpp").read_text(encoding="utf-8-sig")
        begin=commands.split("void MainWindow::BeginFileNameCommand(",1)[1].split(
            "void MainWindow::ExecuteFileCommand(",1)[0]
        for field in (
            "struct PendingNameEdit final",
            "fxfile::filecommand::Kind kind;",
            "fxfile::previewops::FileOperationController::Context context{};",
            "std::wstring source{};",
            "std::optional<PendingNameEdit> mPendingNameEdit{};",
        ):
            self.assertIn(field,header)
        self.assertLess(header.index("struct PendingNameEdit final"),
                        header.index("using FileOperationController=fxfile::previewops::FileOperationController;"))
        self.assertNotIn("FileOperationController::Context context{};",header.split(
            "struct PendingNameEdit final",1)[1].split("};",1)[0])
        self.assertIn("mPendingNameEdit.reset();",begin)
        self.assertIn("const auto editContext=FileOperationContext(editSide);",begin)
        self.assertIn("renameSource=indexed->parsingName;",begin)
        self.assertIn("mPendingNameEdit=PendingNameEdit{kind,editContext,std::move(renameSource)};",begin)
        self.assertLess(begin.index("editPane.active>=editPane.tabs.size()"),
                        begin.index("FileOperationContext(editSide);"))
        self.assertLess(begin.index("mPendingNameEdit=PendingNameEdit"),
                        begin.index("fileBar()->BeginNameEdit("))

    def test_rename_commit_requires_same_pane_tab_route_and_selection(self):
        commands=(APP / "m21_commands.cpp").read_text(encoding="utf-8-sig")
        execute=commands.split("void MainWindow::ExecuteFileCommand(",1)[1].split(
            "void MainWindow::OnFileCommandCompleted(",1)[0]
        self.assertIn("mPendingNameEdit->kind!=kind",execute)
        self.assertIn("FileNameBox().Opacity()<0.5",execute)
        self.assertIn("fxfile::nameedit::sameScope(editContext,liveContext)",execute)
        self.assertIn("fxfile::nameedit::sameRenameSource(",execute)
        self.assertIn("mPendingNameEdit->source,indexed->parsingName",execute)
        native=(ROOT / "src" / "base" / "name_edit_guard.h").read_text(
            encoding="utf-8-sig")
        for item in (
            "windowTabIdentity","side","tab","route",
            "visibleFolder","visibleShellFolder"
        ):
            self.assertIn(f"opened.{item}==live.{item}",native)
        self.assertIn("!opened.empty()&&!selected.empty()&&opened==selected",native)
        self.assertIn("request.source=mPendingNameEdit->source;",execute)
        self.assertNotIn("request.source=indexed->parsingName;",execute)
        self.assertLess(execute.index("fxfile::nameedit::sameRenameSource("),
                        execute.index("mFileOperations.startFileCommand("))
        self.assertLess(execute.index("fxfile::nameedit::sameScope(editContext,liveContext)"),
                        execute.index("mFileOperations.startFileCommand("))
        self.assertIn("mPendingNameEdit.reset();",execute)
        self.assertIn("fileBar()->EndNameEdit();",execute)

    def test_cancelled_editor_cannot_commit_or_retarget_hidden_name_action(self):
        bar=(APP / "FileToolbar.xaml.cpp").read_text(encoding="utf-8-sig")
        commands=(APP / "m21_commands.cpp").read_text(encoding="utf-8-sig")
        self.assertIn("if(args.Key()==VirtualKey::Escape){EndNameEdit();",bar)
        self.assertIn("box.Opacity(0.0);",bar)
        execute=commands.split("void MainWindow::ExecuteFileCommand(",1)[1].split(
            "void MainWindow::OnFileCommandCompleted(",1)[0]
        self.assertIn("FileNameBox().Opacity()<0.5",execute)
        self.assertLess(execute.index("FileNameBox().Opacity()<0.5"),
                        execute.index("mFileOperations.startFileCommand("))

    def test_native_name_edit_gate_has_runtime_fixture(self):
        fixture=(ROOT / "tests" / "winui" /
                 "name_edit_guard_native.cpp").read_text(encoding="utf-8-sig")
        commands=(APP / "m21_commands.cpp").read_text(encoding="utf-8-sig")
        self.assertIn('#include "../../src/base/name_edit_guard.h"',commands)
        self.assertIn("fxfile::nameedit::sameScope(",commands)
        self.assertIn("fxfile::nameedit::sameRenameSource(",commands)
        for test_case in (
            "same_context","other_workspace","other_pane",
            "other_pane_tab","other_route","other_filesystem_folder",
            "other_shell_folder","same_rename_source","changed_selection",
            "empty_captured_source","empty_current_source",
            "exact_spelling_required",
        ):
            self.assertIn(f'"{test_case}"',fixture)
        self.assertIn("passed==12&&failed==0",fixture)

    def test_rename_and_create_operations_unchanged(self):
        bar = (APP / "FileToolbar.xaml.cpp").read_text(encoding="utf-8-sig")
        self.assertIn("pendingNameAction_=action", bar)
        self.assertIn("box.Focus(FocusState::Programmatic)", bar)
        self.assertIn("void FileToolbar::EndNameEdit()", bar)
        self.assertIn("pendingNameAction_==0?9:pendingNameAction_==1?10:", bar)
        self.assertIn("pendingNameAction_==2?16:-1", bar)


if __name__ == "__main__":
    unittest.main()

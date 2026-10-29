"""Stale native rename/create completions must not disappear without feedback."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

class FileCommandFeedbackContract(unittest.TestCase):
    def test_toolbar_new_item_menu_reuses_anchored_name_edit_commands(self):
        import xml.etree.ElementTree as ET
        xaml=(APP/"FileToolbar.xaml").read_text(encoding="utf-8-sig")
        tree=ET.fromstring(xaml)
        ns="{http://schemas.microsoft.com/winfx/2006/xaml}Name"
        controls={node.get(ns):node for node in tree.iter() if node.get(ns)}
        self.assertEqual(controls["NewFolderMenuItem"].get("Click"),"OnNewFolderMenu")
        self.assertEqual(controls["NewTextFileMenuItem"].get("Click"),"OnNewTextFileMenu")
        self.assertEqual(controls["CreateFolderButton"].get("Click"),"OnCreateFolder")
        submenu=next(node for node in tree.iter()
                     if node.get("AutomationProperties.Name")=="현재 폴더에 새 항목 만들기")
        gui=(ROOT/"tests/winui/test_px17_new_item_menu_gui.py").read_text(encoding="utf-8")
        self.assertIn('if node.window_text()=="'+submenu.get("AutomationProperties.Name")+'"',gui)
        toolbar=(APP/"FileToolbar.xaml.cpp").read_text(encoding="utf-8-sig")
        self.assertIn("OnNewFolderMenu(IInspectable const&,RoutedEventArgs const&){if(action_)action_(0);}",toolbar)
        self.assertIn("OnNewTextFileMenu(IInspectable const&,RoutedEventArgs const&){if(action_)action_(17);}",toolbar)
        window=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")
        command=window.split("else if(command==17)",1)[1].split("else if",1)[0]
        self.assertIn("BeginFileNameCommand(",command)
        self.assertIn("Kind::CreateTextFile",command)
        self.assertNotIn("ExecuteFileCommand",command)
        self.assertNotIn("CreateFileW",toolbar)

    def test_stale_completion_is_not_silent_or_claimed_success(self):
        body=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        completion=body.split("void MainWindow::OnFileCommandCompleted(",1)[1]
        stale=completion.split("if(disposition==Disposition::StaleContext)",1)[1].split(
            "if(disposition==Disposition::Failed)",1)[0]
        self.assertIn("StatusText().Text(",stale)
        self.assertIn("원본 폴더에서 결과를 확인하세요.",stale)
        self.assertIn("return;",stale)
        self.assertNotIn("성공",stale)
        self.assertNotIn("MoveFile",stale)

    def test_file_command_feedback_remains_in_originating_window_tab(self):
        body=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        completion=body.split("void MainWindow::OnFileCommandCompleted(",1)[1]
        self.assertIn("completion.context.windowTabIdentity",completion)
        self.assertIn("state.identity==completion.context.windowTabIdentity",completion)
        self.assertIn("state.fileOperationNotice=message;",completion)
        self.assertIn("rememberOrigin(notice);",completion)
        self.assertIn("if(originActive)StatusText().Text(hstring(notice));",completion)
        self.assertIn("if(disposition==Disposition::StaleContext)",completion)
        self.assertIn("if(disposition==Disposition::Failed)",completion)
        self.assertIn("ActiveWindowTab().fileOperationNotice.clear();",body)

    def test_failure_and_success_still_use_native_result_and_refresh(self):
        body=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        completion=body.split("void MainWindow::OnFileCommandCompleted(",1)[1]
        for required in (
            "mFileOperations.acceptFileCommand(",
            "if(disposition==Disposition::Ignored)return;",
            "if(disposition==Disposition::Failed)",
            "koreanError(completion.result.error)",
            "fileBar()->EndNameEdit();",
            "fxfile::shellnav::NavigationAction::Refresh",
        ):
            self.assertIn(required,completion)

    def test_file_command_stale_result_preserves_true_outcome(self):
        source=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        completion=source.split("void MainWindow::OnFileCommandCompleted(",1)[1]
        stale=completion.split("if(disposition==Disposition::StaleContext){",1)[1].split(
            "if(disposition==Disposition::Failed){",1)[0]
        self.assertIn("completion.result.error==ERROR_SUCCESS",stale)
        self.assertIn("파일 작업이 완료됐지만 화면이 변경됐습니다.",stale)
        self.assertIn("파일 작업에 실패했고 화면이 변경됐습니다.",stale)
        self.assertIn("std::to_wstring(completion.result.error)",stale)
        self.assertIn("rememberOrigin(notice);",stale)
        self.assertIn("if(originActive)StatusText().Text(hstring(notice));",stale)
        self.assertNotIn("QueuePidl(",stale)

    def test_create_rename_success_survives_shell_refresh_in_origin_tab(self):
        source=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        completion=source.split("void MainWindow::OnFileCommandCompleted(",1)[1]
        success=completion.split("if(disposition!=Disposition::Succeeded)return;",1)[1]
        self.assertIn("fileBar()->EndNameEdit();",success)
        self.assertIn("const std::wstring message=",success)
        for message in ("새 폴더를 만들었습니다.",
                        "새 텍스트 문서를 만들었습니다.",
                        "이름을 변경했습니다."):
            self.assertIn(message,success)
        self.assertIn("rememberOrigin(message);",success)
        self.assertLess(success.index("rememberOrigin(message);"),
                        success.index("if(originActive)StatusText().Text(hstring(message));"))
        self.assertLess(success.index("rememberOrigin(message);"),
                        success.index("QueuePidl(side,"))
        self.assertIn("fxfile::shellnav::NavigationAction::Refresh",success)

    def test_native_create_rename_target_revealed_only_after_same_refresh(self):
        ui=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")
        commands=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        pane=(APP/"file_list_state.h").read_text(encoding="utf-8-sig")
        native=(ROOT/"src"/"base"/"file_command_core.cpp").read_text(
            encoding="utf-8-sig"
        )
        for token in ("result.target=target.native();",
                      "MoveFileW(src.c_str(),target.c_str())"):
            self.assertIn(token,native)
        for token in (
            "if(disposition==Disposition::Failed)",
            "if(disposition!=Disposition::Succeeded)return;",
            "reveal.target=completion.result.target;",
            "reveal.folder=completion.context.visibleShellFolder;",
            "reveal.route=completion.context.route;",
            "reveal.tab=completion.context.tab;",
            "reveal.afterRefresh=false;",
            "fxfile::shellnav::NavigationAction::Refresh",
        ):
            self.assertIn(token,commands)
        self.assertIn("struct FileCommandReveal final",pane)
        self.assertIn("bool afterRefresh=false;",pane)
        accepted=ui.split("void MainWindow::OnNativeResult(",1)[1].split(
            "void MainWindow::OnNativeChange(",1
        )[0]
        for token in (
            "completed.action==Action::Refresh",
            "completed.kind==Kind::Applied",
            "reveal.route==pane.routeIds[pane.active]",
            "reveal.tab==pane.active",
            "reveal.afterRefresh=true;",
            "else reveal.clear();",
        ):
            self.assertIn(token,accepted)
        fill=ui.split("void MainWindow::FillFiles(int side)",1)[1].split(
            "std::wstring MainWindow::WindowTabLabel(",1
        )[0]
        for token in (
            "state.fileCommandReveal.afterRefresh",
            "state.fileCommandReveal.folder==snapshot.parsingName",
            "selected.clear();",
            "focusedPath.clear();",
            "CompareStringOrdinal(itemParsing.c_str(),-1,",
            "view.SelectedItems().Append(row);",
            "if(revealAfterRefresh)view.ScrollIntoView(focusRow);",
            "if(revealAfterRefresh)state.fileCommandReveal.clear();",
        ):
            self.assertIn(token,fill)
        self.assertNotIn("GetFileAttributesW(",fill)
        self.assertNotIn("CreateDirectoryW(",fill)

class TextDocumentCreationContract(unittest.TestCase):
    def test_f13_uses_bounded_native_worker_and_no_replace(self):
        native=(ROOT/"src"/"base"/"file_command_core.cpp").read_text(encoding="utf-8-sig")
        header=(ROOT/"src"/"base"/"file_command_core.h").read_text(encoding="utf-8-sig")
        commands=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        bar=(APP/"FileToolbar.xaml.cpp").read_text(encoding="utf-8-sig")
        win=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")
        menu=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        controller=(APP/"file_operation_controller.cpp").read_text(encoding="utf-8-sig")
        fixture=(ROOT/"tests"/"winui"/"m21"/"m21_native_fixture.cpp").read_text(encoding="utf-8-sig")
        for token in ("CreateTextFile","validTextDocumentLeaf"):
            self.assertIn(token,header)
        for token in ("Kind::CreateTextFile","validTextDocumentLeaf(task.name)",
                      "CREATE_NEW","::CreateFileW(", "FILE_ATTRIBUTE_REPARSE_POINT",
                      "drive!=DRIVE_FIXED&&drive!=DRIVE_REMOVABLE"):
            self.assertIn(token,native)
        self.assertNotIn("CREATE_ALWAYS",native)
        self.assertNotIn("TRUNCATE_EXISTING",native)
        self.assertIn("fxfile::filecommand::execute(request)",controller)
        self.assertIn("새 텍스트 문서.txt",commands)
        self.assertIn("validTextDocumentLeaf(request.name)",commands)
        self.assertIn("kind==fxfile::filecommand::Kind::CreateTextFile?2:1",commands)
        self.assertIn("pendingNameAction_==2?16:-1",bar)
        self.assertIn("else if(command==16)",win)
        self.assertIn('make(L"텍스트 문서 (.txt)"',menu)
        for marker in ("create_empty_unicode_text_document",
                       "text_document_never_overwrites_existing",
                       "text_document_denies_traversal",
                       "text_document_denies_reserved_device"):
            self.assertIn(marker,fixture)


class TransferFeedbackContract(unittest.TestCase):
    def test_collision_skip_coroutine_uses_co_return(self):
        body=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        dialog=body.split("winrt::fire_and_forget MainWindow::ConfirmCollision(",1)[1].split(
            "void MainWindow::OnTransferCompleted(",1)[0]
        self.assertIn("choice=co_await dialog.ShowAsync();",dialog)
        self.assertIn("}catch(...){",dialog)
        self.assertIn("ContentDialogResult choice=ContentDialogResult::None;",dialog)
        self.assertIn("mFileOperations.skipCollisions(",dialog)
        self.assertIn("co_return;",dialog)
        self.assertNotIn("\n  return;",dialog)
        self.assertIn("mFileOperations.confirmCollision(",dialog)

    def test_confirmation_cancel_and_partial_cancel_have_feedback(self):
        body=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        start=body.split("void MainWindow::ApplyTransferStartStatus(",1)[1].split(
            "void MainWindow::StartTransfer(",1)[0]
        completion=body.split("void MainWindow::OnTransferCompleted(",1)[1].split(
            "void MainWindow::OnWindowsCopy(",1)[0]
        self.assertIn("status==Start::Cancelled",start)
        self.assertIn("파일 작업 확인을 취소했습니다.",start)
        self.assertIn("completion.report.aborted",completion)
        self.assertIn("completion.report.error==ERROR_CANCELLED",completion)
        self.assertIn("일부 항목이 처리됐을 수 있습니다.",completion)
        self.assertIn("rememberOrigin(detail);",completion)
        self.assertIn("completion.touchedFolders",completion)
        self.assertIn("state.fileOperationNotice=message;",completion)
        self.assertIn("if(originActive)StatusText().Text(hstring(detail));",completion)
        self.assertIn("if(originActive)StatusText().Text(hstring(message));",completion)
        self.assertIn(
            "if(completion.context.windowTabIdentity==ActiveWindowTab().identity)",
            completion
        )
        self.assertIn("fxfile::shellnav::NavigationAction::Refresh",completion)
        self.assertIn("if(disposition==Disposition::StaleContext)",completion)

    def test_transfer_notice_cleared_only_after_an_actual_launch(self):
        source=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        start=source.split("void MainWindow::ApplyTransferStartStatus(",1)[1].split(
            "void MainWindow::StartTransfer(",1)[0]
        entry=source.split("void MainWindow::StartTransfer(",1)[1].split(
            "winrt::fire_and_forget MainWindow::ConfirmRecycle(",1)[0]
        self.assertIn("if(status==Start::Started){",start)
        self.assertIn("ActiveWindowTab().fileOperationNotice.clear();",start)
        self.assertLess(start.index("if(status==Start::Started){"),
                        start.index("ActiveWindowTab().fileOperationNotice.clear();"))
        self.assertNotIn("fileOperationNotice.clear()",entry)
        self.assertIn("if(mFileOperations.pendingConfirmationToken()){",entry)
        self.assertIn("mFileOperations.requestTransfer(",entry)

    def test_transfer_outcome_is_preserved_for_inactive_origin_workspace(self):
        source=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        body=source.split("void MainWindow::OnTransferCompleted(",1)[1].split(
            "bool MainWindow::CopySelectedToWindowsClipboard(",1)[0]
        stale=body.split("if(disposition==Disposition::StaleContext){",1)[1].split(
            "if(disposition==Disposition::Failed){",1)[0]
        self.assertIn("completion.report.error==ERROR_SUCCESS",stale)
        self.assertIn("!completion.report.aborted",stale)
        self.assertIn("일부 항목이 처리됐을 수 있습니다.",stale)
        self.assertIn("std::to_wstring(completion.report.error)",stale)
        self.assertIn("completion.skippedCollisions",stale)
        self.assertIn("rememberOrigin(notice);",stale)
        self.assertIn("if(originActive)StatusText().Text(hstring(notice));",stale)
        self.assertNotIn("QueuePidl(",stale)
        success=body.split("if(disposition==Disposition::Failed){",1)[1]
        self.assertIn("rememberOrigin(message);",success)
        self.assertLess(success.index("rememberOrigin(message);"),
                        success.index("if(originActive)StatusText().Text(hstring(message));"))
        self.assertIn("state.identity==completion.context.windowTabIdentity",body)
        self.assertIn("state.fileOperationNotice=message;",body)


class AsyncWindowTabOwnershipContract(unittest.TestCase):
    def test_file_operations_reject_other_window_tab_results(self):
        header=(APP/"file_operation_controller.h").read_text(encoding="utf-8-sig")
        controller=(APP/"file_operation_controller.cpp").read_text(encoding="utf-8-sig")
        ui=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        self.assertIn("std::uint64_t windowTabIdentity=0;",header)
        self.assertIn("a.windowTabIdentity==b.windowTabIdentity",controller)
        self.assertIn("context.windowTabIdentity=ActiveWindowTab().identity;",ui)
        self.assertIn("sameContext(completion.context,liveContext)",controller)
        self.assertIn("sameContext(pending.context,liveContext)",controller)
        self.assertIn("completion.report.error==ERROR_ALREADY_EXISTS",controller)
        self.assertIn("!completion.report.aborted",controller)
        self.assertIn(
            "completion.request.collision==fxfile::shelltransfer::Collision::Reject",
            controller
        )


class SkipExistingTransferContract(unittest.TestCase):
    def test_skip_is_local_preflight_only_and_revalidates_remaining(self):
        header=(APP/"file_operation_controller.h").read_text(encoding="utf-8-sig")
        controller=(APP/"file_operation_controller.cpp").read_text(encoding="utf-8-sig")
        for token in (
            "AllSkipped",
            "skipCollisions(",
            "skippedCollisions=0",
        ):
            self.assertIn(token,header)
        body=controller.split(
            "FileOperationController::skipCollisions(",1)[1].split(
            "FileOperationController::StartStatus FileOperationController::launchTransfer(",1
        )[0]
        for token in (
            "SourceMode::Filesystem",
            "DestinationMode::Filesystem",
            "sameContext(pending.context,liveContext)",
            "CompareStringOrdinal(",
            "if(skipped!=pending.collisions.size())",
            "if(remaining.empty()){",
            "skipped=totalSkipped;",
            "return StartStatus::AllSkipped;",
            "launchTransfer(std::move(pending.request)",
        ):
            self.assertIn(token,body)
        self.assertNotIn("DeleteFileW(",body)
        self.assertNotIn("GetFileAttributesW(",body)
        self.assertNotIn("std::thread(",body)
        self.assertIn("value.skippedCollisions=skippedCollisions;",controller)
        self.assertIn("completion.report.collisions",controller)
        # A reduced request can collide again before the Shell operation.
        # Keep earlier skips across a second dialog or a KeepBoth decision.
        self.assertIn("std::size_t skippedCollisions=0;",controller)
        self.assertIn("completion.report.collisions,completion.skippedCollisions",controller)
        self.assertIn("pending.skippedCollisions+skipped",controller)
        self.assertIn("skipped=totalSkipped;",controller)
        self.assertIn("return StartStatus::AllSkipped;",controller)
        self.assertIn("std::move(completion),totalSkipped",controller)
        self.assertIn("std::move(completion),pending.skippedCollisions",controller)

    def test_ui_shows_explicit_choices_and_never_guesses_success_counts(self):
        body=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        section=body.split("MainWindow::ConfirmCollision(",1)[1].split(
            "void MainWindow::OnTransferCompleted(",1
        )[0]
        self.assertIn('SecondaryButtonText(L"충돌 항목 건너뛰기")',section)
        self.assertIn("ContentDialogResult::Secondary",section)
        self.assertIn("mFileOperations.skipCollisions(",section)
        self.assertIn("mFileOperations.confirmCollision(",section)
        self.assertIn("if(status==FileOperationController::StartStatus::AllSkipped)",section)
        self.assertIn("completion.skippedCollisions",body)
        self.assertIn("std::size_t previouslySkipped",body)
        self.assertIn("completion.skippedCollisions,",body)
        self.assertIn("mFileOperations.pendingConfirmationToken());",body)
        self.assertIn("이전 확인에서 충돌 ",body)
        self.assertIn("일부 항목이 처리됐을 수 있습니다.",body)
        self.assertIn("rememberOrigin(detail);",body)
        self.assertNotIn("report.queued-report.completed",body)


if __name__=="__main__":
    unittest.main()

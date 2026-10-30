"""Current file-command, transfer, clipboard and drag safety contracts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class FileOperationContracts(unittest.TestCase):
    def test_native_file_command_rejects_traversal_devices_and_overwrite(self):
        body = read("src/base/file_command_core.cpp")
        for token in (
            "validLeaf",
            "ERROR_INVALID_NAME",
            "ERROR_ALREADY_EXISTS",
            "CreateDirectoryW",
            "MoveFileW",
            "parent_path()!=folder",
        ):
            self.assertIn(token, body)
        self.assertNotIn("MoveFileExW", body)
        self.assertNotIn("DeleteFileW", body)

    def test_shell_transfer_core_is_bounded_and_requires_recycle_consent(self):
        header = read("src/base/shell_transfer_core.h")
        body = read("src/base/shell_transfer_core.cpp")
        for token in (
            "Kind { Copy, Move, Recycle }",
            "Collision { Reject, KeepBoth }",
            "SourceMode { Filesystem, ShellProvider }",
            "kMaxProviderParsingUnits=4096",
            "kMaxProviderPidlBytes=32768",
            "kMaxProviderPidlBytesTotal=1024*1024",
            "recycleConfirmed=false",
            "IFileOperation",
            "FOFX_RECYCLEONDELETE",
            "FOF_RENAMEONCOLLISION",
            "kMaxItems=1024",
            "kMaxSourcePathUnits=1024*1024",
            "request.sources.size()>kMaxItems",
            "!request.recycleConfirmed",
            "ERROR_ALREADY_EXISTS",
            "descendant(item,dest)",
            "FILE_ATTRIBUTE_REPARSE_POINT",
            "state_.cancel.load",
            "E_ABORT",
        ):
            self.assertIn(token, header + body)
        for forbidden in ("CWnd", "XamlRoot", "Windows::ApplicationModel",
                          "RemoveDirectoryW", "SHFileOperation"):
            self.assertNotIn(forbidden, header + body)
        # Only the unique, request-created staging pathname may be deleted.
        # Original sources and published destination paths remain protected.
        self.assertEqual(1, body.count("::DeleteFileW("))
        self.assertIn("::DeleteFileW(stage.c_str())", body)

    def test_native_shell_per_item_failures_never_report_aggregate_success(self):
        core = read("src/base/shell_transfer_core.cpp")
        fixture = read("tests/winui/m22/m22_transfer_fixture.cpp")
        self.assertIn("std::atomic<HRESULT> firstFailure_{S_OK}", core)
        self.assertIn("HRESULT firstFailure() const noexcept", core)
        for callback in ("PostCopyItem", "PostMoveItem", "PostDeleteItem",
                         "FinishOperations"):
            self.assertIn("HRESULT STDMETHODCALLTYPE " + callback, core)
        self.assertIn("return completed(hr);", core)
        self.assertIn("sink->firstFailure()", core)
        self.assertIn("if(operation&&performed)", core)
        self.assertIn("operation->GetAnyOperationsAborted(&anyAborted)", core)
        self.assertIn("FAILED(hr)?code(hr)", core)
        self.assertIn("sharing_violation_copy_reports_failure_and_preserves_source",
                      fixture)
        self.assertIn("sharing_violation_move_reports_failure_and_preserves_source",
                      fixture)

    def test_aborted_transfer_is_never_reported_as_success(self):
        controller = read("app/winui/file_operation_controller.cpp")
        accept = controller.split(
            "FileOperationController::acceptTransfer(", 1)[1].split(
            "FileOperationController::StartStatus FileOperationController::startFileCommand(", 1
        )[0]
        # A helper may supply an aborted flag despite a success error code.
        # Fail closed, rather than claiming all requested items completed.
        self.assertIn("completion.report.aborted||", accept)
        self.assertIn("completion.report.error!=ERROR_SUCCESS", accept)
        self.assertLess(accept.index("completion.report.aborted||"),
                        accept.index("return TransferDisposition::Succeeded;"))
        self.assertLess(accept.index("return TransferDisposition::Failed;"),
                        accept.index("return TransferDisposition::Succeeded;"))
        self.assertIn("!completion.report.aborted&&", accept)
        transfer = read("app/winui/m22_transfers.cpp")
        self.assertIn("completion.report.aborted||", transfer)
        self.assertIn("일부 항목이 처리됐을 수 있습니다.", transfer)
        self.assertIn("rememberOrigin(detail);", transfer)

    def test_regular_fixed_file_copy_commits_only_completed_staging(self):
        core = read("src/base/shell_transfer_core.cpp")
        fixture = read("tests/winui/m22/m22_transfer_fixture.cpp")
        wrapper = read("tests/winui/m22/test_native.py")
        self.assertIn("bool stageEligible(Request const& task)", core)
        self.assertIn("task.kind!=Kind::Copy", core)
        self.assertIn("task.collision!=Collision::Reject", core)
        self.assertIn("FILE_ATTRIBUTE_REPARSE_POINT", core)
        self.assertIn("::GetDriveTypeW(sourceRoot.c_str())!=DRIVE_FIXED", core)
        self.assertIn("::GetDriveTypeW(destRoot.c_str())!=DRIVE_FIXED", core)
        self.assertIn("COPY_FILE_FAIL_IF_EXISTS", core)
        self.assertIn("::MoveFileExW(stage.c_str(),target.c_str(),MOVEFILE_WRITE_THROUGH)", core)
        self.assertIn("::DeleteFileW(stage.c_str())", core)
        self.assertIn("if(canceled(progress))", core)
        self.assertNotIn("MOVEFILE_REPLACE_EXISTING", core)
        self.assertIn("committed_local_copy_has_no_partial_stage", fixture)
        self.assertIn("M22_REAL_STAGED_KILLED_COPY_FINAL_TARGET_ABSENT", wrapper)
        self.assertIn("M22_REAL_STAGED_MID_COPY_CANCEL_SOURCE_UNCHANGED", wrapper)
        self.assertIn("M22_STAGED_LATE_TARGET_COLLISION_PRESERVED_BYTES", wrapper)
        self.assertIn("M22_STAGED_UNRELATED_PARTIAL_NEVER_DELETED", wrapper)
        self.assertIn("M22_STAGED_DENIED_WRITE_SOURCE_PRESERVED", wrapper)
        self.assertIn("M22_STAGED_DENIED_WRITE_NO_DESTINATION", wrapper)
        header = read("src/base/shell_transfer_core.h")
        self.assertIn("bool inspectStageFile(", header)
        self.assertIn("bool sameStageFile(", header)
        probe = core[core.index("bool sameStageFile("):
                     core.index("Report validate(Request")]
        for token in ("FILE_FLAG_OPEN_REPARSE_POINT", "FileIdInfo",
                      "FILE_ATTRIBUTE_REPARSE_POINT",
                      "attributes.nNumberOfLinks!=1",
                      "safeFilesystemFolder(path.parent_path(),Kind::Copy)"):
            self.assertIn(token, probe)
        for forbidden in ("DeleteFileW", "MoveFileExW",
                          "SetFileInformationByHandle"):
            self.assertNotIn(forbidden, probe)
        for scenario in (
            "stage_identity_stable_readonly_snapshot",
            "stage_identity_refuses_multiple_hardlinks",
            "stage_identity_detects_same_path_replacement",
            "stage_identity_rejects_unowned_names_and_unnormalized_paths",
        ):
            self.assertIn(scenario, fixture)

        self.assertIn("M22_LIVE_ACL_AFTER_WRITES_SOURCE_BYTES_PRESERVED", wrapper)
        self.assertIn("M22_LIVE_ACL_AFTER_WRITES_NO_TRUNCATED_FINAL", wrapper)
        self.assertIn("M22_LIVE_ACL_PREEXISTING_DESTINATION_PRESERVED", wrapper)
        self.assertIn("M22_KILLED_STAGE_EXACT_IDENTITY_RECLAIM_TEST_OWNED_ONLY", wrapper)
        self.assertIn("M22_KILLED_STAGE_UNRELATED_PARTIAL_UNTOUCHED", wrapper)
        self.assertIn("M22_DENIED_MOVE_PRESERVES_ORIGINAL_SOURCE", wrapper)
        self.assertIn("--owned-move-deny", fixture)
        self.assertIn("recursive_copy_nested_lock_reports_failure_and_preserves_source", fixture)
        self.assertIn("recursive_copy_preflight_cancel_preserves_entire_source", fixture)
        self.assertIn("--owned-stage-race", fixture)
        self.assertIn("--owned-stage-deny", fixture)

    def test_partial_failure_notice_survives_navigation_refresh(self):
        ui = read("app/winui/MainWindow.xaml.cpp")
        header = read("app/winui/MainWindow.xaml.h")
        workspace = read("app/winui/window_tab_state.h")
        transfer = read("app/winui/m22_transfers.cpp")
        self.assertIn("std::wstring fileOperationNotice{};", workspace)
        self.assertNotIn("mTransferFailureNotice", header)
        self.assertIn("state.fileOperationNotice=message;", transfer)
        self.assertIn("ActiveWindowTab().fileOperationNotice.clear();", transfer)
        self.assertIn("completion.context.windowTabIdentity", transfer)
        self.assertIn("if(originActive)StatusText().Text(hstring(detail));", transfer)
        self.assertIn("if(originActive)StatusText().Text(hstring(message));", transfer)
        self.assertIn("completed.action==Action::Refresh&&", ui)
        self.assertIn("!ActiveWindowTab().fileOperationNotice.empty()", ui)
        self.assertIn(
            "StatusText().Text(hstring(ActiveWindowTab().fileOperationNotice));",
            ui
        )
        self.assertIn("ActiveWindowTab().fileOperationNotice.clear();", ui)
        self.assertIn("if(!state.fileOperationNotice.empty())", ui)

    def test_selected_row_activates_command_pane(self):
        source = read("app/winui/MainWindow.xaml.cpp")
        begin = source.index("void MainWindow::OnFileSelectionChanged(")
        end = source.index("void MainWindow::OnFileSelectionKeyUp(", begin)
        body = source[begin:end]
        self.assertIn("if(mPopulatingFileLists)return;", body)
        # F05 disclosure headings must never become command targets.
        # Only a newly selected real file row may activate its pane.
        self.assertIn("bool newlySelectedFile=false;", body)
        self.assertIn("for(auto const& candidate:args.AddedItems())", body)
        # Stale selected rows may still carry a valid Shell Tag.
        # Current route/tab, workspace owner and actual ListView membership
        # must be checked before activating the command pane.
        for guard in (
            "visible.visibleRoute!=pane.routeIds[pane.active]",
            "visible.visibleTab!=pane.active",
            "ActiveWindowTab().identity",
            "if(!ownedPresentation)return;",
            "if(!row||!row.Tag())continue;",
            "view.Items().IndexOf(candidate,currentIndex)",
        ):
            self.assertIn(guard, body)
        self.assertIn("if(newlySelectedFile&&ActiveWindowTab().model.activePane!=side)", body)
        self.assertIn("ActivatePane(side);", body)

    def test_partial_failure_refreshes_visible_touched_folders(self):
        transfer = read("app/winui/m22_transfers.cpp")
        fixture = read("tests/winui/m22/m22_transfer_fixture.cpp")
        start = transfer.index("void MainWindow::OnTransferCompleted(")
        end = transfer.index("bool MainWindow::CopySelectedToWindowsClipboard(",
                             start)
        body = transfer[start:end]
        self.assertLess(
            body.index("Disposition::NeedsCollisionConfirmation"),
            body.index("QueuePidl(side"))
        self.assertLess(body.index("QueuePidl(side"),
                        body.index("Disposition::StaleContext"))
        self.assertLess(body.index("QueuePidl(side"),
                        body.index("Disposition::Failed"))
        self.assertIn("completion.touchedFolders.begin()", body)
        self.assertIn("일부 항목이 처리됐을 수 있습니다.", body)
        for scenario in (
            "batch_partial_copy_failure_preserves_both_sources",
            "batch_partial_move_failure_preserves_remaining_source",
        ):
            self.assertIn(scenario, fixture)

    def test_isolated_filesystem_collision_skip_uses_exact_readonly_recheck(self):
        core = read("src/base/shell_transfer_core.cpp")
        fixture = read("tests/winui/m22/m22_transfer_fixture.cpp")
        host = core.split("Report executeIsolated(", 1)[1].split(
            "int runIsolatedHelper(", 1
        )[0]
        self.assertIn("filesystemCollisionReported=true;", host)
        self.assertIn("auto observed=validate(task);", host)
        self.assertIn("result.collisions.swap(observed.collisions);", host)
        self.assertIn("observed.queued==result.queued", host)
        self.assertIn("task.collision==Collision::Reject", host)
        self.assertIn("result.error==ERROR_ALREADY_EXISTS&&!result.aborted", host)
        self.assertLess(host.index("::GetExitCodeProcess("),
                        host.index("auto observed=validate(task);"))
        # A wire collision flag must never become a filesystem path "".
        self.assertIn("task.sourceMode!=SourceMode::Filesystem||", host)
        self.assertNotIn("::DeleteFileW(", host)
        self.assertNotIn("::MoveFileExW(", host)
        for token in (
            "--owned-isolated-collision",
            "--owned-isolated-move-collision",
            "M22_ISOLATED_COLLISION_PATH=",
            "M22_ISOLATED_SKIP_PRESERVES_COLLISION=",
            "M22_ISOLATED_MOVE_COLLISION_PATH=",
            "M22_ISOLATED_MOVE_SKIP_PRESERVES_SOURCE=",
            "task.kind=moving?Kind::Move:Kind::Copy;",
            "read(target)==\"existing-destination\"",
            "read(taken)==\"original-source\"",
            "(moving?!fs::exists(free):read(free)==\"remaining-source\")",
            "task.sources={free.native()};",
        ):
            self.assertIn(token, fixture)

    def test_network_copy_move_are_isolated_while_recycle_stays_local_only(self):
        header = read("src/base/shell_transfer_core.h")
        body = read("src/base/shell_transfer_core.cpp")
        fixture = read("tests/winui/m22/m22_transfer_fixture.cpp")
        controller = read("app/winui/file_operation_controller.cpp")
        helper = read("app/winui/helper/FlyShellIsolationHelper.cpp")
        project = read("app/winui/helper/FlyShellIsolationHelper.project-template.xml")
        joined = header + body
        for token in (
            "supportsDriveType(Kind kind,UINT driveType)",
            "driveType==DRIVE_FIXED||driveType==DRIVE_REMOVABLE||",
            "driveType==DRIVE_REMOTE",
            "case Kind::Recycle:",
            "transferDriveRoot(",
            'value.rfind(L"\\\\\\\\?\\\\",0)==0',
            'value.rfind(L"\\\\\\\\.\\\\",0)==0',
            "safeFilesystemFolder(parent,request.kind)",
            "safeFilesystemFolder(dest,request.kind)",
            "validateProviderCopy(",
            "ILIsParent(parent,child,TRUE)",
            "sourceParentPidl",
            "sourcePidls",
            "SHCreateItemFromIDList",
            "SFGAO_CANCOPY",
            "SIGDN_PARENTRELATIVEEDITING",
            "SourceMode::ShellProvider",
            "executeIsolated(Request const& task,Progress& progress)",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
            "kTransferCancelGraceMs",
            "--file-transfer",
        ):
            self.assertIn(token, joined + helper)
        self.assertIn("shell_transfer_core.cpp", project)
        self.assertIn("file_command_core.cpp", project)
        self.assertIn("shelltransfer::executeIsolated(request,*progress)", controller)
        self.assertIn("shelltransfer::execute(request,*progress)", controller)
        for token in (
            "copy_accepts_remote_drive",
            "move_accepts_remote_drive",
            "parse_standard_unc_share_root",
            "parse_drive_letter_root",
            "reject_extended_and_device_roots",
            "recycle_rejects_remote_drive",
            "actual_unc_copy_destination",
            "actual_unc_move_source",
            "unc_recycle_remains_rejected",
            "reject_extended_unc_namespace",
        ):
            self.assertIn(token, fixture)
        self.assertNotIn("copy_rejects_remote_drive", fixture)
        self.assertNotIn("move_rejects_remote_drive", fixture)

    def test_ui_routes_commands_through_async_controller_and_refreshes_touched_panes(self):
        command = read("app/winui/m21_commands.cpp")
        transfer = read("app/winui/m22_transfers.cpp")
        controller = read("app/winui/file_operation_controller.cpp")
        for token in (
            "mFileOperations.startFileCommand",
            "mFileOperations.requestTransfer",
            "mFileOperations.cancel",
            "get_weak",
            "DispatcherQueue",
        ):
            self.assertIn(token, command + transfer)
        for token in (
            "filecommand::execute",
            "shelltransfer::execute",
            "state_->progress",
            "completion.ticket!=state_->epoch",
            "sameContext(",
            "visibleShellFolder",
            "SourceMode::Filesystem",
            "touched.push_back(request.sourceParent)",
            "touched.push_back(request.destination)",
            "TransferDisposition::Succeeded",
        ):
            self.assertIn(token, controller)
        self.assertIn("completion.touchedFolders.begin()", transfer)
        self.assertIn("QueuePidl(side", transfer)
        for token in (
            "SourceMode::ShellProvider",
            "snapshot.parsingName",
            "copyPidlBytes(snapshot.folder.get(),req.sourceParentPidl)",
            "snapshot.children[resident].id.get()",
            "kMaxProviderParsingUnits",
            "가상 Shell/provider 항목은 현재 반대쪽 실제 폴더로 복사만 지원합니다.",
        ):
            self.assertIn(token, transfer)
        self.assertNotIn("indexed->attributes&SFGAO_CANCOPY", transfer)
        self.assertIn(
            "item->GetAttributes(SFGAO_CANCOPY,&attrs)",
            read("src/base/shell_transfer_core.cpp"),
        )

    def test_create_folder_shortcuts_reuse_existing_file_command_identity(self):
        main = read("app/winui/MainWindow.xaml.cpp")
        command = read("app/winui/m21_commands.cpp")
        # Inspect the new-folder command itself. Unrelated tab refreshes and
        # the independently supported F11 window shortcut may precede it.
        start = main.index("const bool createFolderShortcut=")
        constructor = main[start:main.index("if(!control)return;", start)]
        self.assertIn("VirtualKey::N", constructor)
        self.assertNotIn("VirtualKey::F11", constructor)
        self.assertIn("!alt&&control&&shift&&", constructor)
        self.assertEqual(
            1,
            constructor.count(
                "fxfile::filecommand::Kind::CreateFolder"
            ),
        )
        self.assertIn("BeginFileNameCommand(", constructor)
        self.assertNotIn("CreateDirectoryW", constructor)
        self.assertIn("if(mFileOperations.busy()||mFileOperations.pendingConfirmationToken())", command)
        self.assertIn(
            "const int side=ActiveWindowTab().model.activePane;",
            command,
        )
        self.assertIn("mFileOperations.startFileCommand", command)

    def test_clipboard_wire_is_unicode_bounded_and_cut_errors_do_not_copy(self):
        body = read("src/base/shell_clipboard_core.cpp")
        for token in (
            "CF_HDROP",
            "Preferred DropEffect",
            "OpenClipboard(owner)",
            "SetClipboardData",
            "DragQueryFileW",
            "shelltransfer::kMaxSourcePathUnits",
            "MaxItems=shelltransfer::kMaxItems",
            "drop.fWide",
            "payload.paths.size()>MaxItems",
            "CompareStringOrdinal",
            "return ERROR_NOT_SUPPORTED;",
            "if(answer==ERROR_SUCCESS)answer=::GetLastError();",
        ):
            self.assertIn(token, body)
        for forbidden in ("winrt::", "CWnd"):
            self.assertNotIn(forbidden, body)

    def test_file_row_drag_owns_pointer_threshold_and_programmatic_start(self):
        main = read("app/winui/MainWindow.xaml.cpp")
        header = read("app/winui/MainWindow.xaml.h")
        drag = read("app/winui/m23_drag.cpp")
        for token in (
            "OnFileRowPointerPressed",
            "PollFileRowPointerDrag",
            "StartFileRowDragAsync",
            "OnFileRowPointerReleased",
        ):
            self.assertIn(token, main + header + drag)
        for token in (
            "SM_CXDRAG",
            "SM_CYDRAG",
            "IsLeftButtonPressed()",
            "GetAsyncKeyState(VK_LBUTTON)",
            "GetCursorPos(&cursor)",
            "PointerPoint::GetCurrentPoint(pointerId)",
            "StartDragAsync(point)",
            "ResetFileRowPointerDrag()",
        ):
            self.assertIn(token, drag)
        for token in (
            "PointerPressedEvent()",
            "PointerReleasedEvent()",
            "PointerCanceledEvent()",
            "box_value(PointerEventHandler",
            "}),true);",
        ):
            self.assertIn(token, main)
        self.assertNotIn("PointerMovedEvent()", main[main.index("row.CanDrag(true);"):
                                                  main.index("view.Items().Append(row);")])
        self.assertIn("row.DragStarting(", main)

    def test_clipboard_paste_and_drag_share_the_transfer_core(self):
        transfer = read("app/winui/m22_transfers.cpp")
        drag = read("app/winui/m23_drag.cpp")
        xaml = read("app/winui/MainWindow.xaml")
        for token in (
            "shellclipboard::read",
            "CopySelectedToWindowsClipboard",
            "PasteFromWindowsClipboard()",
            "StartTransfer(std::move(request))",
        ):
            self.assertIn(token, transfer)
        for token in (
            "GetStorageItemsAsync",
            "DragItemsStartingEventArgs",
            "args.GetDeferral()",
            "mPrivateDragToken.clear()",
            "DataPackageOperation::Copy",
            "StartTransfer(std::move(request))",
        ):
            self.assertIn(token, drag)
        self.assertEqual(2, xaml.count('DragItemsStarting="OnFileDragItemsStarting"'))
        self.assertEqual(2, xaml.count('Drop="OnFileDrop"'))

    def test_owned_native_fixtures_do_not_touch_global_clipboard_or_recycle_bin(self):
        clipboard = read("tests/winui/m23/m23_native_fixture.cpp")
        recycle = read("tests/winui/m22/m22_transfer_fixture.cpp")
        self.assertNotIn("shellclipboard::write(", clipboard)
        self.assertNotIn("shellclipboard::read(", clipboard)
        self.assertIn("reject_missing_second_terminal_unicode_null", clipboard)
        self.assertIn(
            "recycle_plan" if "recycle_plan" in recycle else "recycle_requires_explicit_consent",
            recycle,
        )
        self.assertNotIn("execute(r,progress); // recycle", recycle)


if __name__ == "__main__":
    unittest.main()

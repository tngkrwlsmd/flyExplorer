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
        # Unjournaled legacy path still uses the original no-replace
        # MoveFileExW, while private journalled copies pin file handles.
        self.assertIn("::MoveFileExW(", core)
        self.assertIn("stage.c_str(),target.c_str(),MOVEFILE_WRITE_THROUGH", core)
        self.assertIn("publishActiveBoundStage(", core)
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

    def test_durable_stage_receipt_is_non_destructive_and_not_cleanup_authority(self):
        header = read("src/base/stage_receipt_core.h")
        core = read("src/base/stage_receipt_core.cpp")
        fixture = read("tests/winui/m22/m22_transfer_fixture.cpp")
        native = read("tests/winui/m22/test_native.py")
        app_project = read("app/winui/flyExplorer.project-template.xml")
        for symbol in ("writeStageReceipt", "readStageReceipt",
                       "receiptMatchesStage", "StageOwnershipReceipt",
                       "createPrivateStageReceiptDirectory",
                       "isPrivateStageReceiptDirectory",
                       "inspectReceiptCreator", "ReceiptCreatorState",
                       "writeBoundStageReceipt",
                       "prepareUserStageReceiptDirectory",
                       "markStageCopyCompleted", "markStageCopyPublished",
                       "inspectStageReceiptState", "StageReceiptState"):
            self.assertIn(symbol, header)
        for marker in ("CREATE_NEW", "FILE_FLAG_WRITE_THROUGH",
                       "FlushFileBuffers", "FILE_FLAG_OPEN_REPARSE_POINT",
                       "FileIdInfo", "checksum(raw)", "inspectStageFile",
                       "sameStageFile", "GetSecurityInfo", "SE_DACL_PROTECTED",
                       "ConvertStringSecurityDescriptorToSecurityDescriptorW",
                       "CREATE_NO_WINDOW", "WaitForSingleObject"):
            if marker == "CREATE_NO_WINDOW":
                self.assertIn(marker, fixture)
                continue
            self.assertIn(marker, core + read("src/base/shell_transfer_core.cpp"))
        for destructive in ("DeleteFileW", "RemoveDirectoryW", "MoveFileExW",
                            "SetFileInformationByHandle"):
            self.assertNotIn(destructive, core)
        self.assertIn(
            '<ClCompile Include="..\\..\\src\\base\\stage_receipt_core.cpp">\n'
            '      <PrecompiledHeader>NotUsing</PrecompiledHeader>',
            app_project)
        self.assertIn("expected=62", native)
        self.assertIn("expected=66", native)
        helper_project = read(
            "app/winui/helper/FlyShellIsolationHelper.project-template.xml")
        self.assertIn("stage_receipt_core.cpp", helper_project)
        transfer = read("src/base/shell_transfer_core.cpp")
        self.assertIn("writeBoundStageReceipt(", transfer)
        self.assertIn("prepareUserStageReceiptDirectory(", transfer)
        self.assertIn("progress.receiptDirectory", transfer)
        self.assertIn("!journalReady", transfer)
        self.assertIn("markStageCopyCompleted(", transfer)
        self.assertIn("markStageCopyPublished(", transfer)
        # Journalled active Copy pins the source file HANDLE and inspects
        # the parent. Win32 re-resolves the absolute target path, so this
        # contract does not imply handle-anchored destination protection.
        # The receipt primitive itself remains strictly non-mutating.
        self.assertIn("publishActiveBoundStage(", transfer)
        self.assertIn("SetFileInformationByHandle(", transfer)
        self.assertIn("FileRenameInfo,rename", transfer)
        self.assertIn("rename->RootDirectory=nullptr;", transfer)
        self.assertIn("const std::wstring exactTarget=destination.native();", transfer)
        self.assertIn("FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE", transfer)
        self.assertIn("rename->ReplaceIfExists=FALSE;", transfer)
        self.assertIn("GetFinalPathNameByHandleW(", transfer)
        self.assertIn("struct DirectoryPins final", transfer)
        self.assertIn("FILE_SHARE_READ|FILE_SHARE_WRITE,", transfer)
        self.assertIn("g_directoryRenameProbe", transfer)
        self.assertIn("setDirectoryRenameProbeForTest", header)
        self.assertIn("receipt_active_publish_pins_ancestor_against_rename", fixture)
        native_project = read(
            "tests/winui/m22/FlyM22ShellTransferContracts.project-template.xml")
        self.assertIn("FLY_M22_TEST_DIRECTORY_RENAME_LOCK", native_project)
        self.assertNotIn("FLY_M22_TEST_DIRECTORY_RENAME_LOCK", helper_project)
        self.assertNotIn("FLY_M22_TEST_DIRECTORY_RENAME_LOCK", app_project)
        self.assertIn("--owned-stage-race-receipt", fixture)
        self.assertIn("FILE_FLAG_OPEN_REPARSE_POINT", transfer)
        self.assertIn("PublicationUnconfirmed", core)
        self.assertIn("PhaseRead::Invalid", core)
        self.assertIn("--owned-stage-kill-receipt", fixture)
        self.assertIn("--receipt-verify-killed", fixture)
        self.assertIn("--receipt-inspect-state", fixture)
        self.assertIn("--owned-helper-ipc-copy", fixture)
        self.assertIn("--owned-helper-ipc-untrusted", fixture)
        self.assertIn("M22_ISOLATED_HELPER_IPC_UNTRUSTED_STORE", fixture)
        self.assertIn("executeIsolated(request,progress)", fixture)
        self.assertIn("FLY_M22_OWNED_RECEIPT_STORE", transfer)
        self.assertIn("#if defined(FLY_M22_TEST_ISOLATED_RECEIPT_STORE)", transfer)
        self.assertIn("#else\n  if(stageEligible(task))", transfer)
        self.assertIn("FlyM22OwnedHelper", helper_project)
        self.assertIn("FLY_M22_TEST_ISOLATED_RECEIPT_STORE", helper_project)
        self.assertIn("--receipt-create-private", fixture)
        for scenario in ("receipt_roundtrip_flush_and_exact_stage_identity",
                         "receipt_create_new_never_overwrites_existing",
                         "receipt_rejects_same_path_file_replacement",
                         "receipt_corruption_fails_closed_without_file_mutation",
                         "receipt_refuses_untrusted_inherited_acl_store",
                         "receipt_private_owner_dacl_created_without_acl_reset",
                         "receipt_creator_alive_and_pid_reuse_fail_closed",
                         "receipt_creator_exited_without_stage_mutation",
                         "live_staged_copy_callback_durable_receipt_before_publish",
                         "live_staged_copy_refuses_untrusted_receipt_directory",
                         "receipt_phase_initial_copying_readonly",
                         "receipt_phase_completed_immutable_write_once",
                         "receipt_phase_rename_without_published_marker_ambiguous",
                         "receipt_phase_published_same_identity_write_once",
                         "receipt_phase_published_target_replacement_is_inconsistent",
                         "receipt_phase_corrupt_transition_rejected_readonly",
                         "receipt_zero_byte_staged_copy_published_with_bound_identity",
                         "receipt_active_publish_pins_ancestor_against_rename"):
            self.assertIn(scenario, fixture)

    def test_partial_failure_notice_survives_navigation_refresh(self):
        ui = read("app/winui/MainWindow.xaml.cpp")
        header = read("app/winui/MainWindow.xaml.h")
        transfer = read("app/winui/m22_transfers.cpp")
        self.assertIn("std::wstring mTransferFailureNotice{};", header)
        self.assertIn("mTransferFailureNotice=detail;", transfer)
        self.assertIn("mTransferFailureNotice.clear();", transfer)
        self.assertIn("completed.action==Action::Refresh&&", ui)
        self.assertIn("!mTransferFailureNotice.empty()", ui)
        self.assertIn("StatusText().Text(hstring(mTransferFailureNotice));", ui)
        self.assertIn("mTransferFailureNotice.clear();", ui)

    def test_selected_row_activates_command_pane(self):
        source = read("app/winui/MainWindow.xaml.cpp")
        begin = source.index("void MainWindow::OnFileSelectionChanged(")
        end = source.index("void MainWindow::OnFileSelectionKeyUp(", begin)
        body = source[begin:end]
        self.assertIn("if(mPopulatingFileLists)return;", body)
        self.assertIn("args.AddedItems().Size()!=0", body)
        self.assertIn("ActiveWindowTab().model.activePane!=side", body)
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
        constructor = main[
            main.index("RootShell().PreviewKeyDown("):
            main.index("RefreshWindowTabs();")
        ]
        self.assertIn("VirtualKey::N", constructor)
        self.assertNotIn("VirtualKey::F11", constructor)
        self.assertIn("VK_CONTROL", constructor)
        self.assertIn("VK_SHIFT", constructor)
        self.assertIn("VK_MENU", constructor)
        self.assertEqual(
            1,
            constructor.count(
                "fxfile::filecommand::Kind::CreateFolder"
            ),
        )
        self.assertIn("BeginFileNameCommand(", constructor)
        self.assertNotIn("CreateDirectoryW", constructor)
        self.assertIn("if(mFileOperations.busy())", command)
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

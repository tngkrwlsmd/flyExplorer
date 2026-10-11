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
                          "DeleteFileW", "RemoveDirectoryW", "SHFileOperation"):
            self.assertNotIn(forbidden, header + body)

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

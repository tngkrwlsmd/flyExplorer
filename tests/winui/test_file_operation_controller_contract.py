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
            "recycleConfirmed=false",
            "IFileOperation",
            "FOFX_RECYCLEONDELETE",
            "FOF_RENAMEONCOLLISION",
            "request.sources.size()>32",
            "!request.recycleConfirmed",
            "ERROR_ALREADY_EXISTS",
            "descendant(item,dest)",
            "FILE_ATTRIBUTE_REPARSE_POINT",
            "state_.cancel.load",
            "E_ABORT",
        ):
            self.assertIn(token, header + body)
        for forbidden in ("CWnd", "XamlRoot", "Windows::ApplicationModel"):
            self.assertNotIn(forbidden, header + body)

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
            "touched.push_back(request.sourceParent)",
            "touched.push_back(request.destination)",
            "TransferDisposition::Succeeded",
        ):
            self.assertIn(token, controller)
        self.assertIn("completion.touchedFolders.begin()", transfer)
        self.assertIn("QueuePidl(side", transfer)

    def test_create_folder_shortcuts_reuse_existing_file_command_identity(self):
        main = read("app/winui/MainWindow.xaml.cpp")
        command = read("app/winui/m21_commands.cpp")
        constructor = main[
            main.index("RootShell().PreviewKeyDown("):
            main.index("RefreshWindowTabs();")
        ]
        self.assertIn("VirtualKey::N", constructor)
        self.assertIn("VirtualKey::F11", constructor)
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
            "MaxBytes=65536",
            "MaxItems=32",
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

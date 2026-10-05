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

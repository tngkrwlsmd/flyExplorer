"""Outbound drag must expose standard Windows StorageItems without weakening same-app validation."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "app" / "winui" / "m23_drag.cpp"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class OutboundDragContract(unittest.TestCase):
    def test_row_drag_keeps_private_payload_and_adds_standard_storage_items(self):
        source = compact(SOURCE.read_text(encoding="utf-8"))
        row = source[source.index("void MainWindow::OnFileRowDragStarting"):]
        row = row[:row.index("void MainWindow::OnFileDragOver")]
        self.assertIn('SetData(hstring(PrivateFormat)', row)
        self.assertIn("RequestedOperation(DataPackageOperation::Copy)", row)
        self.assertIn("AllowedOperations(DataPackageOperation::Copy)", row)
        self.assertIn("attachOutboundStorageItems(args,std::move(outboundItems))", row)

    def test_standard_storage_items_are_built_asynchronously_under_drag_deferral(self):
        source = compact(SOURCE.read_text(encoding="utf-8"))
        helper = source[source.index("fire_and_forget attachOutboundStorageItems"):]
        helper = helper[:helper.index("void MainWindow::ResetFileRowPointerDrag")]
        self.assertIn("args.GetDeferral()", helper)
        self.assertIn("StorageFolder:: GetFolderFromPathAsync", helper)
        self.assertIn("StorageFile:: GetFileFromPathAsync", helper)
        self.assertIn("args.Data().SetStorageItems(storageItems,false)", helper)
        self.assertIn("deferral.Complete()", helper)

    def test_files_and_folders_are_projected_without_synchronous_filesystem_probe(self):
        source = compact(SOURCE.read_text(encoding="utf-8"))
        row = source[source.index("void MainWindow::OnFileRowDragStarting"):]
        row = row[:row.index("void MainWindow::OnFileDragOver")]
        self.assertIn("outboundItems.push_back({indexed->parsingName,indexed->isFolder()})", row)
        self.assertNotIn("std::filesystem::is_directory", row)
        self.assertNotIn("GetFileAttributes", row)

    def test_same_app_drop_still_prefers_private_token_over_storage_items(self):
        source = compact(SOURCE.read_text(encoding="utf-8"))
        drop = source[source.index("fire_and_forget MainWindow::OnFileDrop"):]
        private_pos = drop.index("if(view.Contains(hstring(PrivateFormat)))")
        storage_pos = drop.index("else if(view.Contains(StandardDataFormats::StorageItems()))")
        self.assertLess(private_pos, storage_pos)
        self.assertIn("source.routeIds[source.active]!=mPrivateDragRoute", drop)
        self.assertIn("mPrivateDragSources.clear()", drop)

    def test_builtin_list_drag_remains_private_fallback_without_fake_sync_storage_items(self):
        source = compact(SOURCE.read_text(encoding="utf-8"))
        builtin = source[source.index("void MainWindow::OnFileDragItemsStarting"):]
        builtin = builtin[:builtin.index("void MainWindow::OnFileRowDragStarting")]
        self.assertIn('SetData(hstring(PrivateFormat)', builtin)
        self.assertNotIn("SetStorageItems", builtin)
        self.assertNotIn("GetFileFromPathAsync", builtin)


if __name__ == "__main__":
    unittest.main()

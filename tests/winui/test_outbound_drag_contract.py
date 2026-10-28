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

    def test_same_app_owned_drag_supports_both_pane_directions(self):
        # Source-only inspection: importing this GUI script would launch a
        # process and create files, so never import it from a contract test.
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'choices=("left-to-right", "right-to-left")',
            'default="left-to-right"',
            'REVERSE = DIRECTION == "right-to-left"',
            'SOURCE_PANE_ID = "RightFiles" if REVERSE else "LeftFiles"',
            'TARGET_PANE_ID = "LeftFiles" if REVERSE else "RightFiles"',
            'source_dir = right if REVERSE else left',
            'target_dir = left if REVERSE else right',
            'visit(SOURCE_PANE_ID, source_dir, source.name)',
            'source_row = row(SOURCE_PANE_ID, source.name)',
            'rr = element(TARGET_PANE_ID).rectangle()',
            'copied = target_dir / source.name',
            'assert copied.read_bytes() == source.read_bytes()',
            'assert source.is_file()',
            'print("SAME_APP_DRAG_DIRECTION", DIRECTION',
            'print("REAL_SAME_APP_PRIVATE_DRAG_RIGHT_TO_LEFT_COPY"',
        ):
            self.assertIn(token, script)
        self.assertIn('source.write_text("owned same-app drag', script)
        self.assertIn('assert_legacy_profile_unchanged(', script)
        self.assertIn('preview.returncode == 0', script)
        self.assertIn('assert owner.value == preview.pid', script)
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_owned_nested_folder_drag_keeps_structure_bytes_and_default_file(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            '"--item-kind", choices=("file", "folder"), default="file"',
            'ITEM_KIND = arguments.item_kind',
            'if ITEM_KIND == "folder":',
            'source.mkdir()',
            'nested.mkdir()',
            'write_bytes(',
            'source.write_text("owned same-app drag',
            'copied.is_dir() if ITEM_KIND == "folder" else copied.is_file()',
            'def owned_tree(root):',
            'relative = child.relative_to(root).as_posix()',
            'assert not child.is_symlink()',
            'assert owned_tree(copied) == owned_tree(source)',
            'assert source.exists(), "same-app copy drag must preserve source"',
            'print("REAL_SAME_APP_PRIVATE_DRAG_NESTED_FOLDER_COPY"',
            'print("SAME_APP_DRAG_ITEM_KIND", ITEM_KIND',
        ):
            self.assertIn(token, script)
        self.assertNotIn('source.rename(', script)
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_same_app_private_drag_stays_copy_only_for_both_directions(self):
        source=compact(SOURCE.read_text(encoding="utf-8"))
        drop=source[source.index("fire_and_forget MainWindow::OnFileDrop"):]
        self.assertIn("request.kind=fxfile::shelltransfer::Kind::Copy",drop)
        self.assertIn("mPrivateDragSide==side",drop)
        self.assertIn("source.routeIds[source.active]!=mPrivateDragRoute",drop)
        self.assertIn("mPrivateDragToken.clear()",drop)
        self.assertLess(
            drop.index("if(view.Contains(hstring(PrivateFormat)))"),
            drop.index("else if(view.Contains(StandardDataFormats::StorageItems()))")
        )
        self.assertNotIn("Kind::Move", drop)

    def test_builtin_list_drag_remains_private_fallback_without_fake_sync_storage_items(self):
        source = compact(SOURCE.read_text(encoding="utf-8"))
        builtin = source[source.index("void MainWindow::OnFileDragItemsStarting"):]
        builtin = builtin[:builtin.index("void MainWindow::OnFileRowDragStarting")]
        self.assertIn('SetData(hstring(PrivateFormat)', builtin)
        self.assertNotIn("SetStorageItems", builtin)
        self.assertNotIn("GetFileFromPathAsync", builtin)


if __name__ == "__main__":
    unittest.main()

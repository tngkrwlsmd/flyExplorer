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
            '"--item-kind", choices=("file", "folder", "multi-file", "mixed"), default="file"',
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

    def test_multi_file_private_drag_requires_two_selected_owned_rows(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'choices=("file", "folder", "multi-file", "mixed")',
            'if ITEM_KIND == "multi-file":',
            'second_source = source_dir / "두번째-한글.txt"',
            'second_row.click_input(pressed="control")',
            'source_row.is_selected() and second_row.is_selected()',
            'print("M23_OWNED_MULTI_FILE_SELECTED"',
            'second_copy = target_dir / second_source.name',
            'second_copy.read_bytes() == second_source.read_bytes()',
            'assert second_source.is_file()',
            'print("REAL_SAME_APP_PRIVATE_DRAG_MULTI_FILE_COPY"',
        ):
            self.assertIn(token, script)
        self.assertIn('"--direction", choices=("left-to-right", "right-to-left")',
                      script)
        self.assertIn('default="left-to-right"',script)
        self.assertIn('default="file"',script)
        self.assertNotIn('source.unlink(',script)

    def test_mixed_file_folder_selected_and_copied_with_complete_payload(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            '"mixed"), default="file"',
            'elif ITEM_KIND == "mixed":',
            'second_source = source_dir / "혼합-한글-폴더"',
            'if ITEM_KIND in ("multi-file", "mixed"):',
            'second_row.click_input(pressed="control")',
            'source_row.is_selected() and second_row.is_selected()',
            'second_copy = target_dir / second_source.name',
            'assert owned_tree(second_copy) == owned_tree(second_source)',
            'assert second_source.is_dir()',
            'print("REAL_SAME_APP_PRIVATE_DRAG_MIXED_FILE_FOLDER_COPY"',
        ):
            self.assertIn(token, script)
        self.assertIn('assert copied.read_bytes() == source.read_bytes()',script)
        self.assertNotIn('source.unlink(',script)
        self.assertNotIn('shutil.rmtree(',script)

    def test_reverse_drag_collision_is_explicit_opt_in_and_preserves_both_files(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            '"--collision", choices=("none", "cancel", "keep-both", "keep-both-late-folder", "keep-both-late-file", "keep-both-type-folder-file", "keep-both-source-renamed", "skip", "skip-all"), default="none"',
            'if COLLISION != "none" and (',
            'collision_target = target_dir / source.name',
            'collision_target.write_bytes(collision_bytes)',
            'assert collision_target.read_bytes() == collision_bytes',
            'assert source.read_bytes() == source_bytes',
            'if COLLISION == "cancel":',
            'cancel.iface_invoke.Invoke()',
            'M23_REVERSE_DRAG_COLLISION_CANCEL_NO_MUTATION=PASS',
            'approve.iface_invoke.Invoke()',
            'unique_copy = eventually(',
            'M23_REVERSE_DRAG_COLLISION_KEEP_BOTH_PRESERVES_TARGET=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('collision_target.write_bytes(collision_bytes)'),
            script.index('preview = None'))
        self.assertIn('args.Data().RequestedOperation(DataPackageOperation::Copy)',
                      SOURCE.read_text(encoding="utf-8"))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_reverse_mixed_drag_cancel_preserves_original_file_and_folder(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'COLLISION not in ("skip", "skip-all", "keep-both-late-folder", "keep-both-late-file",',
            '"keep-both-type-folder-file")',
            'and ITEM_KIND not in ("file", "mixed")',
            'if ITEM_KIND == "mixed" and COLLISION in ("cancel", "keep-both", "keep-both-late-folder"):',
            'assert owned_tree(second_source) == second_source_tree',
            'assert not (target_dir / second_source.name).exists()',
            'cancel.iface_invoke.Invoke()',
            'lambda: "파일 작업 확인을 취소했습니다."',
            'assert sorted(p.name for p in target_dir.iterdir()) == [source.name]',
            'M23_REVERSE_DRAG_COLLISION_MIXED_CANCEL_NO_MUTATION=PASS',
            'assert source.read_bytes() == source_bytes',
            'assert collision_target.read_bytes() == collision_bytes',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('cancel.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_COLLISION_MIXED_CANCEL_NO_MUTATION=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_reverse_mixed_drag_keep_both_preserves_original_and_copied_folder(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'COLLISION not in ("skip", "skip-all", "keep-both-late-folder", "keep-both-late-file",',
            '"keep-both-type-folder-file")',
            'and ITEM_KIND not in ("file", "mixed")',
            'assert owned_tree(second_source) == second_source_tree',
            'approve.iface_invoke.Invoke()',
            'unique_copy = eventually(',
            'lambda: unique_copy.read_bytes() == source_bytes',
            'clean_folder = target_dir / second_source.name',
            'lambda: clean_folder.is_dir() and',
            'owned_tree(clean_folder) == second_source_tree',
            'assert sorted(p.name for p in target_dir.iterdir()) == sorted(',
            '(source.name, unique_copy.name, second_source.name)',
            'M23_REVERSE_DRAG_COLLISION_MIXED_KEEP_BOTH_PRESERVES_ALL=PASS',
            'assert source.read_bytes() == source_bytes',
            'assert collision_target.read_bytes() == collision_bytes',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('approve.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_COLLISION_MIXED_KEEP_BOTH_PRESERVES_ALL=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_source_renamed_during_collision_modal_fails_without_mutation(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            '"keep-both-source-renamed"',
            'renamed_source = source_dir / "원본-이름변경-한글.txt"',
            'os.rename(source, renamed_source)',
            'assert not source.exists()',
            'assert renamed_source.read_bytes() == source_bytes',
            'approve.iface_invoke.Invoke()',
            'lambda: "일부 항목이 처리됐을 수 있습니다."',
            'in element("StatusText").window_text()',
            'assert sorted(p.name for p in target_dir.iterdir()) == [source.name]',
            'assert collision_target.read_bytes() == collision_bytes',
            'M23_REVERSE_DRAG_SOURCE_RENAMED_FAIL_CLOSED=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('os.rename(source, renamed_source)'),
            script.index('approve.iface_invoke.Invoke()'))
        self.assertLess(
            script.index('approve.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_SOURCE_RENAMED_FAIL_CLOSED=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_reverse_folder_on_existing_file_preserves_both_types(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            '"keep-both-type-folder-file"',
            'COLLISION == "keep-both-type-folder-file" and ITEM_KIND != "mixed"',
            'second_collision_target = target_dir / second_source.name',
            'second_collision_bytes = b"pre-existing destination file where source is nested folder"',
            'second_collision_target.write_bytes(second_collision_bytes)',
            'assert second_collision_target.is_file()',
            'assert second_collision_target.read_bytes() == second_collision_bytes',
            'assert owned_tree(second_source) == second_source_tree',
            'approve.iface_invoke.Invoke()',
            'def type_mismatch_copies():',
            'if p.is_file()',
            'if p.is_dir() and p.name != second_source.name',
            'copied_file.read_bytes() == source_bytes',
            'owned_tree(copied_folder) == second_source_tree',
            'copied_file.name, copied_folder.name',
            'M23_REVERSE_DRAG_FOLDER_ON_FILE_KEEP_BOTH=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('second_collision_target.write_bytes(second_collision_bytes)'),
            script.index('approve.iface_invoke.Invoke()'))
        self.assertLess(
            script.index('approve.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_FOLDER_ON_FILE_KEEP_BOTH=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_late_file_collision_keep_both_preserves_all_original_file_bytes(self):
        # One pre-existing file collision opens the modal. A second independent
        # collision appears only while the real dialog is still visible.
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            '"keep-both-late-file"',
            'COLLISION == "keep-both-late-file" and ITEM_KIND != "multi-file"',
            'late_file = target_dir / second_source.name',
            'late_file_bytes = b"late destination second file: preserve untouched"',
            'late_file.write_bytes(late_file_bytes)',
            'assert second_source.read_bytes() == second_source_bytes',
            'assert collision_target.read_bytes() == collision_bytes',
            'assert late_file.read_bytes() == late_file_bytes',
            'approve.iface_invoke.Invoke()',
            'def renamed_file_copies():',
            'originals = {source.name, second_source.name}',
            'if p.is_file() and p.name not in originals',
            'return candidates if len(candidates) == 2 else None',
            'sorted(p.read_bytes() for p in copies)',
            'sorted((source_bytes, second_source_bytes))',
            'copies[0].name, copies[1].name',
            'M23_REVERSE_DRAG_LATE_FILE_COLLISION_KEEP_BOTH=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('late_file.write_bytes(late_file_bytes)'),
            script.index('approve.iface_invoke.Invoke()'))
        self.assertLess(
            script.index('approve.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_LATE_FILE_COLLISION_KEEP_BOTH=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_late_nested_folder_collision_keep_both_preserves_both_original_trees(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            '"keep-both-late-folder"',
            'COLLISION == "keep-both-late-folder" and ITEM_KIND != "mixed"',
            'late_folder = target_dir / second_source.name',
            'late_folder.mkdir()',
            'late competing destination nested payload: preserve',
            'late original root bytes',
            'late_folder_tree = owned_tree(late_folder)',
            'assert owned_tree(second_source) == second_source_tree',
            'assert source.read_bytes() == source_bytes',
            'assert collision_target.read_bytes() == collision_bytes',
            'approve.iface_invoke.Invoke()',
            'def renamed_folder_copy():',
            'p.is_dir() and p.name != second_source.name',
            'owned_tree(copied_folder) == second_source_tree',
            'assert owned_tree(late_folder) == late_folder_tree',
            'second_source.name, copied_folder.name',
            'M23_REVERSE_DRAG_LATE_FOLDER_COLLISION_KEEP_BOTH=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('late_folder.mkdir()'),
            script.index('approve.iface_invoke.Invoke()'))
        self.assertLess(
            script.index('approve.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_LATE_FOLDER_COLLISION_KEEP_BOTH=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_reverse_drag_skip_preserves_collision_and_copies_clean_member(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'COLLISION == "skip" and ITEM_KIND not in ("multi-file", "mixed")',
            'COLLISION not in ("skip", "skip-all", "keep-both-late-folder", "keep-both-late-file",',
            '"keep-both-type-folder-file")',
            'and ITEM_KIND not in ("file", "mixed")',
            'second_row.click_input(pressed="control")',
            'source_row.is_selected() and second_row.is_selected()',
            'source_bytes = source.read_bytes() if source.is_file() else None',
            'if COLLISION == "skip":',
            'assert not (target_dir / second_source.name).exists()',
            'skip = modal_button("충돌 항목 건너뛰기")',
            'skip.iface_invoke.Invoke()',
            'clean_copy = target_dir / second_source.name',
            'eventually(clean_copy.is_file,',
            'clean_copy.read_bytes() == second_source.read_bytes()',
            'assert sorted(p.name for p in target_dir.iterdir()) == sorted(',
            'assert collision_target.read_bytes() == collision_bytes',
            'assert source.read_bytes() == source_bytes',
            'M23_REVERSE_DRAG_COLLISION_SKIP_COPIES_ONLY_CLEAN=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('collision_target.write_bytes(collision_bytes)'),
            script.index('preview = None'))
        self.assertLess(
            script.index('skip.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_COLLISION_SKIP_COPIES_ONLY_CLEAN=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_reverse_multi_drag_all_collisions_skip_preserves_every_byte(self):
        # This distinct opt-in case creates *two* pre-existing destinations.
        # It is not the earlier one-collision/one-clean-member scenario.
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'COLLISION == "skip-all" and ITEM_KIND not in ("multi-file", "mixed")',
            'second_collision_target = target_dir / second_source.name',
            'second_collision_target.write_bytes(second_collision_bytes)',
            'second_source_bytes = (',
            'if COLLISION == "skip-all":',
            'assert second_collision_target.read_bytes() == second_collision_bytes',
            'assert second_source.read_bytes() == second_source_bytes',
            'expected_existing = sorted(',
            'elif COLLISION in ("skip", "skip-all"):',
            'skip.iface_invoke.Invoke()',
            'lambda: "충돌한 2개 항목을 모두 건너뛰었습니다. 파일을 변경하지 않았습니다."',
            'in element("StatusText").window_text()',
            'assert sorted(p.name for p in target_dir.iterdir()) == expected_existing',
            'M23_REVERSE_DRAG_COLLISION_SKIP_ALL_PRESERVES_BOTH=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('second_collision_target.write_bytes(second_collision_bytes)'),
            script.index('preview = None'))
        self.assertLess(
            script.index('skip.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_COLLISION_SKIP_ALL_PRESERVES_BOTH=PASS'))
        controller=(ROOT/"app/winui/file_operation_controller.cpp").read_text(
            encoding="utf-8")
        transfer=(ROOT/"app/winui/m22_transfers.cpp").read_text(
            encoding="utf-8")
        self.assertIn('return StartStatus::AllSkipped;', controller)
        self.assertIn('L"충돌한 "+std::to_wstring(skipped)', transfer)
        self.assertIn('개 항목을 모두 건너뛰었습니다. 파일을 변경하지 않았습니다.',
                      transfer)
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_reverse_mixed_all_collisions_skip_preserves_both_original_trees(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'COLLISION == "skip-all" and ITEM_KIND not in ("multi-file", "mixed")',
            'assert ITEM_KIND in ("multi-file", "mixed") and second_source is not None',
            'second_collision_target = target_dir / second_source.name',
            'if ITEM_KIND == "mixed":',
            'second_collision_target.mkdir()',
            '(second_collision_target / "하위-폴더").mkdir()',
            'existing destination nested folder: do not replace',
            'existing destination root payload',
            'second_source_tree = (',
            'second_collision_tree = (',
            'def assert_second_collision_unchanged():',
            'assert owned_tree(second_source) == second_source_tree',
            'assert owned_tree(second_collision_target) == second_collision_tree',
            'assert_second_collision_unchanged()',
            'lambda: "충돌한 2개 항목을 모두 건너뛰었습니다. 파일을 변경하지 않았습니다."',
            'assert sorted(p.name for p in target_dir.iterdir()) == expected_existing',
            'M23_REVERSE_DRAG_COLLISION_MIXED_ALL_SKIP_PRESERVES_TREES=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('second_collision_target.mkdir()'),
            script.index('preview = None'))
        self.assertLess(
            script.index('skip.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_COLLISION_MIXED_ALL_SKIP_PRESERVES_TREES=PASS'))
        self.assertNotIn('source.unlink(', script)
        self.assertNotIn('shutil.rmtree(', script)

    def test_reverse_mixed_drag_skip_preserves_existing_file_and_nested_folder(self):
        script=(ROOT/"tests/winui/test_same_app_drag_regression_gui.py").read_text(
            encoding="utf-8")
        for token in (
            'COLLISION == "skip" and ITEM_KIND not in ("multi-file", "mixed")',
            'elif ITEM_KIND == "mixed":',
            'second_source = source_dir / "혼합-한글-폴더"',
            'collision_target.write_bytes(collision_bytes)',
            'if COLLISION == "skip":',
            'second_source.is_file() if ITEM_KIND == "multi-file"',
            'else second_source.is_dir()',
            'skip = modal_button("충돌 항목 건너뛰기")',
            'skip.iface_invoke.Invoke()',
            'clean_copy = target_dir / second_source.name',
            'if ITEM_KIND == "multi-file":',
            'assert ITEM_KIND == "mixed"',
            'lambda: (clean_copy / "하위-폴더" / "혼합-한글.txt").is_file()',
            'lambda: owned_tree(clean_copy) == owned_tree(second_source)',
            'assert sorted(p.name for p in target_dir.iterdir()) == sorted(',
            'assert collision_target.read_bytes() == collision_bytes',
            'assert source.read_bytes() == source_bytes',
            'M23_REVERSE_DRAG_COLLISION_MIXED_SKIP_PRESERVES_FOLDER=PASS',
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index('collision_target.write_bytes(collision_bytes)'),
            script.index('preview = None'))
        self.assertLess(
            script.index('skip.iface_invoke.Invoke()'),
            script.index('M23_REVERSE_DRAG_COLLISION_MIXED_SKIP_PRESERVES_FOLDER=PASS'))
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

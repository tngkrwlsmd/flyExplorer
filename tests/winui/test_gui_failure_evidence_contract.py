"""Standalone contract for GUI-failure evidence; runs without a desktop."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from gui_failure_evidence import (
    MAX_ENTRIES, _disk_rows, _owned_labels, _safe_address, _uia_pane,
    capture_failure,
)


class MockNode:
    def __init__(self, text):
        self.text = text
        self.element_info = type("Info", (), {
            "control_type": "ListItem", "automation_id": "fixture-item"})

    def window_text(self):
        return self.text


class MockSpec:
    def __init__(self, value=None, nodes=None):
        self.value, self.nodes = value, nodes or []

    def exists(self, timeout=None):
        return True

    def get_value(self):
        return self.value

    def descendants(self):
        return self.nodes

    def window_text(self):
        return self.value


class MockWindow:
    def child_window(self, auto_id):
        if auto_id == "AddressBox":
            return MockSpec("C:\\Users\\someone\\Private")
        return MockSpec(nodes=[MockNode("copy.txt"),
                               MockNode("Private contents should be hidden")])


class StartupWindow(MockWindow):
    def __init__(self, address, status, active):
        self.address, self.status, self.active = address, status, active

    def child_window(self, auto_id):
        if auto_id == "AddressBox":
            return MockSpec(self.address)
        if auto_id == "StatusText":
            return MockSpec(self.status)
        if auto_id == "ActivePaneText":
            return MockSpec(self.active)
        if auto_id == "LeftFiles":
            return MockSpec(nodes=[MockNode("Nested")])
        if auto_id == "RightFiles":
            return MockSpec(nodes=[MockNode("Secondary")])
        return MockSpec(nodes=[])


class GuiFailureEvidenceContract(unittest.TestCase):
    def test_capture_is_bounded_owned_and_redacts_external_uia(self):
        with TemporaryDirectory() as root:
            base = Path(root) / "phase6-winui"
            owned = base / "shell-owned-contract"
            left, right = owned / "Left", owned / "Right"
            left.mkdir(parents=True)
            right.mkdir(parents=True)
            (left / "copy.txt").write_text("test fixture", encoding="utf-8")
            try:
                raise AssertionError("fixture failure")
            except AssertionError as err:
                output = capture_failure(base=base, owned=owned, left=left,
                                         right=right, win=MockWindow(),
                                         hwnd=None, pid=None, error=err)
            self.assertTrue((output / "manifest.json").is_file())
            self.assertTrue((output / "panes.json").is_file())
            self.assertTrue((output / "owned-files.json").is_file())
            self.assertTrue((output / "failure-trace.txt").is_file())
            manifest = json.loads((output / "manifest.json").read_text("utf-8"))
            self.assertEqual("FAIL", manifest["result"])
            self.assertTrue(manifest["screenshot"].startswith("skipped:"))
            nodes = json.loads((output / "panes.json").read_text("utf-8"))
            self.assertEqual("[outside test-owned scope]",
                             nodes["AddressBox"]["value"])
            self.assertEqual("[non-fixture label]",
                             nodes["RightFiles"]["nodes"][1]["name"])
            files = json.loads((output / "owned-files.json").read_text("utf-8"))
            self.assertEqual("copy.txt", files["left"]["items"][0]["name"])
            self.assertNotIn("test fixture", (output / "owned-files.json").read_text("utf-8"))

    def test_watcher_failure_keeps_only_owned_path_free_native_events(self):
        with TemporaryDirectory() as root:
            base = Path(root) / "phase6-winui"
            owned = base / "shell-owned-watcher"
            left, right = owned / "Left", owned / "Right"
            left.mkdir(parents=True)
            right.mkdir()
            output = capture_failure(
                base=base, owned=owned, left=left, right=right,
                win=StartupWindow(str(left), "Shell 폴더를 열지 못했습니다.",
                                  "활성: 왼쪽"),
                hwnd=None, pid=None,
                error=AssertionError(
                    "native directory watcher did not refresh the real WinUI ListView"),
                startup_events=["LEFT_APPLIED", "LEFT_FAILED",
                                "LEFT_HRESULT_8007000D", "private path value"])
            raw = (output / "panes.json").read_text(encoding="utf-8")
            startup = json.loads(raw)["Startup"]
            self.assertEqual(["LEFT_APPLIED", "LEFT_FAILED",
                              "LEFT_HRESULT_8007000D"],
                             startup["owned_native_events"])
            self.assertNotIn("sampled_transitions", startup)
            self.assertNotIn("private path value", raw)
            self.assertEqual("shell-failed", startup["status_category"])

    def test_startup_categories_have_no_raw_status_or_external_paths(self):
        with TemporaryDirectory() as root:
            base = Path(root) / "phase6-winui"
            owned = base / "shell-owned-startup"
            left, right = owned / "Left", owned / "Right"
            (left / "Nested").mkdir(parents=True)
            (right / "Secondary").mkdir(parents=True)
            secret = "Private user status C:\\Users\\person\\secret"
            window = StartupWindow(str(left), secret, "활성: 오른쪽")
            output = capture_failure(base=base, owned=owned, left=left,
                                     right=right, win=window, hwnd=None,
                                     pid=None, error=AssertionError("fixture"))
            raw = (output / "panes.json").read_text(encoding="utf-8")
            startup = json.loads(raw)["Startup"]
            self.assertEqual("owned-left", startup["address_route"])
            self.assertEqual("right", startup["active_pane"])
            self.assertEqual("other", startup["status_category"])
            self.assertTrue(startup["left_expected_child_visible"])
            self.assertTrue(startup["right_expected_child_visible"])
            self.assertEqual(1, startup["left_uia_list_items"])
            self.assertEqual(1, startup["right_uia_list_items"])
            self.assertNotIn(secret, raw)
            self.assertNotIn("person", raw)

    def test_startup_status_codes_are_fixed_and_empty_route_distinguished(self):
        with TemporaryDirectory() as root:
            base = Path(root) / "phase6-winui"
            owned = base / "shell-owned-startup"
            left, right = owned / "Left", owned / "Right"
            left.mkdir(parents=True)
            right.mkdir()
            window = StartupWindow("", "폴더를 불러오는 중입니다.", "활성: 왼쪽")
            output = capture_failure(base=base, owned=owned, left=left,
                                     right=right, win=window, hwnd=None,
                                     pid=None, error=AssertionError("fixture"))
            startup = json.loads(
                (output / "panes.json").read_text("utf-8"))["Startup"]
            self.assertEqual("empty", startup["address_route"])
            self.assertEqual("left", startup["active_pane"])
            self.assertEqual("loading", startup["status_category"])

    def test_g01_startup_timeline_is_bounded_and_private(self):
        with TemporaryDirectory() as root:
            base = Path(root) / "phase6-winui"
            owned = base / "shell-owned-startup"
            left, right = owned / "Left", owned / "Right"
            left.mkdir(parents=True)
            right.mkdir()
            sensitive = "C:\\Users\\someone\\private-marker"
            samples = [
                {"elapsed_bucket": index * 2, "status": "loading",
                 "address": "empty"} for index in range(19)
            ]
            samples[-1] = {
                "elapsed_bucket": 36, "status": sensitive,
                "address": sensitive,
            }
            failure = AssertionError(
                "UI-independent native core/helper was not active at startup")
            output = capture_failure(
                base=base, owned=owned, left=left, right=right,
                win=StartupWindow("", "폴더를 불러오는 중입니다.", "활성: 왼쪽"),
                hwnd=None, pid=None, error=failure, startup_samples=samples)
            raw = (output / "panes.json").read_text(encoding="utf-8")
            timeline = json.loads(raw)["Startup"]["sampled_transitions"]
            self.assertEqual(16, len(timeline))
            self.assertEqual(
                {"elapsed_bucket": 36, "status": "other", "address": "other",
                 "left_fixture_visible": False},
                timeline[-1])
            self.assertNotIn(sensitive, raw)
            non_startup = capture_failure(
                base=base, owned=owned, left=left, right=right,
                win=None, hwnd=None, pid=None,
                error=AssertionError("unrelated GUI gate failed"),
                startup_samples=samples)
            unrelated = json.loads(
                (non_startup / "panes.json").read_text(encoding="utf-8"))
            self.assertNotIn("sampled_transitions", unrelated["Startup"])

    def test_bounded_scandir_for_large_owned_directory_and_redaction(self):
        # Simulate 20,000 direct children without creating a large fixture.
        # Any regression that exhausts scandir will consume all 20,000 names.
        class FakeEntry:
            def __init__(self, index):
                self.name = f"owned-{index:05d}.txt"

            def is_symlink(self):
                return False

            def stat(self, follow_symlinks=True):
                return SimpleNamespace(st_size=1)

            def is_dir(self, follow_symlinks=True):
                return False

            def is_file(self, follow_symlinks=True):
                return True

        class CountingScan:
            def __init__(self, counter):
                self.counter = counter

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def __iter__(self):
                for index in range(20000):
                    self.counter.append(1)
                    yield FakeEntry(index)

        with TemporaryDirectory() as root:
            owned = Path(root) / "shell-owned-bounded"
            left, right = owned / "Left", owned / "Right"
            left.mkdir(parents=True)
            right.mkdir()
            visited = []
            with patch("gui_failure_evidence.os.scandir",
                       side_effect=lambda *_: CountingScan(visited)):
                rows = _disk_rows(left, owned)
                labels = _owned_labels(left, right)
            self.assertEqual(MAX_ENTRIES, len(rows["items"]))
            self.assertTrue(rows["truncated"])
            self.assertEqual("owned-00000.txt", rows["items"][0]["name"])
            self.assertEqual("owned-00069.txt", rows["items"][-1]["name"])
            self.assertEqual(3 * (MAX_ENTRIES + 1), len(visited))
            self.assertLessEqual(len(labels), 5 + 2 * MAX_ENTRIES)
            self.assertIn("owned-00000.txt", labels)
            self.assertNotIn("owned-00070.txt", labels)
            ui = _uia_pane(MockWindow(), "LeftFiles", labels)
            self.assertEqual("[non-fixture label]", ui["nodes"][1]["name"])
            self.assertNotIn("Private contents should be hidden", json.dumps(ui))

    def test_refuses_unowned_directory_and_skips_symlinks(self):
        with TemporaryDirectory() as root:
            base = Path(root) / "phase6-winui"
            owned = base / "shell-owned-test"
            left, right = owned / "Left", owned / "Right"
            left.mkdir(parents=True)
            right.mkdir()
            self.assertEqual("[outside test-owned scope]",
                             _safe_address(Path(root), owned))
            self.assertEqual([], _disk_rows(left, owned)["items"])
            with self.assertRaises(ValueError):
                capture_failure(base=base, owned=owned, left=left,
                                right=Path(root), win=None,
                                hwnd=None, pid=None, error=AssertionError())


if __name__ == "__main__":
    unittest.main()

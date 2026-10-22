"""Standalone contract for GUI-failure evidence; runs without a desktop."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gui_failure_evidence import _disk_rows, _safe_address, capture_failure


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

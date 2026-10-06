"""Shared bounded file-operation budget contracts."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class TransferBudgetContract(unittest.TestCase):
    def test_shared_budget_is_explicit_and_exceeds_legacy_32(self):
        header = compact(read("src/base/shell_transfer_core.h"))
        self.assertIn("kMaxItems=1024", header)
        self.assertIn("kMaxSourcePathUnits=1024*1024", header)

    def test_native_transfer_validates_item_and_aggregate_path_budget(self):
        core = compact(read("src/base/shell_transfer_core.cpp"))
        self.assertIn("request.sources.size()>kMaxItems", core)
        self.assertIn("sourcePathUnits>kMaxSourcePathUnits-source.size()-1", core)
        self.assertIn("sourcePathUnits+=source.size()+1", core)

    def test_clipboard_reuses_transfer_budget_instead_of_private_32_cap(self):
        clipboard = compact(read("src/base/shell_clipboard_core.cpp"))
        self.assertIn("MaxItems=shelltransfer::kMaxItems", clipboard)
        self.assertIn("shelltransfer::kMaxSourcePathUnits", clipboard)
        self.assertNotIn("MaxItems=32", clipboard)
        self.assertNotIn("MaxBytes=65536", clipboard)

    def test_winui_selection_clipboard_and_drag_share_the_budget(self):
        transfer = compact(read("app/winui/m22_transfers.cpp"))
        drag = compact(read("app/winui/m23_drag.cpp"))
        self.assertGreaterEqual(
            transfer.count("fxfile::shelltransfer::kMaxItems"), 2
        )
        self.assertGreaterEqual(
            transfer.count("fxfile::shelltransfer::kMaxSourcePathUnits"), 2
        )
        self.assertGreaterEqual(drag.count("fxfile::shelltransfer::kMaxItems"), 3)
        self.assertGreaterEqual(
            drag.count("fxfile::shelltransfer::kMaxSourcePathUnits"), 1
        )
        for legacy in (
            "req.sources.size()>32",
            "item.paths.size()>32",
            "chosen.size()>32",
            "items.Size()>32",
            "args.Items().Size()>32",
        ):
            self.assertNotIn(legacy, transfer + drag)
        self.assertNotIn("최대 32개", transfer + drag)

    def test_native_fixtures_prove_more_than_32_and_fail_closed_above_budget(self):
        transfer_fixture = compact(read("tests/winui/m22/m22_transfer_fixture.cpp"))
        clipboard_fixture = compact(read("tests/winui/m23/m23_native_fixture.cpp"))
        for token in (
            "validate_more_than_32_items",
            "actual_ifileoperation_64_item_copy",
            "reject_over_shared_item_budget",
        ):
            self.assertIn(token, transfer_fixture)
        for token in (
            "cf_hdrop_roundtrip_more_than_32_items",
            "reject_over_shared_item_budget",
        ):
            self.assertIn(token, clipboard_fixture)


if __name__ == "__main__":
    unittest.main()

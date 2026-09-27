"""Negative regression guards for UI-05's fresh-profile resize retry.

This source test supplements, not replaces, native MFC runtime visual evidence.
"""
from pathlib import Path
import unittest

from validate_source_invariants import validate_fresh_profile_compaction_retry_contract

SRC = Path(__file__).resolve().parents[1] / "src" / "fxfile"


class FreshProfileCompactionRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coolbar = (SRC / "main_coolbar.cpp").read_text(encoding="utf-8")
        cls.header = (SRC / "main_coolbar.h").read_text(encoding="utf-8")

    def check_mutation(self, original, replacement, part="cpp"):
        source = self.coolbar if part == "cpp" else self.header
        self.assertIn(original, source, "invalid fixture: tested contract changed")
        mutated = source.replace(original, replacement, 1)
        cpp = mutated if part == "cpp" else self.coolbar
        hdr = mutated if part == "header" else self.header
        self.assertTrue(validate_fresh_profile_compaction_retry_contract(cpp, hdr))

    def test_current_contract_passes(self):
        self.assertEqual(
            validate_fresh_profile_compaction_retry_contract(self.coolbar, self.header), []
        )

    def test_missing_watermark_is_rejected(self):
        self.check_mutation("mLastDefaultCompactWidth;", "mRemovedWatermark;", "header")

    def test_no_width_growth_check_is_rejected(self):
        self.check_mutation(
            "sClient.Width() > mLastDefaultCompactWidth",
            "sClient.Width() > 0",
        )

    def test_no_measured_retry_is_rejected(self):
        self.check_mutation(
            "mLastDefaultCompactWidth = sClient.Width();",
            "mLastDefaultCompactWidth = 0;",
        )

    def test_premature_pending_reset_is_rejected(self):
        self.check_mutation(
            "mLastDefaultCompactWidth = sClient.Width();",
            "mLastDefaultCompactWidth = sClient.Width();\n    mDefaultCompactPending = XPR_FALSE;",
        )

    def test_manual_rebar_drag_cannot_be_removed(self):
        self.check_mutation("sHeader->code == RBN_BEGINDRAG", "sHeader->code == RBN_ENDDRAG")

    def test_saved_user_layout_must_not_auto_compact(self):
        self.check_mutation("XPR_IS_FALSE(sSavedCoolBar)", "XPR_IS_TRUE(sSavedCoolBar)")

    def test_no_synchronous_band_relayout_during_wm_size(self):
        self.check_mutation(
            "CSizableReBar::OnSize(nType, cx, cy);",
            "CSizableReBar::OnSize(nType, cx, cy);\n    sReBarCtrl.SetBandInfo(0, &sRebarBandInfo);",
        )


if __name__ == "__main__":
    unittest.main()

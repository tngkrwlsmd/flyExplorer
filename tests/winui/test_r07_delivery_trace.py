"""R07 테스트 전용 전송 로그의 관측 분류 계약 (Windows/GUI 불필요)."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r07_delivery_trace import observed_delivery_boundary


class R07DeliveryTraceTests(unittest.TestCase):
    def test_last_observed_delivery_boundary(self):
        cases = (
            ((), "POST_NOT_OBSERVED"),
            (("UI_TASK_ENTERED",), "POST_NOT_OBSERVED"),
            (("POST_CALLED",), "POST_RESULT_NOT_OBSERVED"),
            (("POST_CALLED", "POST_REJECTED"), "POST_REJECTED"),
            (("POST_CALLED", "POST_EXCEPTION"), "POST_EXCEPTION"),
            (("POST_CALLED", "POST_ACCEPTED"), "UI_TASK_NOT_OBSERVED"),
            (("POST_CALLED", "POST_ACCEPTED", "UI_TASK_ENTERED"),
             "UI_TASK_DISPATCH_NOT_OBSERVED"),
            (("POST_CALLED", "POST_ACCEPTED", "UI_TASK_ENTERED",
              "UI_TASK_DISPATCH"), "FILE_COMPLETION_NOT_OBSERVED"),
            (("POST_CALLED", "POST_ACCEPTED", "UI_TASK_ENTERED",
              "UI_TASK_DISPATCH", "ON_FILE_COMPLETION"),
             "FILE_COMPLETION_OBSERVED"),
        )
        for stages, expected in cases:
            with self.subTest(stages=stages):
                self.assertEqual(observed_delivery_boundary(stages), expected)

    def test_worker_ui_interleaving_does_not_change_result(self):
        self.assertEqual(observed_delivery_boundary([
            "POST_CALLED", "UI_TASK_ENTERED", "UI_TASK_DISPATCH",
            "ON_FILE_COMPLETION", "POST_ACCEPTED",
        ]), "FILE_COMPLETION_OBSERVED")


if __name__ == "__main__":
    unittest.main()

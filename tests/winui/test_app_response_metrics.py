"""Pure metric checks; Windows timing acceptance comes only from the owned VM."""
import unittest
from benchmark_app_folder import response_summary


class AppResponseMetrics(unittest.TestCase):
    def test_empty_samples_are_not_zero_latency(self):
        self.assertEqual(response_summary([]), {
            "samples": 0, "failed_sends": 0,
            "p50_ms": None, "p95_ms": None, "max_ms": None})

    def test_nearest_rank_p95_and_median_are_order_independent(self):
        result=response_summary([(float(i), True) for i in range(20, 0, -1)])
        self.assertEqual(result["p50_ms"], 10.5)
        self.assertEqual(result["p95_ms"], 19.0)
        self.assertEqual(result["max_ms"], 20.0)

    def test_timeout_is_counted_and_retained_in_maximum(self):
        result=response_summary([(2.0, True), (1001.2, False), (4.0, True)])
        self.assertEqual(result["samples"], 3)
        self.assertEqual(result["failed_sends"], 1)
        self.assertEqual(result["p95_ms"], 4.0)
        self.assertEqual(result["max_ms"], 1001.2)


if __name__ == "__main__":
    unittest.main()

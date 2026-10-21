"""Wire corruption and paging integrity regressions; no desktop or helper needed."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import benchmark_pages
from wire_client import MAGIC, parse, pidl_valid, request


def checksum(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def text(value):
    encoded = value.encode("utf-16le")
    return struct.pack("<I", len(encoded) // 2) + encoded


def frame(names=(), *, flags=0, extra=b""):
    pidl = struct.pack("<I", 2) + b"\0\0"
    body = text("owned") + text("C:\\owned") + text("C:\\owned") + pidl
    for name in names:
        body += struct.pack("<I", 0) + text(name) + text("C:\\owned\\" + name) + pidl
    body += extra
    return struct.pack("<IIiIIII", MAGIC, 3, 0, len(names), len(body), checksum(body), flags) + body


class WireClientTests(unittest.TestCase):
    def test_unicode_request_counts_utf16_units(self):
        data = request("C:\\owned\\한글-\U0001f4c1", offset=1024, limit=17)
        header = struct.unpack_from("<IIIIII", data)
        self.assertEqual(header[:3], (MAGIC, 3, 1))
        self.assertEqual(header[3] * 2, len(data) - 24)
        self.assertEqual(header[4:], (1024, 17))

    def test_valid_unicode_page_and_pidl_request(self):
        reply = parse(frame(["한글.txt"], flags=1))
        self.assertEqual(reply["entries"][0]["name"], "한글.txt")
        self.assertEqual(reply["flags"], 1)
        data = request(pidl_bytes=reply["folder"]["pidl"], limit=1)
        self.assertEqual(struct.unpack_from("<IIIIII", data)[2:4], (2, 2))

    def test_rejects_truncated_appended_and_corrupted_frames(self):
        good = frame(["a.txt"])
        for bad in (good[:19], good[:-1], good+b"x",
                    good[:28]+bytes([good[28]^1])+good[29:]):
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                parse(bad)

    def test_rejects_unknown_flags_and_unconsumed_body_with_valid_checksum(self):
        for bad in (frame(flags=2), frame(extra=b"x")):
            with self.assertRaises(ValueError):
                parse(bad)

    def test_rejects_count_and_body_bounds(self):
        good = frame()
        for offset, value in ((12, 1025), (16, 8*1024**2+1)):
            bad = bytearray(good)
            struct.pack_into("<I", bad, offset, value)
            with self.assertRaises(ValueError):
                parse(bad)

    def test_failure_hresult_has_no_partial_state(self):
        failed = struct.pack("<IIiIIII", MAGIC, 3, -1, 0, 0, checksum(b""), 0)
        self.assertEqual(parse(failed), {"hr": -1, "entries": [], "flags": 0})
        with self.assertRaises(ValueError):
            parse(struct.pack("<IIiIIII", MAGIC, 3, -1, 1, 0, checksum(b""), 0))

    def test_rejects_malformed_pidl(self):
        for bad in (b"", b"\0", b"\0\0x", b"\1\0\0\0", b"\4\0x"):
            self.assertFalse(pidl_valid(bad))


class BenchmarkPagingTests(unittest.TestCase):
    def run_owned(self, responder):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "fixture"
            def page(helper, env, requested, offset, limit, timeout):
                self.assertEqual(requested, folder)
                names, flags = responder(offset)
                return {
                    "hr": 0, "folder": {"filesystem_path": str(folder)},
                    "entries": [{"name": name} for name in names], "flags": flags,
                }, 2.5
            with patch.object(benchmark_pages, "roundtrip", side_effect=page):
                return benchmark_pages.run_case(folder, 3, Path("helper.exe"), {}, 12, page_size=2)

    def test_complete_pages_have_distinct_entries_and_separate_samples(self):
        report = self.run_owned(lambda offset: (
            (["bench-00000.txt", "bench-00001.txt"], 1) if offset == 0
            else (["bench-00002.txt"], 0)))
        self.assertEqual([p["offset"] for p in report["pages"]], [0, 2])
        self.assertEqual(report["all_pages_ms"], 5.0)
        self.assertTrue(report["all_entries_unique_and_preserved"])

    def test_duplicate_missing_and_wrong_continuation_cannot_pass(self):
        cases = (
            lambda offset: ((["bench-00000.txt", "bench-00001.txt"], 1)
                            if offset == 0 else (["bench-00000.txt"], 0)),
            lambda offset: (["bench-00000.txt"], 0),
            lambda offset: (["bench-00000.txt", "bench-00001.txt"], 0),
        )
        for responder in cases:
            with self.subTest(responder=responder), self.assertRaises(AssertionError):
                self.run_owned(responder)

    def test_child_failure_and_timeout_are_not_latency_successes(self):
        with patch.object(benchmark_pages.subprocess, "run") as run:
            run.return_value.returncode = 5
            with self.assertRaises(RuntimeError):
                benchmark_pages.roundtrip(Path("helper.exe"), {}, Path("C:/owned"), 0, 1, 12)
            run.side_effect = benchmark_pages.subprocess.TimeoutExpired("helper.exe", 12)
            with self.assertRaises(benchmark_pages.subprocess.TimeoutExpired):
                benchmark_pages.roundtrip(Path("helper.exe"), {}, Path("C:/owned"), 0, 1, 12)


if __name__ == "__main__":
    unittest.main()

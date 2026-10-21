"""Bounded minidump validation and caller-owned-only evidence paths."""
from pathlib import Path
import struct
import tempfile
import unittest

from owned_process_dump import summarize, validate_paths, capture_owned_dump


def fixture():
    data = bytearray(128)
    struct.pack_into("<IIIIIIQ", data, 0, 0x504d444d, 0xa793, 1, 32, 0, 0, 0x1000)
    struct.pack_into("<III", data, 32, 3, 52, 44)
    struct.pack_into("<I", data, 44, 1)
    struct.pack_into("<I", data, 48, 7)
    struct.pack_into("<II", data, 80, 16, 112)
    struct.pack_into("<II", data, 88, 16, 96)
    return data


class OwnedDumpTests(unittest.TestCase):
    def test_stack_and_context_descriptors_are_required_and_counted(self):
        self.assertEqual(summarize(fixture()),
                         {"threads": 1, "contexts": 1, "stacks": 1, "bytes": 128, "unused_streams": 0})

    def test_rejects_truncated_bad_header_and_directory_bounds(self):
        valid = fixture()
        cases = [valid[:31], valid[:100]]
        for offset, value in ((0, 0), (4, 0), (8, 129), (12, 127)):
            damaged = fixture()
            struct.pack_into("<I", damaged, offset, value)
            cases.append(damaged)
        for data in cases:
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                summarize(data)

    def test_rejects_missing_or_unbounded_thread_records(self):
        for offset, value in ((32, 7), (44, 0), (44, 4097), (44, 2)):
            data = fixture()
            struct.pack_into("<I", data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                summarize(data)

    def test_rejects_empty_or_out_of_file_stack_and_context(self):
        for offset, value in ((80, 0), (88, 0), (84, 127), (92, 127)):
            data = fixture()
            struct.pack_into("<I", data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                summarize(data)

    def test_duplicate_streams_are_rejected(self):
        data = fixture()
        struct.pack_into("<II", data, 8, 2, 128)
        data.extend(struct.pack("<III", 3, 52, 44) * 2)
        with self.assertRaisesRegex(ValueError, "duplicate dump stream"):
            summarize(data)

    def test_repeated_unused_directory_slots_are_not_real_duplicate_streams(self):
        data = fixture()
        struct.pack_into("<II", data, 8, 3, 128)
        data.extend(struct.pack("<III", 3, 52, 44) + bytes(24))
        result = summarize(data)
        self.assertEqual(result["unused_streams"], 2)
        self.assertEqual(result["stacks"], 1)

    def test_only_built_known_exe_and_ignored_output_are_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exe = root / "out/Release/flyExplorer.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"owned fixture")
            output = root / "logs/owned"
            self.assertEqual(validate_paths(exe, output, root), (exe.resolve(), output.resolve()))
            for bad_exe, bad_output in (
                (exe, root / "outside"),
                (root / "missing.exe", output),
                (exe.parent / "unrelated.exe", output),
            ):
                with self.subTest(exe=bad_exe), self.assertRaises(ValueError):
                    validate_paths(bad_exe, bad_output, root)

    def test_unrelated_target_never_reaches_collection(self):
        result = capture_owned_dump(None, Path(__file__), Path(__file__).parent)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error_type"], "ValueError")


if __name__ == "__main__":
    unittest.main()

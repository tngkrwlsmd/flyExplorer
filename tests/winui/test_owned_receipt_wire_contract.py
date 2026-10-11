"""Synthetic, test-owned receipt v1 records; safe to run without WinUI."""
from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from receipt_wire_owned import matches_owned_published_target

HEADER = struct.Struct("<8sIIIQ16sIQI")


def make_record(stage: str, leaf: str) -> bytes:
    raw = bytearray(HEADER.pack(
        b"FLYSTGR1", 1, len(stage.encode("utf-16-le")) // 2,
        len(leaf.encode("utf-16-le")) // 2, 7, b"\x01" * 16, 1234, 99, 0))
    raw += stage.encode("utf-16-le") + leaf.encode("utf-16-le")
    digest = 2166136261
    for byte in raw:
        digest = ((digest ^ byte) * 16777619) & 0xFFFFFFFF
    struct.pack_into("<I", raw, HEADER.size - 4, digest)
    return bytes(raw)


class OwnedReceiptTargetContract(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="fly-owned-wire-")
        self.addCleanup(self.root.cleanup)
        self.base = Path(self.root.name)
        self.destination = self.base / "dest"
        self.destination.mkdir()
        self.target = self.destination / "test-한글.txt"
        self.stage = str(self.destination / ".flyExplorer-copy-{00000000-0000-0000-0000-000000000001}.partial")
        self.receipt = self.base / "new-owned-receipt.bin"

    def save(self, stage=None, leaf=None):
        self.receipt.write_bytes(make_record(
            stage if stage is not None else self.stage,
            leaf if leaf is not None else self.target.name))

    def test_exact_parent_and_unicode_leaf(self):
        self.save()
        self.assertTrue(matches_owned_published_target(
            self.receipt, self.target))

    def test_unrelated_target_rejected(self):
        self.save()
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.destination / "unrelated.txt"))

    def test_unrelated_stage_parent_rejected(self):
        self.save(stage=str(self.base / "other" / Path(self.stage).name))
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.target))

    def test_truncated_and_corrupt_checksum_rejected(self):
        self.save()
        raw = self.receipt.read_bytes()
        self.receipt.write_bytes(raw[:-1])
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.target))
        damaged = bytearray(raw)
        damaged[-1] ^= 1
        self.receipt.write_bytes(damaged)
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.target))

    def test_wrong_version_rejected(self):
        self.save()
        raw = bytearray(self.receipt.read_bytes())
        struct.pack_into("<I", raw, 8, 2)
        self.receipt.write_bytes(raw)
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.target))

    def test_invalid_leaf_with_separator_rejected(self):
        self.save(leaf="other\\target.txt")
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.target))

    def test_invalid_encoded_path_rejected(self):
        self.save()
        raw = bytearray(self.receipt.read_bytes())
        raw[HEADER.size] = 0xFF
        self.receipt.write_bytes(raw)
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.target))

    def test_noncanonical_dot_segment_stage_rejected(self):
        stage = str(self.destination / "redundant" / ".." / Path(self.stage).name)
        self.save(stage=stage)
        self.assertFalse(matches_owned_published_target(
            self.receipt, self.target))

    def test_volume_serial_zero_does_not_replace_file_id_check(self):
        self.save()
        raw = bytearray(self.receipt.read_bytes())
        # Volume is a stored OS value, not a proof-of-existence sentinel.
        struct.pack_into("<Q", raw, 20, 0)
        struct.pack_into("<I", raw, HEADER.size - 4, 0)
        digest = 2166136261
        for byte in raw:
            digest = ((digest ^ byte) * 16777619) & 0xFFFFFFFF
        struct.pack_into("<I", raw, HEADER.size - 4, digest)
        self.receipt.write_bytes(raw)
        self.assertTrue(matches_owned_published_target(
            self.receipt, self.target))


if __name__ == "__main__":
    unittest.main()

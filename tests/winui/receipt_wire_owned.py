"""Read the *single newly created* v1 stage receipt for an exact owned target.

This module never enumerates stores or modifies files. Its FNV check detects
torn records only, not a malicious same-user actor; the native read-only
inspector must independently verify PublishedVerified and FileIdInfo.
"""
from __future__ import annotations

from pathlib import Path
import struct

_HEADER = struct.Struct("<8sIIIQ16sIQI")
_MAX_BYTES = 75_000


def matches_owned_published_target(receipt_file: Path, expected_target: Path) -> bool:
    """Exact v1 stage-path parent and final leaf; fail closed on bad bytes."""
    try:
        if receipt_file.is_symlink() or not receipt_file.is_file():
            return False
        size = receipt_file.stat().st_size
        if size < _HEADER.size or size > _MAX_BYTES:
            return False
        raw = receipt_file.read_bytes()
        if len(raw) != size:
            return False
        (magic, version, stage_units, leaf_units, volume, file_id,
         pid, started, saved) = _HEADER.unpack_from(raw)
        if (magic != b"FLYSTGR1" or version != 1 or
                not 0 < stage_units <= 32000 or
                not 0 < leaf_units <= 255 or
                not pid or not started or not any(file_id) or
                size != _HEADER.size + (stage_units + leaf_units) * 2):
            return False
        unsigned = raw[:_HEADER.size - 4] + b"\0\0\0\0" + raw[_HEADER.size:]
        check = 2166136261
        for byte in unsigned:
            check = ((check ^ byte) * 16777619) & 0xFFFFFFFF
        if check != saved:
            return False
        payload = raw[_HEADER.size:]
        stage = payload[:stage_units * 2].decode("utf-16-le")
        leaf = payload[stage_units * 2:].decode("utf-16-le")
        stage_path = Path(stage)
        expected = Path(expected_target)
        if (not stage_path.is_absolute() or not expected.is_absolute()
                or "\0" in stage or "\0" in leaf
                or str(stage_path) != stage
                or leaf != expected.name or Path(leaf).name != leaf):
            return False
        return stage_path.parent / leaf == expected
    except (OSError, ValueError, UnicodeError, struct.error):
        return False

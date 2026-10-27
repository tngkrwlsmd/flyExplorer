"""Redacted, read-only classification of the owned L08 WinUI hover diagnostic.

Neither UI Automation's arbitrary HelpText nor raw cursor handles are logged
by this classifier. Classification cannot replace the independent OS cursor
acceptance assertion in the owned GUI test.
"""
from __future__ import annotations

import re
from typing import NamedTuple


class PointerState(NamedTuple):
    stage: str
    entered: int
    exited: int
    cursor_set: bool


_PATTERN = re.compile(
    r"L08_(loaded|enter|exit) ENTER=([0-9]{1,5}) "
    r"EXIT=([0-9]{1,5}) CURSOR_SET=([01])",
    re.ASCII,
)


def parse_l08_pointer_help(value: object) -> PointerState | None:
    """Accept only the bounded field layout emitted by DetailColumnHandle."""
    if type(value) is not str or len(value) > 96:
        return None
    match = _PATTERN.fullmatch(value)
    if match is None:
        return None
    stage, entered, exited, cursor_set = match.groups()
    return PointerState(stage, int(entered), int(exited), cursor_set == "1")


def classify_l08_hover(
    before: PointerState | None,
    after: PointerState | None,
    native_cursor: str,
    hit_expected_thumb: bool,
) -> str:
    """Describe evidence boundaries, not a GUI PASS or a product failure."""
    if not hit_expected_thumb:
        return "non-owned-or-missed-thumb"
    if after is None:
        return "uia-diagnostic-unavailable"
    if not after.cursor_set:
        return "protected-cursor-not-set"
    if before is None:
        return "prehover-baseline-unavailable"
    if after.entered < before.entered or after.exited < before.exited:
        return "diagnostic-counters-reset"
    if after.entered == before.entered:
        return "no-new-pointer-enter-observed"
    # PointerEntered occurred during the sample window, but a later
    # PointerExited means the final OS cursor need not be the thumb's.
    # Do not misdiagnose this as a cursor override on the hovered thumb.
    if after.stage == "exit" and after.exited > before.exited:
        return "pointer-entered-then-exited"
    if native_cursor == "sizewe":
        return "pointer-entered-native-sizewe"
    if native_cursor == "arrow":
        return "pointer-entered-native-arrow"
    return "pointer-entered-native-other"


def classify_l08_cursor_reference(
    owned_edit_hit: bool,
    text_cursor: str,
    resize_cursors: tuple[str, ...],
) -> str:
    """Classify cursor-observation *evidence*, never override GUI acceptance.

    IDC_IBEAM is an independent positive control only when the point actually
    hits an owned, enabled Edit. A missing I-beam then prevents attributing
    the arrow readings on resize handles solely to the product. No return
    value from this function can satisfy the strict per-thumb SIZEWE oracle.
    """
    allowed = {"arrow", "ibeam", "sizewe", "other"}
    if (type(owned_edit_hit) is not bool or
            type(text_cursor) is not str or text_cursor not in allowed or
            type(resize_cursors) is not tuple or
            len(resize_cursors) != 3 or
            any(type(item) is not str or item not in allowed
                for item in resize_cursors)):
        return "cursor-reference-evidence-invalid"
    if not owned_edit_hit:
        return "cursor-reference-target-unverified"
    if text_cursor != "ibeam":
        return "cursor-reference-ibeam-not-observed"
    if any(cursor != "sizewe" for cursor in resize_cursors):
        return "resize-cursor-not-observed-with-valid-reference"
    return "native-cursor-observations-match"

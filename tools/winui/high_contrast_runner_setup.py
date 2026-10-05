"""Deterministic Windows Settings setup/restore for High Contrast acceptance.

This controls runner state only. Product acceptance stays in the owned GUI test.
"""
from __future__ import annotations

import argparse
import subprocess
import time
from typing import Callable, TypeVar

from high_contrast_state import query

T = TypeVar("T")


class SetupTimeout(AssertionError):
    pass


def _pywinauto():
    from pywinauto import Desktop, keyboard
    from pywinauto.findwindows import ElementNotFoundError
    from pywinauto.timings import TimeoutError as PywinautoTimeoutError

    return Desktop, keyboard, (ElementNotFoundError, PywinautoTimeoutError)


def wait_for(
    fn: Callable[[], T],
    label: str,
    seconds: float = 25,
    interval: float = 0.25,
) -> T:
    _, _, retry_errors = _pywinauto()
    deadline = time.monotonic() + seconds
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            value = fn()
            if value:
                return value
        except retry_errors as exc:
            last_error = exc
        time.sleep(interval)
    detail = f"; last_transient={last_error!r}" if last_error else ""
    raise SetupTimeout(f"{label}{detail}")


def _settings():
    Desktop, _, _ = _pywinauto()
    windows = [
        window
        for window in Desktop(backend="uia").windows()
        if window.window_text() in ("설정", "Settings")
    ]
    return windows[-1] if windows else None


def close_settings() -> None:
    Desktop, _, _ = _pywinauto()
    failures: list[str] = []
    for window in Desktop(backend="uia").windows():
        if window.window_text() in ("설정", "Settings"):
            try:
                window.close()
            except Exception as exc:
                failures.append(repr(exc))
    if failures:
        print("HIGH_CONTRAST_SETTINGS_CLOSE_WARN", failures, flush=True)
    time.sleep(0.8)


def _named_list(*names: str):
    window = _settings()
    if window is None:
        return None
    expected = set(names)
    return next(
        (
            element
            for element in window.descendants(control_type="ListItem")
            if (element.window_text() or "").strip() in expected
        ),
        None,
    )


def _controls():
    window = _settings()
    if window is None:
        return None
    combo = next(
        (
            element
            for element in window.descendants(control_type="ComboBox")
            if element.is_visible()
        ),
        None,
    )
    apply = next(
        (
            element
            for element in window.descendants(control_type="Button")
            if element.element_info.automation_id
            == "HighContrastThemeApplyButton"
        ),
        None,
    )
    return (combo, apply) if combo is not None and apply is not None else None


def open_contrast_controls():
    _, keyboard, _ = _pywinauto()
    close_settings()
    subprocess.Popen(["cmd", "/c", "start", "", "ms-settings:"])
    wait_for(_settings, "Settings window missing")
    accessibility = wait_for(
        lambda: _named_list("접근성", "Accessibility"),
        "Accessibility navigation item missing",
    )
    accessibility.click_input()
    card = wait_for(
        lambda: _named_list("대비 테마", "Contrast themes"),
        "Contrast themes card missing",
    )
    card.set_focus()
    keyboard.send_keys("{ENTER}")
    return wait_for(_controls, "Contrast themes controls missing")


def set_target(enabled: bool) -> None:
    _, keyboard, _ = _pywinauto()
    before = query()
    print(
        "HIGH_CONTRAST_SETUP_BEFORE "
        f"target={enabled} enabled={before.enabled} scheme={before.scheme!r}",
        flush=True,
    )
    if before.enabled == enabled:
        return

    combo, apply = open_contrast_controls()
    try:
        try:
            combo.select("밤하늘" if enabled else "없음")
        except Exception as exc:
            print("HIGH_CONTRAST_SETUP_SELECT_FALLBACK", repr(exc), flush=True)
            combo.click_input()
            keyboard.send_keys("{END}{ENTER}" if enabled else "{HOME}{ENTER}")
        apply.click_input()
        wait_for(
            lambda: query().enabled == enabled,
            "High Contrast target state was not reached",
            seconds=30,
        )
    finally:
        close_settings()

    after = query()
    print(
        "HIGH_CONTRAST_SETUP_AFTER "
        f"target={enabled} enabled={after.enabled} scheme={after.scheme!r}",
        flush=True,
    )
    if after.enabled != enabled:
        raise AssertionError(
            f"High Contrast state mismatch: expected={enabled} actual={after.enabled}"
        )


def check() -> None:
    _pywinauto()
    state = query()
    print(
        "HIGH_CONTRAST_SETUP_CHECK_PASS "
        f"enabled={state.enabled} scheme={state.scheme!r}",
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("on", "off", "status"), nargs="?", default="status"
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        check()
        return 0
    if args.action == "status":
        state = query()
        print(
            "HIGH_CONTRAST_SETUP_STATUS "
            f"enabled={state.enabled} scheme={state.scheme!r}",
            flush=True,
        )
        return 0

    set_target(args.action == "on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

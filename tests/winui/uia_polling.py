"""Shared bounded UIA polling that only retries known transient automation errors."""
from __future__ import annotations

import time
from typing import Callable, TypeVar

from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError as PywinautoTimeoutError

T = TypeVar("T")

TRANSIENT_UIA_ERRORS = (ElementNotFoundError, PywinautoTimeoutError)


def wait_until(
    predicate: Callable[[], T],
    label: str,
    *,
    seconds: float,
    interval: float,
) -> T:
    """Return the first truthy predicate value; never hide programming errors."""
    deadline = time.monotonic() + seconds
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except TRANSIENT_UIA_ERRORS as exc:
            last_error = exc
        time.sleep(interval)

    detail = f"; last_transient={last_error!r}" if last_error else ""
    raise AssertionError(f"{label}{detail}")

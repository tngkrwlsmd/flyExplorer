"""Side-effect-free query for the current Windows High Contrast state."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class HighContrastState:
    enabled: bool
    scheme: str | None


class _HighContrast(ctypes.Structure):
    _fields_ = (
        ("cbSize", wintypes.UINT),
        ("dwFlags", wintypes.DWORD),
        ("lpszDefaultScheme", wintypes.LPWSTR),
    )


def query() -> HighContrastState:
    if os.name != "nt":
        raise RuntimeError("High Contrast state is only available on Windows")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    state = _HighContrast()
    state.cbSize = ctypes.sizeof(state)
    if not user32.SystemParametersInfoW(
        0x0042, state.cbSize, ctypes.byref(state), 0
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return HighContrastState(bool(state.dwFlags & 1), state.lpszDefaultScheme)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    state = query()
    print(
        "HIGH_CONTRAST_STATE "
        f"enabled={state.enabled} scheme={state.scheme!r}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only sentinel for optional historical fxfile user settings."""
from __future__ import annotations

from pathlib import Path
import hashlib
import os

LEGACY_NAMES = (
    "fxfile.conf",
    "fxfile-main.conf",
    "fxfile-toolbar.dat",
    "fxfile-coolbar.dat",
    "fxfile-dlg_state.conf",
    "fxfile-folder_layout.conf",
)


def default_legacy_root() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not defined")
    return Path(appdata) / "fxfile" / "conf"


def snapshot_legacy_profile(
    root: Path | None = None,
) -> tuple[Path, dict[str, bytes | None]]:
    root = Path(root) if root is not None else default_legacy_root()
    state: dict[str, bytes | None] = {}
    for name in LEGACY_NAMES:
        path = root / name
        state[name] = (
            hashlib.sha256(path.read_bytes()).digest()
            if path.is_file()
            else None
        )
    return root, state


def assert_legacy_profile_unchanged(
    root: Path, state: dict[str, bytes | None]
) -> None:
    root = Path(root)
    for name, before in state.items():
        path = root / name
        if before is None:
            assert not path.exists(), (
                f"test created previously absent real user setting: {path}"
            )
        else:
            assert path.is_file(), f"test removed existing real user setting: {path}"
            after = hashlib.sha256(path.read_bytes()).digest()
            assert after == before, f"test changed existing real user setting: {path}"


def present_count(state: dict[str, bytes | None]) -> int:
    return sum(value is not None for value in state.values())

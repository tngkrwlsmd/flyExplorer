"""Owned High Contrast ON acceptance. Never changes global accessibility state."""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, TypeVar

from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile

sys.path.insert(0, str(ROOT / "tools" / "winui"))
from high_contrast_state import query as current_hc

import psutil
from PIL import ImageGrab
from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError as PywinautoTimeoutError

T = TypeVar("T")

u = c.WinDLL("user32", use_last_error=True)
u.GetForegroundWindow.restype = w.HWND
u.SetWindowPos.argtypes = (
    w.HWND,
    w.HWND,
    c.c_int,
    c.c_int,
    c.c_int,
    c.c_int,
    w.UINT,
)
u.PostMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPARAM)


class AcceptanceFailure(AssertionError):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


TRANSIENT_UIA_ERRORS = (ElementNotFoundError, PywinautoTimeoutError)


def wait_for(
    fn: Callable[[], T],
    label: str,
    *,
    category: str,
    seconds: float = 30,
    interval: float = 0.2,
    on_timeout: Callable[[BaseException | None], dict[str, object]] | None = None,
) -> T:
    deadline = time.monotonic() + seconds
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            value = fn()
            if value:
                return value
        except TRANSIENT_UIA_ERRORS as exc:
            last_error = exc
        time.sleep(interval)

    details: dict[str, object] = {}
    if on_timeout is not None:
        details = on_timeout(last_error)
    suffix = " " + json.dumps(details, ensure_ascii=False) if details else ""
    raise AcceptanceFailure(category, label + suffix)


def _diagnostic_snapshot(
    proc: subprocess.Popen,
    exe: Path,
    hwnd: int | None,
    started: float,
    root: Path,
    last_error: BaseException | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "pid": proc.pid,
        "process_alive": proc.poll() is None,
        "exit_code": proc.poll(),
        "hwnd": hwnd,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "last_uia_exception": repr(last_error) if last_error else None,
    }

    try:
        windows = Desktop(backend="uia").windows(process=proc.pid)
        payload["window_count"] = len(windows)
        payload["window_titles"] = [window.window_text() for window in windows]
        payload["window_handles"] = [window.handle for window in windows]
    except Exception as exc:
        payload["window_probe_error"] = repr(exc)

    try:
        payload["process_exe"] = (
            str(Path(psutil.Process(proc.pid).exe()).resolve())
            if proc.poll() is None
            else None
        )
        payload["expected_exe"] = str(exe.resolve())
    except Exception as exc:
        payload["process_probe_error"] = repr(exc)

    try:
        payload["left_files_exists"] = bool(
            hwnd
            and Desktop(backend="uia")
            .window(handle=hwnd)
            .child_window(auto_id="LeftFiles")
            .exists(timeout=0.2)
        )
    except Exception as exc:
        payload["left_files_probe_error"] = repr(exc)

    try:
        state = current_hc()
        payload["high_contrast_enabled"] = state.enabled
        payload["high_contrast_scheme"] = state.scheme
    except Exception as exc:
        payload["high_contrast_probe_error"] = repr(exc)

    if hwnd:
        try:
            win = Desktop(backend="uia").window(handle=hwnd)
            rect = win.rectangle()
            path = root / "readiness-timeout.png"
            ImageGrab.grab(
                bbox=(rect.left, rect.top, rect.right, rect.bottom),
                all_screens=True,
            ).save(path)
            payload["screenshot"] = str(path)
        except Exception as exc:
            payload["screenshot_error"] = repr(exc)

    print("HIGH_CONTRAST_READINESS_DIAGNOSTIC", json.dumps(payload, ensure_ascii=False), flush=True)
    return payload


def main(
    configuration: str = "Release",
    exe_override: Path | None = None,
    evidence_prefix: str = "high-contrast",
) -> int:
    state = current_hc()
    if not state.enabled:
        print("HIGH_CONTRAST_ON_REQUIRED", repr(state.scheme), flush=True)
        return 2

    exe = exe_override or app_exe(configuration)
    exe = exe.resolve()
    if not exe.is_file():
        raise AcceptanceFailure("CANDIDATE_BINARY_MISSING", str(exe))

    legacy_root, before = snapshot_legacy_profile()
    root = ROOT / "logs" / "high-contrast"
    root.mkdir(parents=True, exist_ok=True)
    owned = Path(tempfile.mkdtemp(prefix="high-contrast-owned-", dir=root))
    folder = owned / "source"
    folder.mkdir()
    for name in ("contrast-alpha.txt", "contrast-beta.txt", "한국어-고대비.txt"):
        (folder / name).write_text("owned high contrast", encoding="utf-8")

    env = os.environ.copy()
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        dest = owned / key.lower()
        dest.mkdir()
        env[key] = str(dest)

    started = time.monotonic()
    proc = subprocess.Popen([str(exe), str(folder)], cwd=exe.parent, env=env)
    hwnd: int | None = None
    passed = False
    primary_error: BaseException | None = None
    print(f"READINESS_STAGE=PROCESS_STARTED pid={proc.pid}", flush=True)

    def snapshot(last_error: BaseException | None) -> dict[str, object]:
        return _diagnostic_snapshot(
            proc, exe, hwnd, started, root, last_error
        )

    try:
        def window_ready():
            nonlocal hwnd
            return_code = proc.poll()
            if return_code is not None:
                raise AcceptanceFailure(
                    "CANDIDATE_PROCESS_EXIT",
                    "flyExplorer exited before High Contrast window appeared: "
                    f"returncode={return_code}",
                )

            try:
                actual_exe = Path(psutil.Process(proc.pid).exe()).resolve()
            except psutil.NoSuchProcess as exc:
                raise AcceptanceFailure(
                    "CANDIDATE_PROCESS_EXIT",
                    f"flyExplorer process vanished before window discovery: {exc}",
                ) from exc
            if actual_exe != exe:
                raise AcceptanceFailure(
                    "CANDIDATE_PID_MISMATCH",
                    f"flyExplorer PID mismatch: expected={exe} actual={actual_exe}",
                )

            windows = [
                window
                for window in Desktop(backend="uia").windows(process=proc.pid)
                if "flyExplorer" in window.window_text()
            ]
            if len(windows) != 1:
                return False
            hwnd = windows[0].handle
            return True

        wait_for(
            window_ready,
            "High Contrast owned flyExplorer window did not start",
            category="CANDIDATE_WINDOW_TIMEOUT",
            on_timeout=snapshot,
        )
        print(f"READINESS_STAGE=WINDOW_FOUND hwnd={hwnd}", flush=True)

        win = Desktop(backend="uia").window(handle=hwnd)
        wait_for(
            lambda: win.child_window(auto_id="LeftFiles").exists(timeout=0.2),
            "High Contrast owned file list did not become ready",
            category="CANDIDATE_UIA_CONTROL_TIMEOUT",
            on_timeout=snapshot,
        )
        print("READINESS_STAGE=CORE_UIA_READY", flush=True)

        win.set_focus()
        if not u.SetWindowPos(hwnd, None, 40, 30, 1100, 720, 0x0014):
            raise AcceptanceFailure(
                "CANDIDATE_INTERACTION_NOT_READY",
                "High Contrast acceptance SetWindowPos failed",
            )
        wait_for(
            lambda: abs(win.rectangle().width() - 1100) <= 3,
            "High Contrast acceptance size did not apply",
            category="CANDIDATE_INTERACTION_NOT_READY",
            on_timeout=snapshot,
        )
        if u.GetForegroundWindow() != hwnd:
            raise AcceptanceFailure(
                "CANDIDATE_INTERACTION_NOT_READY",
                "High Contrast window did not become foreground",
            )
        if not current_hc().enabled:
            raise AcceptanceFailure(
                "WINDOWS_SETTINGS_FAILURE",
                "High Contrast turned off during acceptance",
            )
        print("READINESS_STAGE=INTERACTION_READY", flush=True)

        named = (
            "BackButton",
            "ForwardButton",
            "UpButton",
            "AddressBox",
            "QuickSearchBox",
            "SearchPanelButton",
            "LeftTabs",
            "RightTabs",
            "LeftNameSortButton",
            "RightNameSortButton",
            "LeftFiles",
            "RightFiles",
            "HomeButton",
            "StatusText",
        )
        for key in named:
            element = win.child_window(auto_id=key)
            if not element.exists(timeout=2):
                raise AcceptanceFailure(
                    "PRODUCT_ASSERTION_FAILURE",
                    f"missing automation element: {key}",
                )
            if not element.element_info.name:
                raise AcceptanceFailure(
                    "PRODUCT_ASSERTION_FAILURE",
                    f"missing accessible name: {key}",
                )

        rows = [
            row
            for row in win.child_window(auto_id="LeftFiles").descendants()
            if row.element_info.control_type == "ListItem"
        ]
        if not rows:
            raise AcceptanceFailure(
                "PRODUCT_ASSERTION_FAILURE",
                "High Contrast owned file rows missing",
            )
        rows[0].select()
        wait_for(
            lambda: any(
                row.is_selected()
                for row in win.child_window(auto_id="LeftFiles").descendants()
                if row.element_info.control_type == "ListItem"
            ),
            "High Contrast list selection did not become visible to UIA",
            category="PRODUCT_ASSERTION_FAILURE",
            on_timeout=snapshot,
        )

        rect = win.rectangle()
        shell_image = root / f"{evidence_prefix}-shell.png"
        ImageGrab.grab(
            bbox=(rect.left, rect.top, rect.right, rect.bottom),
            all_screens=True,
        ).save(shell_image)
        print("HIGH_CONTRAST_SHELL_SCREENSHOT", shell_image, flush=True)

        win.child_window(auto_id="SearchPanelButton").click_input()
        wait_for(
            lambda: (
                win.child_window(auto_id="SearchScopeBox").exists(timeout=0.2)
                and win.child_window(auto_id="SearchScopeBox").is_visible()
            ),
            "High Contrast search controls did not become visible",
            category="PRODUCT_ASSERTION_FAILURE",
            on_timeout=snapshot,
        )
        search_image = root / f"{evidence_prefix}-search.png"
        rect = win.rectangle()
        ImageGrab.grab(
            bbox=(rect.left, rect.top, rect.right, rect.bottom),
            all_screens=True,
        ).save(search_image)
        print("HIGH_CONTRAST_SEARCH_SCREENSHOT", search_image, flush=True)

        if not current_hc().enabled:
            raise AcceptanceFailure(
                "WINDOWS_SETTINGS_FAILURE",
                "High Contrast changed during screenshot capture",
            )
        print("OWNED_HIGH_CONTRAST_UIA_AND_SELECTION_PASS", True, flush=True)
        print("OWNED_HIGH_CONTRAST_SEARCH_SURFACE_PASS", True, flush=True)
        passed = True
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        cleanup_errors: list[str] = []
        try:
            if proc.poll() is None:
                if hwnd is not None:
                    u.PostMessageW(hwnd, 0x10, 0, 0)
                    try:
                        proc.wait(timeout=12)
                    except subprocess.TimeoutExpired:
                        proc.terminate()
                        proc.wait(timeout=7)
                else:
                    proc.terminate()
                    proc.wait(timeout=7)
        except Exception as exc:
            cleanup_errors.append(f"process_cleanup={exc!r}")

        try:
            assert_legacy_profile_unchanged(legacy_root, before)
            print("ORIGINAL_SIX_USER_SETTINGS_IDENTICAL", True, flush=True)
        except Exception as exc:
            cleanup_errors.append(f"profile_guard={exc!r}")

        try:
            if not current_hc().enabled:
                cleanup_errors.append("high_contrast_state_changed=False")
        except Exception as exc:
            cleanup_errors.append(f"high_contrast_query={exc!r}")

        if passed and not cleanup_errors and proc.returncode == 0:
            shutil.rmtree(owned)
        else:
            print("OWNED_HIGH_CONTRAST_FIXTURE_RETAINED", owned, flush=True)

        if cleanup_errors:
            print("HIGH_CONTRAST_CLEANUP_ERRORS", cleanup_errors, flush=True)
            if primary_error is None:
                raise AcceptanceFailure(
                    "CLEANUP_FAILURE",
                    "; ".join(cleanup_errors),
                )

    return 0 if passed and proc.returncode == 0 else 1


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configuration", choices=("Debug", "Release"), nargs="?", default="Release")
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--evidence-prefix", default="high-contrast")
    args = parser.parse_args(argv)

    try:
        return main(args.configuration, args.exe, args.evidence_prefix)
    except AcceptanceFailure as exc:
        print(f"FAILURE_CATEGORY={exc.category}", flush=True)
        raise
    except (AttributeError, NameError, TypeError) as exc:
        print("FAILURE_CATEGORY=HELPER_PROGRAMMING_ERROR", flush=True)
        raise
    except Exception:
        print("FAILURE_CATEGORY=CANDIDATE_UIA_FAILURE", flush=True)
        raise


if __name__ == "__main__":
    raise SystemExit(cli())

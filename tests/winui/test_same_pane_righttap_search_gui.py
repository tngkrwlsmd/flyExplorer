"""Owned GUI regression: physical same-pane right click must not cancel a running search.

Uses only disposable local files, an isolated private profile, and a uniquely
owned flyExplorer window. Refuses to click a pixel occupied by another process.
"""
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from pywinauto import Desktop, keyboard, mouse
import benchmark_filtered_folder_gui as h

SOURCE_SHA = "158f2aada9333b8b894ad26aba714ec8d6f82e45"
EXE_SHA256 = "0ef122fc6100fa94914ad5fb1c921d592f8162853fe3b699304ef184ccae9f25"
EXE = Path(r"C:\dev\flyExplorer\logs\righttap-release-158f2aad-20261101\Release\flyExplorer.exe")
BASE = Path(r"C:\dev\flyExplorer\logs\righttap-search-owned-gui-20261101")
FILE_COUNT = 18000


def _selected_file(app, name):
    rows = [row for row in app.rows("Left") if name in row.window_text()]
    return rows[0] if len(rows) == 1 else None


def _owned_menu_visible(app):
    for window in Desktop(backend="uia").windows(process=app.app.pid):
        try:
            for item in window.descendants(control_type="MenuItem"):
                if item.element_info.process_id == app.app.pid and (
                    "속성" in item.window_text() or
                    "추가 옵션 표시" in item.window_text()
                ):
                    return True
        except (LookupError, RuntimeError, OSError):
            continue
    return False


def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise AssertionError("Refuse existing GUI result or owned fixture directory")
    if not EXE.is_file() or hashlib.sha256(EXE.read_bytes()).hexdigest() != EXE_SHA256:
        raise AssertionError("Exact candidate Release executable missing or changed")
    if not (EXE.parent / "FlyShellIsolationHelper.exe").is_file():
        raise AssertionError("Required private shell helper is missing")

    BASE.mkdir(parents=True, exist_ok=True)
    h.BASE = BASE
    fixture = Path(tempfile.mkdtemp(prefix="righttap-owned-", dir=BASE)).resolve()
    quick = fixture / "quick"
    slow = fixture / "slow"
    quick.mkdir()
    slow.mkdir()
    anchor = quick / "righttap-anchor.txt"
    anchor_bytes = b"righttap-test-owned-anchor-unchanged"
    anchor.write_bytes(anchor_bytes)
    survivor = slow / "righttap-owned-00000.txt"
    payload = b"test-owned-no-content-needle" + b"x" * 995
    report = {"source": SOURCE_SHA, "exe_sha256": EXE_SHA256,
              "slow_file_count": FILE_COUNT, "physical_click_attempted": False,
              "search_applied_after_right_click": False}
    passed = False
    try:
        for i in range(FILE_COUNT):
            (slow / f"righttap-owned-{i:05d}.txt").write_bytes(payload)
        baseline = hashlib.sha256(survivor.read_bytes()).hexdigest()
        with h.App(EXE, quick, "righttap-search", "dark") as app:
            h.wait(lambda: _selected_file(app, anchor.name),
                   "Test-owned anchor file not listed", seconds=25).select()
            h.wait(lambda: _selected_file(app, anchor.name) is not None and
                   _selected_file(app, anchor.name).is_selected(),
                   "Anchor selection not committed", seconds=10)

            app.el("SearchPanelButton").invoke()
            h.wait(lambda: app.el("SearchRunButton").is_enabled(),
                   "Search panel not opened", seconds=10)
            assert not app.el("SearchRememberBox").get_toggle_state()
            app.el("SearchScopeBox").set_edit_text(str(slow))
            app.el("SearchTermBox").set_edit_text("righttap-owned-")
            app.el("SearchContentBox").set_edit_text(
                "needle-absent-from-all-test-files")
            app.el("SearchRunButton").invoke()
            h.wait(lambda: app.el("SearchCancelButton").is_enabled(),
                   "Search did not enter in-flight state", seconds=7)
            assert not app.el("SearchRunButton").is_enabled()
            assert "검색 중" in app.el("SearchActiveScopeText").window_text()
            report["search_inflight_before_right_click"] = True

            item = h.wait(lambda: _selected_file(app, anchor.name),
                          "Owned anchor row disappeared", seconds=5).rectangle()
            viewport = app.el("LeftFiles").rectangle()
            left, right = max(item.left, viewport.left), min(item.right, viewport.right)
            top, bottom = max(item.top, viewport.top), min(item.bottom, viewport.bottom)
            if right-left <= 35 or bottom-top <= 8:
                raise AssertionError("Owned file row not visibly clickable")
            cx, cy = left + min(45, (right-left)//2), (top+bottom)//2
            if not (viewport.left < cx < viewport.right and
                    viewport.top < cy < viewport.bottom):
                raise AssertionError("Right-click outside owned list viewport")

            app.win.set_focus()
            if h.owner(h.u.GetForegroundWindow()) != app.app.pid:
                raise AssertionError("Other process owns foreground; no click")
            h.u.WindowFromPoint.argtypes = (wintypes.POINT,)
            h.u.WindowFromPoint.restype = wintypes.HWND
            pixel = h.u.WindowFromPoint(wintypes.POINT(cx, cy))
            if not pixel or h.owner(pixel) != app.app.pid:
                raise AssertionError("Other process owns right-click pixel; no click")
            if not app.el("SearchCancelButton").is_enabled():
                raise AssertionError("Search completed before physical right-click")
            mouse.click(button="right", coords=(cx, cy))
            report["physical_click_attempted"] = True
            h.wait(lambda: _owned_menu_visible(app),
                   "Actual file context menu did not open", seconds=8)
            report["physical_menu_opened"] = True
            if h.owner(h.u.GetForegroundWindow()) != app.app.pid:
                raise AssertionError("Foreign foreground after context menu; no input")
            keyboard.send_keys("{ESC}")
            h.wait(lambda: not _owned_menu_visible(app),
                   "Owned context menu did not dismiss", seconds=8)

            h.wait(lambda:
                   "검색 결과 0개" in app.el("SearchCountText").window_text() and
                   not app.el("SearchCancelButton").is_enabled(),
                   "Running search did not complete after same-pane right click",
                   seconds=95)
            assert str(slow).casefold() in (
                app.el("SearchActiveScopeText").window_text().casefold())
            assert "검색 중" not in app.el("SearchActiveScopeText").window_text()
            assert str(quick).casefold() in (
                app.el("AddressBox").get_value().casefold())
            assert _selected_file(app, anchor.name) is not None
            report["search_applied_after_right_click"] = True
            report["anchor_unchanged"] = anchor.read_bytes() == anchor_bytes
            report["slow_sample_unchanged"] = (
                hashlib.sha256(survivor.read_bytes()).hexdigest() == baseline)
        report["app"] = app.report
        if not all((report["anchor_unchanged"], report["slow_sample_unchanged"],
                    app.report["normal_exit"],
                    app.report["original_settings_unchanged"],
                    app.report["profile_removed"])):
            raise AssertionError("Owned content/normal-close/profile condition failed")
        passed = True
    finally:
        if anchor.exists():
            report["anchor_unchanged_after_exit"] = anchor.read_bytes() == anchor_bytes
        if passed:
            if fixture.parent != BASE.resolve() or fixture.is_symlink():
                raise AssertionError("Untrusted fixture cleanup path")
            shutil.rmtree(fixture)
            report["fixture_removed"] = True
        (BASE / "result.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("RIGHTTAP_SEARCH_GUI_RESULT=" +
              json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

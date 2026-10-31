"""R01: invoke only Properties from owned selected and background menus."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from ctypes import wintypes as w

from pywinauto import mouse
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe


def main(remaining_only=False):
    base = ROOT / "logs" / ("r01-properties-menus-remaining-20261031" if remaining_only
                            else "r01-properties-menus-20261031")
    base.mkdir(parents=True, exist_ok=True)
    h.BASE = base
    fixture = Path(tempfile.mkdtemp(prefix="fixture-", dir=base)).resolve()
    first, second = fixture / "FirstMenu", fixture / "SecondMenu"
    first.mkdir()
    second.mkdir()
    (first / "r01-item.txt").write_bytes(b"first properties menu owned\n")
    (second / "r01-other.txt").write_bytes(b"second properties menu owned\n")
    before = {p.relative_to(fixture).as_posix(): p.read_bytes()
              for p in fixture.rglob("*") if p.is_file()}
    result = {"source": subprocess.check_output(["git", "-C", str(ROOT),
        "rev-parse", "HEAD"], text=True).strip(), "frames": []}
    helper = None
    sheet = None
    passed = False
    h.u.IsWindow.argtypes = (w.HWND,)
    h.u.IsWindow.restype = w.BOOL
    h.u.GetAncestor.argtypes = (w.HWND, w.UINT)
    h.u.GetAncestor.restype = w.HWND
    h.u.WindowFromPoint.argtypes = (w.POINT,)
    h.u.WindowFromPoint.restype = w.HWND
    try:
        with h.App(app_exe("Release"), first, "r01-menus", "dark") as app:
            def row(side, name):
                return next((r for r in app.rows(side) if name in r.window_text()), None)

            def selected(side, name):
                item = row(side, name)
                return item is not None and item.is_selected()

            def click_row(side, name):
                item = h.wait(lambda: row(side, name), "owned row absent: " + name)
                area, box = app.el(side + "Files").rectangle(), item.rectangle()
                x = max(area.left, box.left) + 30
                y = (max(area.top, box.top) + min(area.bottom, box.bottom)) // 2
                assert area.left < x < area.right and area.top < y < area.bottom
                assert h.owner(h.u.GetForegroundWindow()) == app.app.pid
                mouse.click(coords=(x, y))
                h.wait(lambda: selected(side, name),
                       "owned item not selected")

            def properties_item():
                roots = [app.win]
                roots += [x for x in h.Desktop(backend="uia").windows(process=app.app.pid)
                          if x.handle != app.hwnd]
                found = {}
                for root in roots:
                    for item in root.descendants(control_type="MenuItem"):
                        if item.window_text() == "속성" and item.is_visible():
                            r = item.rectangle()
                            found[(r.left, r.top, r.right, r.bottom)] = item
                return next(iter(found.values())) if len(found) == 1 else None

            def invoke_and_close(expected_name, tag):
                nonlocal helper, sheet
                item = h.wait(properties_item, "owned Properties menu item absent")
                assert item.is_enabled()
                app.capture(tag + "-menu")
                previous = {p.pid for p in app.process.children(recursive=True)}
                item.invoke()

                def spawned():
                    matches = []
                    for child in app.process.children(recursive=True):
                        try:
                            if (child.pid not in previous and
                                Path(child.exe()).resolve() == app.exe.parent / "FlyShellIsolationHelper.exe" and
                                "--context-properties" in child.cmdline()):
                                matches.append(child)
                        except h.psutil.Error:
                            pass
                    return matches[0] if len(matches) == 1 else None

                helper = h.wait(spawned, "isolated properties helper absent", 10)

                def dialog():
                    for win in h.Desktop(backend="uia").windows(process=helper.pid):
                        if (win.is_visible() and win.class_name() == "#32770" and
                            expected_name in win.window_text() and "속성" in win.window_text()):
                            return win
                    return None

                sheet = h.wait(dialog, "exact target Properties sheet absent", 12)
                sheet.set_focus()
                assert h.owner(h.u.GetForegroundWindow()) == helper.pid
                r = sheet.rectangle()
                assert 0 <= r.left < r.right <= h.u.GetSystemMetrics(0)
                assert 0 <= r.top < r.bottom <= h.u.GetSystemMetrics(1)
                for x, y in ((r.left+8, r.top+8), (r.right-8, r.bottom-8)):
                    assert h.u.GetAncestor(h.u.WindowFromPoint(w.POINT(x, y)), 2) == sheet.handle
                image = base / (tag + "-properties.png")
                h.ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom),
                                 include_layered_windows=True).save(image)
                result["frames"].append({"name": image.name,
                    "sha256": hashlib.sha256(image.read_bytes()).hexdigest()})
                result[tag] = {"target": expected_name, "visible": True,
                               "dpi": h.u.GetDpiForWindow(sheet.handle)}
                assert h.owner(sheet.handle) == helper.pid
                assert h.u.PostMessageW(sheet.handle, 0x10, 0, 0)
                h.wait(lambda: not h.u.IsWindow(sheet.handle), "owned sheet did not close", 10)
                assert helper.wait(timeout=12) == 0
                helper, sheet = None, None
                app.win.set_focus()
                h.wait(lambda: "속성 창이 닫혔습니다" in app.el("StatusText").window_text(),
                       "Properties close did not settle")
                result[tag]["closed"] = True
                print("R01_STAGE_" + tag.upper() + "=PASS", flush=True)

            h.wait(lambda: row("Left", "r01-item.txt") is not None and
                   app.el("UpButton").is_enabled(), "initial fixture not ready")
            if not remaining_only:
                click_row("Left", "r01-item.txt")
                assert h.owner(h.u.GetForegroundWindow()) == app.app.pid
                h.u.keybd_event(0x5d, 0, 0, 0)
                h.u.keybd_event(0x5d, 0, 2, 0)
                invoke_and_close("r01-item.txt", "selected")
                h.wait(lambda: selected("Left", "r01-item.txt"), "file selection changed")
            else:
                result["selected_case_reused"] = "41156724867/b10bc7a6/9d7624fa"
            # The hidden pane-title Invoke changes the model but need not move
            # keyboard focus. A Control key from the old Left row can activate
            # Left again. Establish a real Right input owner before Ctrl+L.
            click_row("Right", "r01-item.txt")
            h.wait(lambda: app.el("RightFiles").has_keyboard_focus() or any(
                r.has_keyboard_focus() for r in app.rows("Right")),
                "Right input owner not established")
            app.keys("^l")
            app.el("AddressBox").set_edit_text(str(second))
            app.el("AddressBox").set_focus()
            app.keys("{ENTER}")
            h.wait(lambda: row("Right", "r01-other.txt") is not None and
                   app.el("AddressBox").get_value().casefold() == str(second).casefold() and
                   app.el("UpButton").is_enabled(), "right owned folder not committed")
            click_row("Right", "r01-other.txt")
            area = app.el("RightFiles").rectangle()
            last_bottom = max(r.rectangle().bottom for r in app.rows("Right"))
            blank = (area.left + 40, max(area.top + 100, last_bottom + 30))
            assert area.left < blank[0] < area.right and area.top < blank[1] < area.bottom - 8
            assert h.owner(h.u.GetForegroundWindow()) == app.app.pid
            mouse.click(button="right", coords=blank)
            invoke_and_close("SecondMenu", "current-folder")
            assert app.el("AddressBox").get_value().casefold() == str(second).casefold()
            assert row("Left", "r01-item.txt") is not None
            assert {p.relative_to(fixture).as_posix(): p.read_bytes()
                    for p in fixture.rglob("*") if p.is_file()} == before
            result["original_bytes_preserved"] = True
        result["app"] = app.report
        assert app.report["normal_exit"] and app.report["profile_removed"]
        passed = True
    finally:
        if sheet is not None and helper is not None:
            if h.u.IsWindow(sheet.handle) and h.owner(sheet.handle) == helper.pid:
                h.u.PostMessageW(sheet.handle, 0x10, 0, 0)
        if passed:
            assert fixture.parent == base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        (base / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("R01_PROPERTIES_MENUS_RESULT=" + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()

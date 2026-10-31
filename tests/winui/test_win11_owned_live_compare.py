"""Real Explorer/app comparison using one disposable folder and new HWND only.

Observe menus; never execute clipboard, delete, share, archive or provider verbs.
Native captures exclude the personal navigation/history area.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import winreg

import pythoncom
import win32com.client
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe


def main():
    base = ROOT / "logs" / "win11-live-compare-20261031"
    base.mkdir(parents=True, exist_ok=True)
    h.BASE = base
    fixture = Path(tempfile.mkdtemp(prefix="fixture-", dir=base)).resolve()
    (fixture / "CompareOwned.txt").write_bytes(b"owned comparison text\n")
    (fixture / "CompareOwned.md").write_bytes(b"# owned comparison\n")
    (fixture / "Nested").mkdir()
    (fixture / "Nested" / "NestedOwned.txt").write_bytes(b"owned nested\n")
    before = {p.relative_to(fixture).as_posix(): p.read_bytes()
              for p in fixture.rglob("*") if p.is_file()}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
        theme = "light" if winreg.QueryValueEx(key, "AppsUseLightTheme")[0] else "dark"
    result = {"source": subprocess.check_output(["git", "-C", str(ROOT),
        "rev-parse", "HEAD"], text=True).strip(), "theme": theme, "frames": []}
    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch("Shell.Application")
    original = {int(x.HWND) for x in shell.Windows()}
    native = None
    passed = False
    h.u.IsWindow.argtypes = (w.HWND,)
    h.u.IsWindow.restype = w.BOOL

    def windows():
        return {x.handle: x for x in h.Desktop(backend="uia").windows()}

    def capture(tag, rect, pid):
        assert h.owner(h.u.GetForegroundWindow()) == pid, "foreign foreground"
        left, top, right, bottom = rect
        assert 0 <= left < right <= h.u.GetSystemMetrics(0)
        assert 0 <= top < bottom <= h.u.GetSystemMetrics(1)
        path = base / (tag + ".png")
        h.ImageGrab.grab(bbox=rect, include_layered_windows=True).save(path)
        assert path.stat().st_size < 240000
        result["frames"].append({"name": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

    def observe_menu(host, pid, previous, tag, markers=()):
        def peers():
            roots = [host]
            for handle, win in windows().items():
                if handle not in previous and h.owner(handle) == pid:
                    roots.append(win)
            found = {}
            for root in roots:
                for item in root.descendants(control_type="MenuItem"):
                    if item.is_visible() and "MenuBarItem" not in item.element_info.class_name:
                        r = item.rectangle()
                        if r.width() > 10 and r.height() > 5:
                            found[(r.left, r.top, r.right, r.bottom)] = item
            items = list(found.values())
            if markers and not any(any(mark in x.window_text() for mark in markers)
                                   for x in items):
                return None
            return items
        items = h.wait(peers, "visible owned menu absent: " + tag, 10)
        result[tag] = [{"label": item.window_text(), "enabled": item.is_enabled()}
                       for item in items]
        boxes = [item.rectangle() for item in items]
        area = (min(r.left for r in boxes), min(r.top for r in boxes),
                max(r.right for r in boxes), max(r.bottom for r in boxes))
        capture(tag, area, pid)
        return items

    def menu_key(pid):
        assert h.owner(h.u.GetForegroundWindow()) == pid
        h.u.keybd_event(0x5d, 0, 0, 0)
        h.u.keybd_event(0x5d, 0, 2, 0)

    def escape(pid):
        assert h.owner(h.u.GetForegroundWindow()) == pid
        h.keyboard.send_keys("{ESC}")

    try:
        with h.App(app_exe("Release"), fixture, "live-compare", theme) as app:
            assert h.u.GetDpiForWindow(app.hwnd) == 96
            h.wait(lambda: len(app.rows()) == 3 and app.el("UpButton").is_enabled(),
                   "owned flyExplorer fixture not ready")
            app.capture("listing")
            item = h.wait(lambda: next((r for r in app.rows()
                if "CompareOwned.txt" in r.window_text()), None), "owned app row absent")
            area = app.el("LeftFiles").rectangle()
            row = item.rectangle()
            point = (max(row.left, area.left) + 30,
                     (max(row.top, area.top) + min(row.bottom, area.bottom)) // 2)
            assert area.left < point[0] < area.right and area.top < point[1] < area.bottom
            item.click_input(coords=(point[0]-row.left, point[1]-row.top))
            prior = set(windows())
            menu_key(app.app.pid)
            items = observe_menu(app.win, app.app.pid, prior, "fly-selected-menu", ("경로 복사",))
            assert any("경로 복사" in x.window_text() for x in items)
            assert not any("--context-menu" in p.cmdline()
                           for p in app.process.children(recursive=True))
            escape(app.app.pid)
            result["menu_key_selected_cancel"] = True
            h.wait(lambda: any(r.has_keyboard_focus() for r in app.rows()) or
                   app.el("LeftFiles").has_keyboard_focus(), "file focus not restored")
            for row in app.rows():
                if row.is_selected():
                    row.iface_selection_item.RemoveFromSelection()
            app.el("LeftFiles").set_focus()
            h.wait(lambda: len(app.rows()) == 3 and not any(
                r.is_selected() for r in app.rows()), "background selection not clear")
            prior = set(windows())
            menu_key(app.app.pid)
            items = observe_menu(app.win, app.app.pid, prior, "fly-background-menu", ("새로 만들기",))
            assert any("새로 만들기" in x.window_text() for x in items)
            escape(app.app.pid)
            result["menu_key_background_cancel"] = True
            print("LIVE_COMPARE_MENU_KEY_SELECTED_BACKGROUND_PASS", flush=True)
            prior = set(windows())
            app.el("ViewButton").invoke()
            observe_menu(app.win, app.app.pid, prior, "fly-view-menu", ("자세히",))
            escape(app.app.pid)

            shell.Explore(str(fixture))
            target = fixture.as_uri().rstrip("/").casefold()
            def fresh():
                matches = []
                for win in shell.Windows():
                    try:
                        if (int(win.HWND) not in original and
                            str(win.LocationURL).rstrip("/").casefold() == target):
                            matches.append(win)
                    except Exception:
                        pass
                return matches[0] if len(matches) == 1 else None
            native = h.wait(fresh, "fresh owned Explorer window absent", 20)
            hwnd = int(native.HWND)
            pid = h.owner(hwnd)
            win = h.Desktop(backend="uia").window(handle=hwnd)
            assert Path(h.psutil.Process(pid).exe()).name.casefold() == "explorer.exe"
            assert h.u.MoveWindow(hwnd, 20, 20, 1160, 640, True)
            assert h.u.GetDpiForWindow(hwnd) == 96
            win.set_focus()
            r = win.rectangle()
            capture("explorer-header", (r.left+4, r.top+4, r.right-4, r.top+125), pid)
            owned_file = native.Document.Folder.Items().Item("CompareOwned.txt")
            assert owned_file is not None
            native.Document.SelectItem(owned_file, 1 | 4 | 8 | 16)
            h.wait(lambda: native.Document.SelectedItems().Count == 1,
                   "native owned selection absent")
            prior = set(windows())
            menu_key(pid)
            observe_menu(win, pid, prior, "explorer-selected-menu", ("속성", "Properties"))
            escape(pid)
            native.Document.SelectItem(owned_file, 0)
            h.wait(lambda: native.Document.SelectedItems().Count == 0,
                   "native selection not cleared")
            prior = set(windows())
            menu_key(pid)
            observe_menu(win, pid, prior, "explorer-background-menu", ("보기", "View", "새로 만들기", "New"))
            escape(pid)
            for label, keys in (("explorer-view-menu", ("보기", "View")),
                                ("explorer-new-menu", ("새로 만들기", "New"))):
                buttons = [b for b in win.descendants(control_type="Button")
                           if b.window_text().strip() in keys and b.is_visible()]
                if len(buttons) == 1:
                    prior = set(windows())
                    buttons[0].click_input()
                    observe_menu(win, pid, prior, label, ("아이콘", "icons", "폴더", "Folder"))
                    escape(pid)
                else:
                    result[label] = {"observed": False, "reason": "no unique toolbar peer"}
            assert str(native.LocationURL).rstrip("/").casefold() == target
            result["native_folder_unchanged"] = True
            assert {p.relative_to(fixture).as_posix(): p.read_bytes()
                    for p in fixture.rglob("*") if p.is_file()} == before
            result["original_bytes_preserved"] = True
        result["app"] = app.report
        passed = True
    finally:
        if native is not None:
            hwnd = int(native.HWND)
            if hwnd not in original and str(native.LocationURL).rstrip("/").casefold() == fixture.as_uri().rstrip("/").casefold():
                native.Quit()
                h.wait(lambda: not h.u.IsWindow(hwnd), "owned Explorer did not close", 10)
                result["owned_explorer_closed"] = True
        pythoncom.CoUninitialize()
        if passed:
            assert fixture.parent == base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        (base / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("LIVE_COMPARE_RESULT=" + json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

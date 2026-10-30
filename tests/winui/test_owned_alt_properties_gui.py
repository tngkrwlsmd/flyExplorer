"""Alt+Enter on disposable files; close only the exact fresh helper's sheet."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe


def main():
    base = ROOT / "logs" / "alt-properties-owned-20261031-dispatch-fix"
    base.mkdir(parents=True, exist_ok=True)
    h.BASE = base
    fixture = Path(tempfile.mkdtemp(prefix="fixture-", dir=base)).resolve()
    names = ("alt-properties-first-owned.txt", "alt-properties-second-owned.txt")
    for i, name in enumerate(names):
        (fixture / name).write_bytes(("owned property file " + str(i)).encode())
    before = {p.name: p.read_bytes() for p in fixture.iterdir()}
    result = {"source": subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()}
    helper = None
    dialog = None
    passed = False
    h.u.GetAncestor.argtypes = (w.HWND, w.UINT)
    h.u.GetAncestor.restype = w.HWND
    h.u.WindowFromPoint.argtypes = (w.POINT,)
    h.u.WindowFromPoint.restype = w.HWND
    try:
        with h.App(app_exe("Release"), fixture, "alt-properties") as app:
            def rows():
                return {name: next((r for r in app.rows() if name in r.window_text()), None)
                        for name in names}

            h.wait(lambda: all(rows().values()) and app.el("CreateFolderButton").is_enabled(),
                   "owned rows not ready")
            for count in (1, 2):
                app.win.set_focus()
                items = rows()
                items[names[0]].click_input()
                if count == 2:
                    items[names[1]].iface_selection_item.AddToSelection()
                # Keep the real clicked row as the keyboard route owner.
                # Moving focus to the ListView container bypasses the user input
                # path and can make Alt+Enter a harness-only no-op.
                h.wait(items[names[0]].has_keyboard_focus,
                       "clicked owned row not keyboard focused")
                h.wait(lambda: sum(bool(r.is_selected()) for r in rows().values()) == count,
                       "owned selection not ready")
                previous = {p.pid for p in app.process.children(recursive=True)}
                app.keys("%{ENTER}")
                h.wait(lambda: "속성 창을 여는 중입니다" in
                       app.el("StatusText").window_text(),
                       "Alt+Enter was not dispatched from the selected row")

                def spawned():
                    found = []
                    for child in app.process.children(recursive=True):
                        try:
                            if (child.pid not in previous and
                                Path(child.exe()).resolve() == app.exe.parent / "FlyShellIsolationHelper.exe" and
                                "--context-properties" in child.cmdline()):
                                found.append(child)
                        except h.psutil.Error:
                            pass
                    return found[0] if len(found) == 1 else None

                helper = h.wait(spawned, "direct properties helper absent", 10)
                result["helper_sha256"] = hashlib.sha256(Path(helper.exe()).read_bytes()).hexdigest()

                def sheet():
                    assert app.app.poll() is None, "owned app exited"
                    for win in h.Desktop(backend="uia").windows(process=helper.pid):
                        if (win.is_visible() and win.class_name() == "#32770" and
                            re.search(r"properties|속성", win.window_text(), re.I)):
                            return win
                    return None

                dialog = h.wait(sheet, "exact helper properties sheet absent", 12)
                content = "\n".join(e.window_text() for e in dialog.descendants()[:120])
                if count == 1:
                    assert names[0].casefold() in (dialog.window_text() + content).casefold()
                assert sum(bool(r.is_selected()) for r in rows().values()) == count
                dialog.set_focus()
                assert h.owner(h.u.GetForegroundWindow()) == helper.pid
                rect = dialog.rectangle()
                assert 0 <= rect.left < rect.right <= h.u.GetSystemMetrics(0)
                assert 0 <= rect.top < rect.bottom <= h.u.GetSystemMetrics(1)
                # Only capture this verified owned dialog; refuse overlapping foreign windows.
                for x, y in ((rect.left+8, rect.top+8), (rect.right-8, rect.bottom-8)):
                    target = h.u.WindowFromPoint(w.POINT(x, y))
                    assert h.u.GetAncestor(target, 2) == dialog.handle
                image = base / ("alt-properties-light-" + str(count) + "-selected.png")
                h.ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom),
                                 include_layered_windows=True).save(image)
                result[str(count) + "_selected"] = {"dialog_visible": True,
                    "selection_preserved": True, "image": image.name,
                    "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                    "dpi": h.u.GetDpiForWindow(dialog.handle)}
                assert h.owner(dialog.handle) == helper.pid
                assert h.u.PostMessageW(dialog.handle, 0x10, 0, 0)
                h.wait(lambda: not h.u.IsWindow(dialog.handle), "owned sheet did not close", 10)
                assert helper.wait(timeout=12) == 0, "properties helper failed"
                dialog = None
                helper = None
                app.win.set_focus()
                h.wait(lambda: "속성 창이 닫혔습니다" in app.el("StatusText").window_text(),
                       "properties completion status absent")
                assert sum(bool(r.is_selected()) for r in rows().values()) == count
            # Address editing keeps ownership of Alt+Enter.
            app.keys("^l")
            address = app.el("AddressBox")
            draft = str(fixture) + "-unsubmitted"
            address.set_edit_text(draft)
            address.set_focus()
            app.keys("%{ENTER}")
            assert address.get_value() == draft
            assert not any("--context-properties" in p.cmdline()
                           for p in app.process.children(recursive=True))
            app.keys("{ESC}")
            result["address_editor_preserved"] = True
            assert {p.name: p.read_bytes() for p in fixture.iterdir()} == before
            result["original_bytes_preserved"] = True
        assert app.report["normal_exit"] and app.report["profile_removed"]
        result["app"] = app.report
        passed = True
    finally:
        # Failure recovery closes only handles/processes established by this fixture.
        if dialog is not None and helper is not None:
            if h.u.IsWindow(dialog.handle) and h.owner(dialog.handle) == helper.pid:
                h.u.PostMessageW(dialog.handle, 0x10, 0, 0)
        if passed:
            assert fixture.parent == base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        (base / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("ALT_PROPERTIES_RESULT=" + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()

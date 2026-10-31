"""R02: exercise grouping only through the owned blank-background menu."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from pywinauto import Desktop, mouse
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe


def main():
    base = ROOT / "logs" / "r02-background-grouping-20261031"
    if base.exists():
        raise RuntimeError("existing R02 GUI evidence; inspect first")
    base.mkdir(parents=True)
    h.BASE = base
    fixture = Path(tempfile.mkdtemp(prefix="fixture-", dir=base)).resolve()
    files = {
        "r02-alpha.txt": b"alpha grouping owned\n",
        "r02-beta.md": b"beta grouping owned\n",
        "r02-gamma.log": b"gamma grouping owned\n",
    }
    for name, data in files.items():
        (fixture / name).write_bytes(data)
    before = {name: (fixture / name).read_bytes() for name in files}
    result = {
        "source": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "exe_sha256": h.hashlib.sha256(app_exe("Release").read_bytes()).hexdigest(),
    }
    passed = False
    try:
        with h.App(app_exe("Release"), fixture, "r02-grouping", "dark") as app:
            def file_row(name):
                return next((row for row in app.rows("Left")
                             if name in row.window_text()), None)

            def heading(title):
                return next((item for item in app.el("LeftFiles").descendants()
                             if item.element_info.control_type == "Button"
                             and title in item.window_text()), None)

            def visible_menu(text):
                found = {}
                roots = [app.win]
                roots += [window for window in
                          Desktop(backend="uia").windows(process=app.app.pid)
                          if window.handle != app.hwnd]
                for root in roots:
                    for item in root.descendants(control_type="MenuItem"):
                        if item.window_text() != text or not item.is_visible():
                            continue
                        box = item.rectangle()
                        if box.width() < 12 or box.height() < 12:
                            continue
                        found[(box.left, box.top, box.right, box.bottom)] = item
                return next(iter(found.values())) if len(found) == 1 else None

            def blank_point():
                area = app.el("LeftFiles").rectangle()
                bottoms = [row.rectangle().bottom for row in app.rows("Left")]
                assert bottoms
                point = (area.left + 45, max(area.top + 120, max(bottoms) + 35))
                assert (area.left < point[0] < area.right and
                        area.top < point[1] < area.bottom - 8)
                return point

            def open_group_menu():
                app.win.set_focus()
                h.wait(lambda: h.owner(h.u.GetForegroundWindow()) == app.app.pid,
                       "owned app did not regain foreground")
                mouse.click(button="right", coords=blank_point())
                group = h.wait(lambda: visible_menu("분류 방법"),
                               "background grouping submenu absent")
                box = group.rectangle()
                mouse.move(coords=(box.mid_point().x, box.mid_point().y))
                choice = h.wait(lambda: visible_menu("유형"),
                                "background Type grouping choice absent")
                assert group.element_info.process_id == app.app.pid
                assert choice.element_info.process_id == app.app.pid
                return choice

            h.wait(lambda: all(file_row(name) is not None for name in files)
                   and app.el("UpButton").is_enabled(),
                   "owned R02 fixture did not finish loading", 18)
            time.sleep(.8)
            assert heading(".txt") is None and heading(".md") is None
            choice = open_group_menu()
            assert choice.get_toggle_state() == 0
            app.capture("background-group-menu")
            box = choice.rectangle()
            mouse.click(coords=(box.mid_point().x, box.mid_point().y))
            h.wait(lambda: all(heading(title) is not None
                               for title in (".txt", ".md", ".log")),
                   "background Type choice did not group owned rows", 15)
            assert all(file_row(name) is not None for name in files)
            result["type_grouped"] = True

            choice = open_group_menu()
            assert choice.get_toggle_state() == 1
            app.capture("background-group-checked")
            box = choice.rectangle()
            mouse.click(coords=(box.mid_point().x, box.mid_point().y))
            h.wait(lambda: all(heading(title) is None
                               for title in (".txt", ".md", ".log"))
                   and all(file_row(name) is not None for name in files),
                   "checked background Type choice did not turn grouping off", 12)
            assert app.el("AddressBox").get_value().casefold() == str(fixture).casefold()
            assert {name: (fixture / name).read_bytes() for name in files} == before
            result["checked_reopen_and_toggle_off"] = True
            result["bytes_preserved"] = True
        result["app"] = app.report
        assert app.report["normal_exit"] and app.report["profile_removed"]
        passed = True
    finally:
        if passed:
            assert fixture.parent == base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        (base / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("R02_BACKGROUND_GROUPING_RESULT=" +
              json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

"""Owned Ctrl+number workspace selection and editor-preservation acceptance."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe


def main():
    base = ROOT / "logs" / "number-tabs-owned-20261030"
    base.mkdir(parents=True, exist_ok=True)
    h.BASE = base
    fixture = Path(tempfile.mkdtemp(prefix="fixture-", dir=base)).resolve()
    first, second = fixture / "First", fixture / "Second"
    first.mkdir()
    second.mkdir()
    (first / "first-owned.txt").write_bytes(b"owned first")
    (second / "second-owned.txt").write_bytes(b"owned second")
    before = {p.relative_to(fixture).as_posix(): p.read_bytes()
              for p in fixture.rglob("*") if p.is_file()}
    result = {"source": subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()}
    passed = False
    try:
        with h.App(app_exe("Release"), first, "number-tabs") as app:
            def tabs():
                return app.el("WindowTabStrip").descendants(control_type="TabItem")

            def active(index, path, name):
                items = tabs()
                return (len(items) == 2 and
                        bool(items[index].iface_selection_item.CurrentIsSelected) and
                        app.el("AddressBox").get_value().casefold() == str(path).casefold()
                        and any(name in row.window_text() for row in app.rows())
                        and any(name in row.window_text() for row in app.rows("Right"))
                        and app.el("UpButton").is_enabled())

            def select_row(side, name):
                row = h.wait(lambda: next((r for r in app.rows(side)
                    if name in r.window_text()), None), "owned row missing")
                assert h.owner(h.u.GetForegroundWindow()) == app.app.pid
                row.click_input()

            def visit(side):
                # The shared benchmark navigation helper only observes Left.
                app.el("PrimaryPaneTitle" if side == "Left" else
                       "SecondaryPaneTitle").invoke()
                app.keys("^l")
                address = app.el("AddressBox")
                address.set_edit_text(str(second))
                address.set_focus()
                app.keys("{ENTER}")
                h.wait(lambda: address.get_value().casefold() == str(second).casefold()
                       and any("second-owned.txt" in r.window_text()
                               for r in app.rows(side))
                       and app.el("UpButton").is_enabled(),
                       "owned route did not settle in " + side)

            h.wait(lambda: len(tabs()) == 1 and len(app.rows()) == 1
                   and len(app.rows("Right")) == 1
                   and app.el("CreateFolderButton").is_enabled(),
                   "initial owned workspace not ready")
            select_row("Left", "first-owned.txt")
            app.keys("^t")
            h.wait(lambda: len(tabs()) == 2, "second workspace absent")
            visit("Left")
            visit("Right")
            select_row("Left", "second-owned.txt")
            h.wait(lambda: active(1, second, "second-owned.txt"),
                   "second workspace fixture not ready")
            app.capture("second-before-number")
            app.keys("^1")
            h.wait(lambda: active(0, first, "first-owned.txt"),
                   "Ctrl+1 did not select first workspace with both panes")
            app.capture("first-after-number")
            app.keys("^2")
            h.wait(lambda: active(1, second, "second-owned.txt"),
                   "Ctrl+2 did not restore second workspace with both panes")
            app.capture("second-restored")
            app.keys("^2^9")
            assert active(1, second, "second-owned.txt")
            result["number_selection_workspace_paths_and_missing_number_noop"] = True

            app.keys("^l")
            address = app.el("AddressBox")
            h.wait(address.has_keyboard_focus, "address editor not focused")
            address.set_edit_text("owned-unsubmitted-draft")
            app.keys("^1")
            assert address.has_keyboard_focus()
            assert address.get_value() == "owned-unsubmitted-draft"
            assert bool(tabs()[1].iface_selection_item.CurrentIsSelected)
            app.keys("{ESC}")
            h.wait(lambda: active(1, second, "second-owned.txt"),
                   "editor cancellation did not preserve current workspace")
            result["address_editor_input_and_workspace_preserved"] = True
        result["normal_exit"] = app.report["normal_exit"]
        result["original_settings_unchanged"] = app.report["original_settings_unchanged"]
        after = {p.relative_to(fixture).as_posix(): p.read_bytes()
                 for p in fixture.rglob("*") if p.is_file()}
        assert after == before
        result["owned_names_and_bytes_unchanged"] = True
        passed = True
    finally:
        if passed:
            assert fixture.parent == base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        print("NUMBER_TABS_GUI_RESULT=" + json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

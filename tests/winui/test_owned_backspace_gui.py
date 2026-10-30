"""Owned sibling-folder history and text-editor Backspace acceptance."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe


def main():
    base = ROOT / "logs" / "backspace-owned-20261030"
    base.mkdir(parents=True, exist_ok=True)
    h.BASE = base
    fixture = Path(tempfile.mkdtemp(prefix="fixture-", dir=base)).resolve()
    first, second = fixture / "First", fixture / "Second"
    first.mkdir()
    second.mkdir()
    (first / "first-owned.txt").write_bytes(b"owned first")
    (second / "second-owned.txt").write_bytes(b"owned second")

    def contents():
        return {p.relative_to(fixture).as_posix():
                hashlib.sha256(p.read_bytes()).hexdigest()
                for p in fixture.rglob("*") if p.is_file()}

    before = contents()
    result = {"source": subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()}
    passed = False
    try:
        with h.App(app_exe("Release"), first, "backspace") as app:
            def ready(path, name, side="Left"):
                return (app.el("AddressBox").get_value().casefold() ==
                        str(path).casefold() and
                        any(name in row.window_text() for row in app.rows(side)) and
                        app.el("UpButton").is_enabled())

            def select_row(side, name):
                row = h.wait(lambda: next((r for r in app.rows(side)
                    if name in r.window_text()), None), "owned row absent")
                assert h.owner(h.u.GetForegroundWindow()) == app.app.pid
                row.click_input()

            def navigate(side, path, name):
                app.keys("^l")
                address = app.el("AddressBox")
                address.set_edit_text(str(path))
                address.set_focus()
                app.keys("{ENTER}")
                h.wait(lambda: ready(path, name, side),
                       "owned navigation did not settle in " + side)

            h.wait(lambda: len(app.rows()) == 1 and len(app.rows("Right")) == 1
                   and app.el("CreateFolderButton").is_enabled(),
                   "initial owned panes not ready")
            # Sibling folders distinguish Back history from parent/Up.
            select_row("Left", "first-owned.txt")
            navigate("Left", second, "second-owned.txt")
            select_row("Left", "second-owned.txt")
            app.capture("left-before-back")
            app.keys("{BACKSPACE}")
            h.wait(lambda: ready(first, "first-owned.txt"),
                   "left Backspace did not return to previous sibling")
            assert "first-owned.txt" in app.first("Right")
            app.capture("left-after-back")
            result["left_sibling_history_and_opposite_preserved"] = True

            select_row("Right", "first-owned.txt")
            navigate("Right", second, "second-owned.txt")
            select_row("Right", "second-owned.txt")
            app.keys("{BACKSPACE}")
            h.wait(lambda: ready(first, "first-owned.txt", "Right"),
                   "right Backspace did not return to previous sibling")
            assert "first-owned.txt" in app.first("Left")
            result["right_sibling_history_and_opposite_preserved"] = True

            # These editors are outside the file-list route; Backspace edits
            # text without submitting navigation, search or a file command.
            app.keys("^l")
            address = app.el("AddressBox")
            h.wait(address.has_keyboard_focus, "address editor not focused")
            address.set_edit_text(str(first) + "x")
            app.keys("{END}{BACKSPACE}")
            h.wait(lambda: address.get_value() == str(first),
                   "address Backspace did not delete text")
            app.keys("{ESC}")
            app.keys("^f")
            search = app.el("QuickSearchBox")
            h.wait(search.has_keyboard_focus, "search editor not focused")
            search.set_edit_text("ab")
            app.keys("{END}{BACKSPACE}")
            h.wait(lambda: search.get_value() == "a",
                   "search Backspace did not delete text")
            search.set_edit_text("")
            select_row("Right", "first-owned.txt")
            app.keys("{F2}")
            editor = app.el("FileNameBox")
            h.wait(editor.has_keyboard_focus, "rename editor not focused")
            editor.set_edit_text("rename-draft.txt")
            app.keys("{END}{BACKSPACE}")
            h.wait(lambda: editor.get_value() == "rename-draft.tx",
                   "rename Backspace did not delete text")
            app.keys("{ESC}")
            h.wait(lambda: editor.get_value() == "", "rename cancel failed")
            assert ready(first, "first-owned.txt", "Right")
            assert "first-owned.txt" in app.first("Left")
            result["address_search_and_rename_text_editing_preserved"] = True
        result["normal_exit"] = app.report["normal_exit"]
        result["original_settings_unchanged"] = app.report["original_settings_unchanged"]
        assert contents() == before
        result["owned_names_and_bytes_unchanged"] = True
        passed = True
    finally:
        if passed:
            assert fixture.parent == base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        print("BACKSPACE_GUI_RESULT=" + json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

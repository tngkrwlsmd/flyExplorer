"""R18 owned Windows GUI: actual Alt+Shift+P Details toggle, Alt+P baseline.

Works only with a disposable file, profile and owned app window.
No system-wide clipboard, Explorer windows or personal folders are touched.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

from pywinauto.keyboard import send_keys
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE = ROOT / "logs" / "r18-details-keyboard-owned-20261101"


def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise RuntimeError("Retained R18 GUI evidence exists")
    BASE.mkdir(parents=True, exist_ok=True)
    h.BASE = BASE
    folder = Path(tempfile.mkdtemp(prefix="r18-owned-", dir=BASE)).resolve()
    source = folder / "r18-owned-file.txt"
    content = b"r18-keyboard-never-implicitly-reads-file"
    source.write_bytes(content)
    result = {
        "exe_sha256": hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()
    }
    success = False
    try:
        with h.App(app_exe("Release"), folder, "r18-details-shortcut", "dark") as app:
            def name():
                return app.el("FileInfoToggleButton").element_info.name

            def key(keys):
                app.win.set_focus()
                assert h.owner(h.u.GetForegroundWindow()) == app.app.pid, (
                    "Refusing keyboard input to foreign foreground window"
                )
                send_keys(keys, pause=0.12)

            def no_automatic_read():
                assert app.el("TextPreviewBody").window_text().strip() == "", (
                    "Preview body was filled without explicit opt-in"
                )
                assert "꺼" in app.el("TextPreviewStatus").window_text(), (
                    "Text preview opt-in changed without consent"
                )

            assert "열기" in name(), "Details must start collapsed"
            key("%+p")  # Alt+Shift+P, actual keyboard injection.
            h.wait(lambda: "닫기" in name(),
                   "R18 first Alt+Shift+P did not open Details", seconds=12)
            no_automatic_read()
            result["details_opened_by_keyboard"] = True
            key("%+p")
            h.wait(lambda: "열기" in name(),
                   "R18 second Alt+Shift+P did not close Details", seconds=12)
            result["details_closed_by_keyboard"] = True

            # Alt+P keeps the old explicit Preview-reveal focus behavior,
            # but must not enable reading the selected file by itself.
            key("%p")
            h.wait(lambda: "닫기" in name(),
                   "Existing Alt+P did not open the pane", seconds=12)
            no_automatic_read()
            result["alt_p_open_kept"] = True
            key("%p")
            h.wait(lambda: "열기" in name(),
                   "Existing Alt+P did not close the pane", seconds=12)
            result["alt_p_close_kept"] = True
            result["original_unchanged"] = source.read_bytes() == content
        result["app"] = app.report
        assert result["original_unchanged"]
        assert app.report["normal_exit"]
        assert app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success = True
    finally:
        result["owned_file_preserved_on_exit"] = source.read_bytes() == content
        if success:
            assert folder.parent == BASE.resolve() and not folder.is_symlink()
            shutil.rmtree(folder)
            result["fixture_removed"] = True
        (BASE / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("R18_DETAILS_GUI_RESULT=" +
              json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

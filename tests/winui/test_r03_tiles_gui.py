"""R03 Tiles bounded GUI: focused pane Ctrl+Shift+7 and legacy Details."""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

def main():
    base = ROOT / "logs" / "r03-tiles-20261031"
    if base.exists() and any(base.iterdir()):
        raise RuntimeError("existing R03 Tiles evidence; preserve and inspect")
    base.mkdir(parents=True, exist_ok=True)
    h.BASE = base
    fixture = Path(tempfile.mkdtemp(prefix="fixture-", dir=base)).resolve()
    samples = {
        "tile-alpha.txt": b"r03 tiles alpha\n",
        "tile-beta.md": b"r03 tiles beta\n",
        "tile-gamma.log": b"r03 tiles gamma\n",
    }
    for name, data in samples.items():
        (fixture / name).write_bytes(data)
    originals = {name: (fixture / name).read_bytes() for name in samples}
    result = {"exe_sha256": hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    success = False
    try:
        with h.App(app_exe("Release"), fixture, "r03-tiles", "dark") as app:
            def row(side, name):
                return next((r for r in app.rows(side) if name in r.window_text()), None)
            def ready():
                return all(row(side, name) is not None
                           for side in ("Left", "Right") for name in samples)
            def rectangles(side):
                return [row(side, name).rectangle() for name in samples]
            h.wait(ready, "owned folder rows missing", seconds=20)
            left = app.el("LeftFiles")
            right = app.el("RightFiles")
            left.set_focus()
            app.keys("^+7")
            def tiles_ready():
                return ready() and all(248 <= box.width() <= 264 and
                                       74 <= box.height() <= 86
                                       for box in rectangles("Left"))
            h.wait(tiles_ready, "Ctrl+Shift+7 did not produce Tile rows", seconds=20)
            assert all(box.height() < 70 for box in rectangles("Right"))
            assert left.is_enabled() and right.is_enabled()
            app.capture("tiles")
            result["left_tiles_right_details"] = True
            left.set_focus()
            app.keys("^+6")
            h.wait(lambda: ready() and all(box.height() < 70
                   for box in rectangles("Left")),
                   "legacy Details unavailable after Tiles", seconds=15)
            assert all(box.height() < 70 for box in rectangles("Right"))
            result["legacy_details_reachable"] = True
            left.set_focus()
            app.keys("^+7")
            h.wait(tiles_ready, "Tiles not repeatable after Details", seconds=15)
            app.capture("tiles-again")
            assert {name: (fixture / name).read_bytes() for name in samples} == originals
            result["files_preserved"] = True
        result["app"] = app.report
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success = True
    finally:
        if success:
            assert fixture.parent == base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        (base / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("R03_TILES_GUI_RESULT=" + json.dumps(result, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()

"""Focused R03 Content view GUI; only isolated local fixture and app profile."""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

def main():
    base=ROOT/"logs"/"r03-content-20261031"
    if base.exists() and any(base.iterdir()):
        raise RuntimeError("R03 Content evidence exists; inspect instead of replacing")
    base.mkdir(parents=True,exist_ok=True)
    h.BASE=base
    fixture=Path(tempfile.mkdtemp(prefix="fixture-",dir=base)).resolve()
    samples={
        "content-alpha.txt":b"r03 content alpha\n",
        "content-beta.md":b"r03 content beta\n",
        "content-gamma.log":b"r03 content gamma\n",
    }
    for name,data in samples.items():
        (fixture/name).write_bytes(data)
    originals={name:(fixture/name).read_bytes() for name in samples}
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    success=False
    try:
        with h.App(app_exe("Release"),fixture,"r03-content","dark") as app:
            def row(side,name):
                return next((item for item in app.rows(side)
                             if name in item.window_text()),None)
            def all_rows():
                return all(row(side,name) is not None
                           for side in ("Left","Right") for name in samples)
            def rectangles(side):
                return [row(side,name).rectangle() for name in samples]
            h.wait(all_rows,"owned content fixture rows not ready",seconds=20)
            left=app.el("LeftFiles")
            right=app.el("RightFiles")
            left.set_focus()
            app.keys("^+8")
            def content_ready():
                return all_rows() and all(300<=box.width()<=600 and
                    76<=box.height()<=115 for box in rectangles("Left"))
            h.wait(content_ready,"Ctrl+Shift+8 did not enter full-width Content view",seconds=20)
            assert all(box.height()<70 for box in rectangles("Right"))
            assert left.is_enabled() and right.is_enabled()
            app.capture("content")
            result["left_content_right_details"]=True
            left.set_focus()
            app.keys("^+6")
            h.wait(lambda:all_rows() and all(box.height()<70
                   for box in rectangles("Left")),
                   "Details mode unavailable after Content",seconds=15)
            assert all(box.height()<70 for box in rectangles("Right"))
            result["legacy_details_reachable"]=True
            left.set_focus()
            app.keys("^+8")
            h.wait(content_ready,"Content view not repeatable",seconds=15)
            app.capture("content-again")
            assert {name:(fixture/name).read_bytes() for name in samples}==originals
            result["files_preserved"]=True
        result["app"]=app.report
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success=True
    finally:
        if success:
            assert fixture.parent==base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"]=True
        (base/"result.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("R03_CONTENT_GUI_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":main()

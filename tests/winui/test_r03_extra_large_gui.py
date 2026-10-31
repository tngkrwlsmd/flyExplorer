"""R03 owned GUI: Ctrl+Shift+1 selects extra-large only on active pane."""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

def main():
    base=ROOT/"logs"/"r03-extra-large-icons-20261031"
    if base.exists() and any(base.iterdir()):
        raise RuntimeError("existing R03 evidence; preserve and inspect")
    base.mkdir(parents=True,exist_ok=True)
    h.BASE=base
    fixture=Path(tempfile.mkdtemp(prefix="fixture-",dir=base)).resolve()
    samples={
        "r03-alpha.txt":b"r03 owned alpha\n",
        "r03-beta.md":b"r03 owned beta\n",
        "r03-gamma.log":b"r03 owned gamma\n",
    }
    for name,data in samples.items():
        (fixture/name).write_bytes(data)
    before={name:(fixture/name).read_bytes() for name in samples}
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    passed=False
    try:
        with h.App(app_exe("Release"),fixture,"r03-extra-large","dark") as app:
            def row(side,name):
                return next((r for r in app.rows(side)
                             if name in r.window_text()),None)
            def boxes(side):
                return [row(side,name).rectangle() for name in samples]
            def all_rows():
                return all(row(side,name) is not None
                           for side in ("Left","Right") for name in samples)
            h.wait(all_rows,"both owned pane lists absent",seconds=20)
            left=app.el("LeftFiles")
            right=app.el("RightFiles")
            left.set_focus()
            app.keys("^+1")
            def extra_ready():
                return all_rows() and all(160<=b.width()<=176 and
                                          180<=b.height()<=196
                                          for b in boxes("Left"))
            h.wait(extra_ready,"extra-large mode was not applied to left pane",seconds=20)
            assert all(b.height()<70 for b in boxes("Right"))
            assert left.is_enabled() and right.is_enabled()
            app.capture("extra-large")
            result["left_extra_large_right_details"]=True
            left.set_focus()
            app.keys("^+2")
            def large_ready():
                return all_rows() and all(108<=b.width()<=120 and
                                          122<=b.height()<=132
                                          for b in boxes("Left"))
            h.wait(large_ready,"legacy large icons unavailable after R03",seconds=15)
            assert all(b.height()<70 for b in boxes("Right"))
            app.capture("legacy-large")
            result["legacy_large_reachable"]=True
            left.set_focus()
            app.keys("^+1")
            h.wait(extra_ready,"extra-large mode not repeatable",seconds=15)
            assert {name:(fixture/name).read_bytes() for name in samples}==before
            result["original_files_preserved"]=True
        result["app"]=app.report
        assert app.report["normal_exit"] and app.report["profile_removed"]
        passed=True
    finally:
        if passed:
            assert fixture.parent==base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"]=True
        (base/"result.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("R03_GUI_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)
if __name__=="__main__":main()

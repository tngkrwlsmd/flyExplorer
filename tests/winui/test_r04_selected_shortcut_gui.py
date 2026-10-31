"""R04 exact selected-file app menu -> .lnk creation on an owned fixture.

Only the freshly spawned flyExplorer process, its own UIA/menu items, and an
isolated local test folder/profile are allowed. No clipboard or OS settings.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

from pywinauto import Desktop
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE=ROOT/"logs"/"r04-selected-shortcut-gui-20261031"


def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise RuntimeError("Retained R04 GUI evidence exists; preserve it")
    BASE.mkdir(parents=True, exist_ok=True)
    h.BASE=BASE
    fixture=Path(tempfile.mkdtemp(prefix="owned-fixture-", dir=BASE)).resolve()
    original=fixture/"r04-owned-source.txt"
    original.write_bytes(b"r04 selected shortcut original\n")
    content=original.read_bytes()
    created=fixture/"r04-created-link.lnk"
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    completed=False
    try:
        with h.App(app_exe("Release"),fixture,"r04-selected-shortcut","dark") as app:
            def source_row():
                found=[r for r in app.rows("Left") if original.name in r.window_text()]
                return found[0] if len(found)==1 else None
            row=h.wait(source_row,"owned source row unavailable",seconds=20)
            app.win.set_focus()
            row.select()
            h.wait(lambda:source_row() is not None and source_row().is_selected(),
                   "source not selected",seconds=8)
            app.el("LeftFiles").set_focus()
            assert h.owner(h.u.GetForegroundWindow())==app.app.pid
            app.keys("+{F10}")

            def shortcut_action():
                matches={}
                for top in Desktop(backend="uia").windows(process=app.app.pid):
                    try:
                        for item in top.descendants(control_type="MenuItem"):
                            if (item.element_info.process_id==app.app.pid and
                                    item.window_text().strip()=="바로 가기 만들기"):
                                box=item.rectangle()
                                matches[(box.left,box.top,box.right,box.bottom)]=item
                    except (RuntimeError,LookupError):
                        continue
                return next(iter(matches.values())) if len(matches)==1 else None

            item=h.wait(shortcut_action,"owned shortcut menu absent",seconds=12)
            assert item.is_enabled() and item.element_info.process_id==app.app.pid
            assert h.owner(h.u.GetForegroundWindow())==app.app.pid
            item.click_input()
            result["selected_menu_clicked"]=True

            edit=app.el("FileNameBox")
            h.wait(lambda:edit.is_visible() and
                   edit.get_value().endswith(" - 바로 가기.lnk"),
                   "shortcut name edit did not open",seconds=12)
            result["name_editor_shown"]=True
            assert not created.exists()
            edit.set_edit_text(created.name)
            edit.type_keys("{ENTER}")
            h.wait(created.is_file,"selected shortcut not created",seconds=25)
            payload=created.read_bytes()
            assert len(payload)>40 and payload[:4]==b"\x4c\x00\x00\x00",(
                "created output is not a Shell link header")
            assert original.read_bytes()==content
            h.wait(lambda:any(created.stem in r.window_text() for r in app.rows("Left")),
                   "created shortcut not displayed after refresh",seconds=20)
            result["link_created_and_displayed"]=True
            result["original_bytes_unchanged"]=True
            assert app.app.poll() is None
        result["app"]=app.report
        assert result["app"]["normal_exit"] and result["app"]["original_settings_unchanged"]
        assert result["app"]["profile_removed"]
        completed=True
    finally:
        if completed:
            assert fixture.parent==BASE.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"]=True
        (BASE/"result.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("R04_SELECTED_SHORTCUT_GUI_RESULT="+
              json.dumps(result,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()

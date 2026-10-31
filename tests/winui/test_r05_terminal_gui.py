"""R05 owned Windows Terminal new-window GUI: no command input or clipboard."""
from pathlib import Path
from ctypes import wintypes as w
import ctypes as c
import hashlib
import json
import shutil
import tempfile

import psutil
from pywinauto import Desktop,mouse
import benchmark_filtered_folder_gui as h
from paths import ROOT,app_exe

u=c.windll.user32
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.EnumWindows.argtypes=(c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM),w.LPARAM)
u.IsWindowVisible.argtypes=(w.HWND,)
u.IsWindow.argtypes=(w.HWND,)
u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)

def terminal_windows():
    # Read HWND/PID only for WindowsTerminal.exe, not window text or user data.
    found=set()
    names={}
    def visit(hwnd,ignore):
        if not u.IsWindowVisible(hwnd):
            return True
        pid=w.DWORD()
        u.GetWindowThreadProcessId(hwnd,c.byref(pid))
        if not pid.value:
            return True
        if pid.value not in names:
            try:
                names[pid.value]=psutil.Process(pid.value).name().casefold()
            except psutil.Error:
                names[pid.value]=""
        if names[pid.value]=="windowsterminal.exe":
            found.add((int(hwnd),pid.value))
        return True
    fn=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)(visit)
    assert u.EnumWindows(fn,0),"EnumWindows failed"
    return found

def main():
    base=ROOT/"logs"/"r05-terminal-owned-20261031"
    if base.exists() and any(base.iterdir()):
        raise RuntimeError("Retained R05 owned evidence exists; preserve it")
    base.mkdir(parents=True,exist_ok=True)
    h.BASE=base
    fixture=Path(tempfile.mkdtemp(prefix="fixture-",dir=base)).resolve()
    marker=fixture/"r05-owned-sentinel.txt"
    marker.write_bytes(b"r05 only original sentinel\n")
    original=marker.read_bytes()
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    baseline=terminal_windows()
    new_hwnd=None
    success=False
    try:
        with h.App(app_exe("Release"),fixture,"r05-terminal","dark") as app:
            h.wait(lambda:any(marker.name in x.window_text() for x in app.rows("Left")),
                   "owned folder entry absent",seconds=20)
            view=app.el("LeftFiles")
            rect=view.rectangle()
            x=rect.left+min(90,(rect.right-rect.left)//3)
            y=rect.bottom-45
            assert rect.left<x<rect.right and rect.top<y<rect.bottom
            for item in app.rows("Left"):
                ir=item.rectangle()
                assert not ir.left<=x<ir.right or not ir.top<=y<ir.bottom,(
                    "R05 right click would touch a selected file row")
            app.win.set_focus()
            assert h.owner(u.GetForegroundWindow())==app.app.pid
            mouse.click(button="right",coords=(x,y))
            def owned_action():
                matches={}
                for win in Desktop(backend="uia").windows(process=app.app.pid):
                    try:
                        for item in win.descendants(control_type="MenuItem"):
                            if (item.element_info.process_id==app.app.pid and
                                    item.window_text().strip()=="터미널에서 열기"):
                                r=item.rectangle()
                                matches[(r.left,r.top,r.right,r.bottom)]=item
                    except (RuntimeError,LookupError):
                        continue
                return next(iter(matches.values())) if len(matches)==1 else None
            item=h.wait(owned_action,"R05 owned background menu entry absent",seconds=12)
            assert item.element_info.process_id==app.app.pid
            assert h.owner(u.GetForegroundWindow())==app.app.pid
            app.capture("menu")
            item.click_input()
            def own_new_terminal():
                matches=terminal_windows()-baseline
                return next(iter(matches)) if len(matches)==1 else None
            new_hwnd,pid=h.wait(own_new_terminal,
                               "new Windows Terminal window not observed",seconds=20)
            assert psutil.Process(pid).name().casefold()=="windowsterminal.exe"
            assert u.IsWindow(new_hwnd)
            result["new_terminal_window"]=True
            result["terminal_pid"]=pid
            assert marker.read_bytes()==original
            assert app.app.poll() is None
            assert str(fixture).casefold() in app.el("AddressBox").get_value().casefold()
            result["original_file_preserved"]=True
            assert u.PostMessageW(new_hwnd,0x10,0,0),"could not close owned Terminal HWND"
            h.wait(lambda:not u.IsWindow(new_hwnd),
                   "owned Terminal window did not close",seconds=15)
            result["terminal_window_closed"]=True
            new_hwnd=None
            app.win.set_focus()
            app.capture("returned")
        result["app"]=app.report
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success=True
    finally:
        if new_hwnd and u.IsWindow(new_hwnd):
            # Only the unique new window observed after the owned click.
            u.PostMessageW(new_hwnd,0x10,0,0)
        if success:
            assert fixture.parent==base.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"]=True
        (base/"result.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("R05_TERMINAL_GUI_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()

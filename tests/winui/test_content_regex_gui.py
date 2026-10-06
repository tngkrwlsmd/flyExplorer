"""Focused UIA-only acceptance for bounded content regex search.

Uses only owned files/profile state and UI Automation patterns; it never sends
physical mouse/keyboard input or steals foreground focus from a user window.
"""
from pathlib import Path
from paths import ROOT, app_exe
from profile_guard import (
    assert_legacy_profile_unchanged,
    snapshot_legacy_profile,
)
from uia_polling import wait_until
import ctypes as c
import ctypes.wintypes as W
import os
import shutil
import subprocess
import tempfile
import time

from pywinauto import Desktop

CONFIG=os.environ.get("FLY_MIGRATION_CONFIGURATION","Release")
assert CONFIG in ("Debug","Release")
EXE=app_exe(CONFIG)
assert EXE.is_file(),EXE
LOGS=ROOT/"logs"/"content-regex-gui"
LOGS.mkdir(parents=True,exist_ok=True)

u=c.windll.user32
CALL=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CALL,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,c.POINTER(W.DWORD)]
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,c.c_int]
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]


def owned_windows(pid):
    found=[]
    @CALL
    def cb(hwnd,_):
        process=W.DWORD()
        u.GetWindowThreadProcessId(hwnd,c.byref(process))
        if process.value==pid and u.IsWindowVisible(hwnd):
            title=c.create_unicode_buffer(700)
            u.GetWindowTextW(hwnd,title,len(title))
            found.append((int(hwnd),title.value))
        return 1
    u.EnumWindows(cb,0)
    return found


def wait_for(fn,label,seconds=15):
    return wait_until(fn,label,seconds=seconds,interval=.12)


def launch(left,env):
    proc=subprocess.Popen(
        [str(EXE),str(left)],
        cwd=EXE.parent,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    hwnd=None
    try:
        def discover():
            nonlocal hwnd
            if proc.poll() is not None:
                return True
            windows=[
                (handle,title) for handle,title in owned_windows(proc.pid)
                if "flyExplorer" in title
            ]
            if len(windows)==1:
                hwnd=windows[0][0]
                return True
            return False
        wait_for(discover,"content-regex WinUI window not discovered",20)
        assert proc.poll() is None,("WinUI startup failed",proc.returncode)
        assert hwnd is not None,owned_windows(proc.pid)
        return proc,hwnd,Desktop(backend="uia").window(handle=hwnd)
    except BaseException:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        raise


def close(proc,hwnd):
    if proc.poll() is None:
        u.PostMessageW(W.HWND(hwnd),0x10,0,0)
        try:
            proc.wait(timeout=12)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    assert proc.returncode==0,proc.returncode


def element(win,name):
    return win.child_window(auto_id=name)


def invoke(win,name):
    control=element(win,name).wrapper_object()
    control.invoke()


def set_text(win,name,value):
    control=element(win,name).wrapper_object()
    control.set_edit_text(value)


def set_toggle(win,name,wanted):
    control=element(win,name).wrapper_object()
    current=control.get_toggle_state()
    if current!=wanted:
        control.toggle()
    wait_for(
        lambda: element(win,name).wrapper_object().get_toggle_state()==wanted,
        f"{name} toggle state did not become {wanted}",
        5,
    )


def count_text(win):
    return element(win,"SearchCountText").window_text()


def result_labels(win):
    return [
        item.window_text()
        for item in element(win,"SearchMatches").descendants()
        if item.element_info.control_type=="ListItem"
    ]


def open_search(win):
    invoke(win,"SearchPanelButton")
    wait_for(
        lambda: element(win,"SearchScopeBox").exists(timeout=.15)
        and element(win,"SearchScopeBox").is_visible(),
        "advanced search panel did not open through UIA InvokePattern",
        8,
    )


def main():
    user,before=snapshot_legacy_profile()
    owned=Path(tempfile.mkdtemp(prefix="owned-content-regex-",dir=LOGS))
    left=owned/"Left"
    appdata=owned/"appdata"
    localdata=owned/"localdata"
    temp=owned/"tmp"
    for folder in (left,appdata,localdata,temp):
        folder.mkdir()
    (left/"content-regex.txt").write_text(
        "Alpha NeedLe omega",encoding="utf-8")
    (left/"content-other.txt").write_text(
        "Alpha unrelated omega",encoding="utf-8")
    env={
        **os.environ,
        "APPDATA":str(appdata),
        "LOCALAPPDATA":str(localdata),
        "TEMP":str(temp),
        "TMP":str(temp),
    }
    preset_file=localdata/"flyExplorer"/"search-presets-v1.txt"
    proc=None
    hwnd=None
    try:
        proc,hwnd,win=launch(left,env)
        open_search(win)
        for name in (
            "SearchScopeBox",
            "SearchContentBox",
            "SearchContentRegexBox",
            "SearchCaseBox",
            "SearchRunButton",
            "SearchCountText",
            "SearchMatches",
            "SearchPresetNameBox",
            "SearchPresetSaveButton",
            "SearchPresetApplyButton",
            "SearchPresetDeleteButton",
        ):
            assert element(win,name).exists(timeout=3),name

        set_text(win,"SearchScopeBox",str(left))
        set_text(win,"SearchTermBox","")
        set_text(win,"SearchContentBox",r"^Alpha\s+Need(Le|Missing)\s+omega$")
        set_toggle(win,"SearchContentRegexBox",1)
        invoke(win,"SearchRunButton")
        wait_for(
            lambda:"검색 결과 1개" in count_text(win),
            "bounded content regex did not produce one result",
            18,
        )
        labels=result_labels(win)
        assert any("content-regex.txt" in label for label in labels),labels
        assert not any("content-other.txt" in label for label in labels),labels
        print("REAL_CONTENT_REGEX_UIA_GROUP_ALTERNATION_PASS",True,flush=True)

        set_text(win,"SearchContentBox","(?=Alpha)Alpha")
        invoke(win,"SearchRunButton")
        wait_for(
            lambda:"파일 내용 정규식이 올바르지 않습니다" in count_text(win),
            "unsupported lookaround was not rejected before worker",
            8,
        )
        assert element(win,"SearchRunButton").is_enabled()
        print("REAL_CONTENT_REGEX_UIA_INVALID_PRESTART_REJECT_PASS",True,flush=True)

        set_text(win,"SearchContentBox",r"Need(Le|Missing)")
        set_text(win,"SearchPresetNameBox","내용 정규식")
        invoke(win,"SearchPresetSaveButton")
        wait_for(
            lambda:preset_file.is_file()
            and "schema=4" in preset_file.read_text(encoding="utf-8")
            and "\t1\t0\t0\t" in preset_file.read_text(encoding="utf-8"),
            "content-regex preset schema 4 was not persisted",
            10,
        )
        print("REAL_CONTENT_REGEX_UIA_PRESET_SCHEMA4_SAVE_PASS",True,flush=True)
        close(proc,hwnd)
        proc=None
        hwnd=None

        proc,hwnd,win=launch(left,env)
        open_search(win)
        wait_for(
            lambda:element(win,"SearchPresetNameBox").get_value()=="내용 정규식",
            "saved content-regex preset name did not reload",
            8,
        )
        invoke(win,"SearchPresetApplyButton")
        wait_for(
            lambda:
                element(win,"SearchContentBox").get_value()==r"Need(Le|Missing)"
                and element(win,"SearchContentRegexBox").wrapper_object().get_toggle_state()==1,
            "content-regex preset did not restore query and toggle",
            8,
        )
        invoke(win,"SearchRunButton")
        wait_for(
            lambda:"검색 결과 1개" in count_text(win),
            "reloaded content-regex preset did not execute",
            18,
        )
        print("REAL_CONTENT_REGEX_UIA_PRESET_RESTART_PASS",True,flush=True)

        invoke(win,"SearchPresetDeleteButton")
        wait_for(
            lambda:preset_file.is_file()
            and preset_file.read_text(encoding="utf-8").strip()=="schema=4",
            "content-regex preset delete did not persist",
            8,
        )
        print("REAL_CONTENT_REGEX_UIA_PRESET_DELETE_PASS",True,flush=True)
        close(proc,hwnd)
        proc=None
        hwnd=None

        assert_legacy_profile_unchanged(user,before)
        print("CONTENT_REGEX_UIA_GUI_PASS",True,flush=True)
        return 0
    finally:
        if proc is not None and proc.poll() is None:
            if hwnd is not None:
                u.PostMessageW(W.HWND(hwnd),0x10,0,0)
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        assert_legacy_profile_unchanged(user,before)
        assert owned.name.startswith("owned-content-regex-")
        assert owned.parent==LOGS
        shutil.rmtree(owned,ignore_errors=False)
        print("CONTENT_REGEX_UIA_FIXTURE_RECLAIMED",True,flush=True)


if __name__=="__main__":
    raise SystemExit(main())

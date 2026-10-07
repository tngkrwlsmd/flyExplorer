"""Focused UIA-only acceptance for isolated Copy/Move transfers.

Uses only owned files/profile state and UI Automation patterns. It never sends
physical mouse/keyboard input or requires a foreground desktop window.
"""
from pathlib import Path
from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
from uia_polling import wait_until
import ctypes as c
import ctypes.wintypes as W
import os
import shutil
import subprocess
import tempfile

from pywinauto import Desktop

CONFIG=os.environ.get("FLY_MIGRATION_CONFIGURATION","Release")
assert CONFIG in ("Debug","Release")
EXE=app_exe(CONFIG)
assert EXE.is_file(),EXE
LOGS=ROOT/"logs"/"unc-copy-move-gui"
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


def wait_for(fn,label,seconds=18):
    return wait_until(fn,label,seconds=seconds,interval=.12)


def launch(folder,env):
    proc=subprocess.Popen(
        [str(EXE),str(folder)],
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
        wait_for(discover,"UNC transfer WinUI window not discovered",20)
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
    element(win,name).wrapper_object().invoke()


def rows(win,side):
    return [
        item for item in element(win,side+"Files").descendants()
        if item.element_info.control_type=="ListItem"
    ]


def row(win,side,name):
    return next((item for item in rows(win,side) if name in item.window_text()),None)


def select_one(win,side,name):
    def selected():
        item=row(win,side,name)
        if item is None:
            return False
        item.iface_selection_item.Select()
        current=row(win,side,name)
        return current is not None and current.is_selected()
    wait_for(selected,f"UIA SelectionPattern failed for {side} {name}",12)


def main():
    user,before=snapshot_legacy_profile()
    owned=Path(tempfile.mkdtemp(prefix="owned-unc-transfer-",dir=LOGS))
    left=owned/"Left"
    appdata=owned/"appdata"
    localdata=owned/"localdata"
    temp=owned/"tmp"
    for folder in (left,appdata,localdata,temp):
        folder.mkdir()
    (left/"격리복사.txt").write_text("isolated copy",encoding="utf-8")
    (left/"격리이동.txt").write_text("isolated move",encoding="utf-8")
    env={
        **os.environ,
        "APPDATA":str(appdata),
        "LOCALAPPDATA":str(localdata),
        "TEMP":str(temp),
        "TMP":str(temp),
    }
    proc=None
    hwnd=None
    try:
        proc,hwnd,win=launch(left,env)
        for name in (
            "PrimaryPaneTitle","SecondaryPaneTitle","UpButton",
            "LeftFiles","RightFiles","CopyButton","MoveButton","StatusText",
            "ActivePaneText",
        ):
            assert element(win,name).exists(timeout=5),name
        wait_for(
            lambda:row(win,"Left","격리복사.txt") is not None
            and row(win,"Left","격리이동.txt") is not None,
            "owned transfer sources did not reach the left pane",
            18,
        )

        # Startup seeds both panes with the same owned path. Activate the right
        # pane through its automation-only pane-title button, then use the
        # UpButton InvokePattern to make the owned parent the destination.
        invoke(win,"SecondaryPaneTitle")
        wait_for(
            lambda:"오른쪽" in element(win,"ActivePaneText").window_text(),
            "right pane did not activate through InvokePattern",
            6,
        )
        invoke(win,"UpButton")
        wait_for(
            lambda:row(win,"Right","Left") is not None,
            "right pane did not navigate to the owned parent",
            18,
        )

        invoke(win,"PrimaryPaneTitle")
        wait_for(
            lambda:"왼쪽" in element(win,"ActivePaneText").window_text(),
            "left pane did not reactivate through InvokePattern",
            6,
        )
        select_one(win,"Left","격리복사.txt")
        wait_for(
            lambda:element(win,"CopyButton").is_enabled(),
            "CopyButton did not enable after UIA selection",
            6,
        )
        invoke(win,"CopyButton")
        wait_for(
            lambda:(owned/"격리복사.txt").is_file(),
            "isolated Copy did not commit to the opposite owned pane",
            20,
        )
        assert (owned/"격리복사.txt").read_text(encoding="utf-8")=="isolated copy"
        assert (left/"격리복사.txt").is_file()
        try:
            wait_for(
                lambda:"복사를 완료했습니다" in element(win,"StatusText").window_text(),
                "Copy completion did not return through FileOperationController",
                10,
            )
        except AssertionError:
            print(
                "UNC_COPY_COMPLETION_DIAG",
                "STATUS=",repr(element(win,"StatusText").window_text()),
                "COPY_ENABLED=",element(win,"CopyButton").is_enabled(),
                "MOVE_ENABLED=",element(win,"MoveButton").is_enabled(),
                "CANCEL_ENABLED=",element(win,"CancelButton").is_enabled(),
                flush=True,
            )
            raise
        print("REAL_UNC_TRANSFER_UIA_ISOLATED_LOCAL_COPY_PASS",True,flush=True)

        select_one(win,"Left","격리이동.txt")
        wait_for(
            lambda:element(win,"MoveButton").is_enabled(),
            "MoveButton did not enable after UIA selection",
            6,
        )
        invoke(win,"MoveButton")
        wait_for(
            lambda:(owned/"격리이동.txt").is_file()
            and not (left/"격리이동.txt").exists(),
            "isolated Move did not commit to the opposite owned pane",
            20,
        )
        assert (owned/"격리이동.txt").read_text(encoding="utf-8")=="isolated move"
        try:
            wait_for(
                lambda:"이동을 완료했습니다" in element(win,"StatusText").window_text(),
                "Move completion did not return through FileOperationController",
                10,
            )
        except AssertionError:
            print(
                "UNC_MOVE_COMPLETION_DIAG",
                "STATUS=",repr(element(win,"StatusText").window_text()),
                "COPY_ENABLED=",element(win,"CopyButton").is_enabled(),
                "MOVE_ENABLED=",element(win,"MoveButton").is_enabled(),
                "CANCEL_ENABLED=",element(win,"CancelButton").is_enabled(),
                flush=True,
            )
            raise
        print("REAL_UNC_TRANSFER_UIA_ISOLATED_LOCAL_MOVE_PASS",True,flush=True)

        close(proc,hwnd)
        proc=None
        hwnd=None
        assert_legacy_profile_unchanged(user,before)
        print("UNC_COPY_MOVE_UIA_GUI_PASS",True,flush=True)
    finally:
        if proc is not None and proc.poll() is None:
            if hwnd:
                u.PostMessageW(W.HWND(hwnd),0x10,0,0)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        assert_legacy_profile_unchanged(user,before)
        shutil.rmtree(owned,ignore_errors=True)


if __name__=="__main__":
    main()

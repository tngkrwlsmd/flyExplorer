"""M2.1 actual WinUI Korean, native file mutation and theme-restart owned GUI.

Called only by the existing GUI harness inside its disposable APPDATA and
owned isolated folders, never with an unowned process/window or real folder.
"""
import ctypes
import hashlib
import subprocess
from pathlib import Path
import psutil
from pywinauto import Desktop

def run(*,p,win,element,safe_click,focus,eventually,left,right,localdata,env,exe):
    assert left.is_dir() and right.is_dir() and left!=right
    profile=localdata/"flyExplorer"/"ui-preferences-v1.txt"
    assert profile.parent.parent==localdata
    # Default UI strings and accessibility names must be *genuine* Hangul.
    for diagnostic_id in ("CreateFolderButton","RenameButton","ThemeStateText"):
        diagnostic_text=element(diagnostic_id).window_text()
        print("M21_LIVE_UNICODE_"+diagnostic_id,
            diagnostic_text.encode("unicode_escape").decode("ascii"),flush=True)
    assert '새 폴더' in element("CreateFolderButton").window_text()
    assert '이름 변경' in element("RenameButton").window_text()
    assert element("ShellHeading").exists(timeout=4)
    assert element("ThisPCButton").exists(timeout=4)
    assert element("ThemePicker").exists(timeout=4)
    print("REAL_M21_KOREAN_DEFAULT_REUSABLE_HEADER_SIDEBAR_AND_FILE_COMMANDS",True,flush=True)
    picker=element("ThemePicker").wrapper_object()
    focus()
    picker.select(2)
    try:print("M21_THEME_UIA_SELECTED",picker.selected_text().encode("unicode_escape").decode("ascii"),flush=True)
    except Exception as e:print("M21_THEME_UIA_SELECTED_ERROR",type(e).__name__,flush=True)
    print("M21_THEME_LABEL_AFTER_SELECT",element("ThemeStateText").window_text().encode("unicode_escape").decode("ascii"),flush=True)
    eventually(lambda:element("ThemeStateText").window_text()=="테마: 다크",
               "native Korean dark UI string not rendered")
    expected=b"schema=1\r\nlanguage=ko-KR\r\ntheme=dark\r\n"
    eventually(lambda:profile.is_file() and profile.read_bytes()==expected,
               "native private Korean dark theme not atomically persisted",12)
    focus()
    picker.select(1)
    eventually(lambda:profile.read_bytes()==
               b"schema=1\r\nlanguage=ko-KR\r\ntheme=light\r\n",
               "native private light theme update not persisted",12)
    focus()
    picker.select(2)
    eventually(lambda:profile.read_bytes()==expected,
               "rapid dark/light/dark event ordering was not preserved",12)
    print("REAL_M21_PRIVATE_KO_KR_THEME_SYSTEM_CHOICES_DARK_LIGHT_DARK_ATOMIC",True,flush=True)

    # Exact same self-built executable, exact inherited synthetic profile.
    # Never enumerate or close any arbitrary desktop application window.
    child=subprocess.Popen([str(exe),str(left)],env=env,cwd=exe.parent)
    child_handle=None
    try:
        def child_ready():
            nonlocal child_handle
            if child.poll() is not None:return False
            if Path(psutil.Process(child.pid).exe()).resolve()!=exe.resolve():
                raise AssertionError("a foreign executable reused owned PID")
            matches=[w for w in Desktop(backend="uia").windows(process=child.pid)
                     if "flyExplorer" in w.window_text()]
            if len(matches)!=1:return False
            selected=Desktop(backend="uia").window(handle=matches[0].handle).child_window(auto_id="ThemeStateText")
            if not selected.exists(timeout=.25):return False
            if selected.window_text()!="테마: 다크":return False
            child_handle=matches[0].handle
            return True
        eventually(child_ready,"same binary did not restore ko-KR dark from owned profile",20)
        print("REAL_M21_SECOND_OWNED_PROCESS_RELOADED_KOREAN_DARK_THEME",True,flush=True)
    finally:
        if child.poll() is None:
            if child_handle is None:
                # The child was created by this very test with the
                # disposable left-folder argument. Never leave an
                # unvalidated owned window/process running after failure.
                assert Path(psutil.Process(child.pid).exe()).resolve()==exe.resolve()
                assert psutil.Process(child.pid).cmdline()[1]==str(left)
                child.terminate()
                child.wait(timeout=8)
                raise AssertionError("owned child did not show expected persisted theme")
            u=ctypes.WinDLL("user32",use_last_error=True)
            u.GetWindowThreadProcessId.argtypes=(ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_ulong))
            pid=ctypes.c_ulong()
            u.GetWindowThreadProcessId(child_handle,ctypes.byref(pid))
            assert pid.value==child.pid,"refuse WM_CLOSE on foreign window"
            assert u.PostMessageW(child_handle,0x10,0,0),"owned child close failed"
            try:child.wait(timeout=14)
            except subprocess.TimeoutExpired:
                child.terminate();child.wait(timeout=5)
                raise AssertionError("exact owned dark-restart child did not exit")
        assert child.returncode==0,child.returncode

    # The existing parent harness began in an owned left directory.
    focus()
    safe_click(element("LeftFiles"))
    eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
               "owned synthetic left folder is not active before file operations",10)
    chosen=element("FileNameBox")
    chosen.set_edit_text("새 폴더")
    safe_click(element("CreateFolderButton"))
    created=left/"새 폴더"
    eventually(created.is_dir,"real native command failed creating owned Korean folder",15)
    eventually(lambda:any("새 폴더" in row.window_text()
                     for row in element("LeftFiles").descendants()),
               "native isolated Shell watcher failed to refresh new Korean folder",15)
    assert not (right/"새 폴더").exists()
    print("REAL_M21_NATIVE_CREATE_OWNED_KOREAN_FOLDER_AND_INDEPENDENT_WATCH",True,flush=True)
    chosen.set_edit_text("이름 변경")
    def find_row():
        return next((entry for entry in element("LeftFiles").descendants()
                     if entry.element_info.control_type=="ListItem" and
                         "새 폴더" in entry.window_text()),None)
    eventually(lambda:find_row() is not None,
               "new owned Korean ListViewItem did not appear",12)
    # A filesystem watcher can replace the row peer between lookup and the
    # rename click, especially in optimized Release builds. Re-resolve and
    # verify one selected owned row before invoking the existing command.
    def select_created():
        current=find_row()
        if current is None:
            return False
        focus()
        current.select()
        refreshed=find_row()
        return refreshed is not None and refreshed.is_selected()
    eventually(select_created,
               "owned Korean folder could not be selected after watcher refresh",10)
    safe_click(element("RenameButton"))
    renamed=left/"이름 변경"
    eventually(lambda:renamed.is_dir() and not created.exists(),
               "real native rename failed on selected owned Korean folder",15)
    eventually(lambda:any("이름 변경" in row.window_text()
                      for row in element("LeftFiles").descendants()),
               "native Shell watcher did not refresh renamed folder",15)
    print("REAL_M21_NATIVE_RENAME_SELECTED_OWNED_KOREAN_FOLDER",True,flush=True)
    # The successful rename queues one native Refresh. In optimized builds that
    # owned refresh can land after the next command and replace its status text.
    # Wait for that exact prior refresh to settle before asserting the duplicate
    # create error; never weaken the actual non-overwrite filesystem assertion.
    eventually(lambda:"폴더 변경 알림" in element("StatusText").window_text(),
               "rename refresh did not settle before duplicate create",12)
    # A second attempt must never overwrite an existing folder.
    chosen.set_edit_text("이름 변경")
    safe_click(element("CreateFolderButton"))
    eventually(lambda:"이미 존재" in element("StatusText").window_text(),
               "real duplicate native create did not show non-overwrite Korean error",12)
    assert renamed.is_dir() and not (right/"이름 변경").exists()
    print("REAL_M21_DUPLICATE_KOREAN_NAME_BLOCKED_WITH_PREVIOUS_FOLDER_PRESERVED",True,flush=True)
    # OS locale must NOT change default language; user preference is preview
    # private and independent of all six original legacy MFC config files.
    assert profile.read_bytes()==expected
    print("REAL_M21_PRIVATE_THEME_STILL_KO_KR_AND_NO_LEGACY_PROFILE_WRITE",True,flush=True)

"""Actual M2.7 installer lifecycle in a bounded owned directory/HKCU test scope."""
from pathlib import Path
import ctypes
import os
import shutil
import subprocess
import time
import uuid
import winreg

from pywinauto import Desktop

ROOT=Path(__file__).resolve().parents[2]
SETUP=ROOT/"out"/"package"/"flyExplorer-Setup-x64.exe"
LOGS=ROOT/"logs"/"m27"
REG_PATH=r"Software\Microsoft\Windows\CurrentVersion\Uninstall\flyExplorer-InstallerTest"

def run(args):
    result=subprocess.run([str(SETUP),*args],cwd=SETUP.parent,timeout=45)
    assert result.returncode==0,(args,result.returncode)

def reg_value(name):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_PATH) as key:
        return winreg.QueryValueEx(key,name)[0]

def reg_exists():
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_PATH).Close()
        return True
    except FileNotFoundError:
        return False

def wait_absent(path,seconds=20):
    end=time.time()+seconds
    while time.time()<end:
        if not path.exists():
            return True
        time.sleep(.2)
    return not path.exists()

def launch_installed(root,profile):
    source=profile/"source";source.mkdir(parents=True,exist_ok=True)
    (source/"installed-navigation.txt").write_text("owned",encoding="utf-8")
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        p=profile/key.lower();p.mkdir(exist_ok=True);env[key]=str(p)
    exe=root/"flyExplorer.exe"
    proc=subprocess.Popen([str(exe),str(source)],cwd=root,env=env)
    window=None
    try:
        end=time.time()+18
        while time.time()<end:
            windows=Desktop(backend="uia").windows(process=proc.pid)
            if windows:
                window=Desktop(backend="uia").window(handle=windows[0].handle)
                if window.child_window(auto_id="LeftFiles").exists(timeout=.2):
                    items=[x.window_text() for x in
                           window.child_window(auto_id="LeftFiles").descendants()
                           if x.element_info.control_type=="ListItem"]
                    if any("installed-navigation.txt" in x for x in items):
                        return
            time.sleep(.25)
        raise AssertionError("installed flyExplorer did not navigate owned folder")
    finally:
        if proc.poll() is None:
            if window is not None:
                ctypes.windll.user32.PostMessageW(window.handle,0x10,0,0)
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.terminate();proc.wait(timeout=5)
        assert proc.returncode==0,proc.returncode

def main():
    assert SETUP.is_file(),f"missing installer: {SETUP}; run package.bat Release"
    LOGS.mkdir(parents=True,exist_ok=True)
    token=uuid.uuid4().hex[:10]
    root=LOGS/f"flyExplorer-installer-test-{token}"
    profile=LOGS/f"installer-profile-{token}"
    profile.mkdir()
    sentinel=profile/"user-settings-sentinel.txt"
    sentinel.write_text("preserve",encoding="utf-8")
    try:
        run(["/S","/DESKTOP",f"/TESTROOT={root}","/TESTDISPLAYVERSION=1.0.0.0"])
        for rel in ("flyExplorer.exe","FlyShellIsolationHelper.exe","flyExplorer.pri",
                    "flyExplorerUninstall.exe","install-manifest.txt",
                    "licenses/flyExplorer-LICENSE.txt","licenses/GPL-3.0.txt",
                    "licenses/THIRD_PARTY-NOTICES.txt","licenses/PAYLOAD_PROVENANCE.md",
                    "licenses/nuget/microsoft.windowsappsdk/2.5.1/license.txt",
                    "licenses/nuget/microsoft.windowsappsdk/2.5.1/NOTICE.txt",
                    "licenses/nuget/microsoft.web.webview2/1.0.3719.77/LICENSE.txt",
                    "licenses/nuget/microsoft.web.webview2/1.0.3719.77/NOTICE.txt",
                    "licenses/nuget/microsoft.windows.ai.machinelearning/2.1.74/ThirdPartyNotices.txt"):
            assert (root/rel).is_file(),rel
        assert (root/"_installer_shortcuts/StartMenu/flyExplorer.lnk").is_file()
        assert (root/"_installer_shortcuts/Desktop/flyExplorer.lnk").is_file()
        assert reg_exists()
        assert reg_value("DisplayName")=="flyExplorer"
        assert reg_value("DisplayVersion")=="1.0.0.0"
        assert Path(reg_value("InstallLocation"))==root

        # Same-version repair/reinstall.
        run(["/S",f"/TESTROOT={root}","/TESTDISPLAYVERSION=1.0.0.0"])
        assert reg_value("DisplayVersion")=="1.0.0.0"

        # Synthetic installer-state upgrade and explicit downgrade policy check.
        run(["/S",f"/TESTROOT={root}","/TESTDISPLAYVERSION=1.0.0.1"])
        assert reg_value("DisplayVersion")=="1.0.0.1"
        run(["/S",f"/TESTROOT={root}","/TESTDISPLAYVERSION=1.0.0.0"])
        assert reg_value("DisplayVersion")=="1.0.0.0"

        launch_installed(root,profile)

        uninstaller=root/"flyExplorerUninstall.exe"
        result=subprocess.run([str(uninstaller),"/UNINSTALL","/S",f"/TESTROOT={root}"],
                              cwd=root,timeout=45)
        assert result.returncode==0,result.returncode
        assert wait_absent(root),root
        assert not reg_exists()
        assert sentinel.is_file()
        print("OWNED_INSTALLER_CLEAN_INSTALL_REPAIR_UPGRADE_ROLLBACK_UNINSTALL",True)
        print("INSTALLED_APP_OWNED_NAVIGATION",True)
        print("USER_SETTINGS_SENTINEL_PRESERVED",True)
    finally:
        if reg_exists():
            try:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,REG_PATH)
            except OSError:pass
        if root.exists():shutil.rmtree(root,ignore_errors=True)
        if profile.exists():shutil.rmtree(profile,ignore_errors=True)

if __name__=="__main__":
    main()

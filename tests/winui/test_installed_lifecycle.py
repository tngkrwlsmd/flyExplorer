"""Actual installer lifecycle in a bounded owned directory/HKCU test scope.

This proves the current unsigned setup's bounded install/repair/update/rollback/
launch/uninstall behavior. It is not a signed clean-machine Program Files/HKLM
certification.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import time
import uuid
import winreg

import psutil
from pywinauto import Desktop

ROOT=Path(__file__).resolve().parents[2]
SETUP=ROOT/"out"/"package"/"flyExplorer-Setup-x64.exe"
LOGS=ROOT/"logs"/"m27"
REG_PATH=r"Software\Microsoft\Windows\CurrentVersion\Uninstall\flyExplorer-InstallerTest"

SHUTDOWN_HELPER=ROOT/"tools"/"winui"/"diagnose_installed_shutdown.py"
_shutdown_spec=importlib.util.spec_from_file_location(
    "diagnose_installed_shutdown",
    SHUTDOWN_HELPER,
)
assert _shutdown_spec is not None and _shutdown_spec.loader is not None
shutdown_helper=importlib.util.module_from_spec(_shutdown_spec)
_shutdown_spec.loader.exec_module(shutdown_helper)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def owned_runtime_processes(root):
    root=root.resolve()
    found=[]
    for proc in psutil.process_iter(["pid","exe"]):
        try:
            exe=proc.info.get("exe")
            if exe and Path(exe).resolve().is_relative_to(root):
                found.append(proc)
        except (psutil.Error,OSError,RuntimeError):
            pass
    return found


def wait_owned_runtime_processes(root,label,seconds=8):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        pending=owned_runtime_processes(root)
        if not pending:
            print("OWNED_INSTALLER_RUNTIME_PROCESSES_SETTLED",label,True,flush=True)
            return
        time.sleep(.2)
    pending=owned_runtime_processes(root)
    detail=[(proc.pid,proc.name()) for proc in pending if proc.is_running()]
    for proc in pending:
        try:proc.terminate()
        except psutil.Error:pass
    _,alive=psutil.wait_procs(pending,timeout=4)
    for proc in alive:
        try:proc.kill()
        except psutil.Error:pass
    raise AssertionError(
        "owned installed runtime process did not settle before next lifecycle phase: "
        +repr(detail)
    )


def runtime_provenance(root):
    path=root/"licenses"/"PAYLOAD_PROVENANCE.json"
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    assert data["format"]=="flyexplorer-runtime-provenance-v1"
    assert data["runtime_file_count"]==len(data["files"])
    for item in data["files"]:
        target=root/Path(item["path"])
        assert target.is_file(),item["path"]
        assert target.stat().st_size==item["bytes"],item["path"]
        assert sha256(target)==item["sha256"],item["path"]
    return data


def install_manifest(root):
    return {
        line.strip()
        for line in (root/"install-manifest.txt").read_text(
            encoding="utf-8-sig").splitlines()
        if line.strip()
    }


def assert_runtime_manifest_covered(root,provenance):
    installed=install_manifest(root)
    runtime={item["path"].replace("/","\\") for item in provenance["files"]}
    normalized={item.replace("/","\\") for item in installed}
    assert runtime<=normalized,(runtime-normalized)


def launch_installed(root,profile,label):
    source=profile/"source";source.mkdir(parents=True,exist_ok=True)
    (source/"installed-navigation.txt").write_text("owned",encoding="utf-8")
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        p=profile/key.lower();p.mkdir(exist_ok=True);env[key]=str(p)
    exe=root/"flyExplorer.exe"
    expected=sha256(exe)
    proc=subprocess.Popen([str(exe),str(source)],cwd=root,env=env)
    window=None
    try:
        end=time.time()+18
        while time.time()<end:
            if proc.poll() is not None:
                break
            windows=Desktop(backend="uia").windows(process=proc.pid)
            if windows:
                window=Desktop(backend="uia").window(handle=windows[0].handle)
                if window.child_window(auto_id="LeftFiles").exists(timeout=.2):
                    items=[x.window_text() for x in
                           window.child_window(auto_id="LeftFiles").descendants()
                           if x.element_info.control_type=="ListItem"]
                    if any("installed-navigation.txt" in x for x in items):
                        assert sha256(exe)==expected
                        print("INSTALLED_APP_OWNED_NAVIGATION",label,True,flush=True)
                        return
            time.sleep(.25)
        raise AssertionError("installed flyExplorer did not navigate owned folder")
    finally:
        if proc.poll() is None:
            if window is None:
                proc.terminate();proc.wait(timeout=5)
                raise AssertionError("owned installed app HWND unavailable at shutdown")
            diagnostic=shutdown_helper.post_close_and_observe(
                proc,
                window.handle,
                label=label,
                evidence_dir=Path(os.environ.get(
                    "FLYEXPLORER_REMOTE_EVIDENCE_DIR",
                    str(LOGS),
                )),
                timeout=16.0,
                interval=0.1,
            )
            if diagnostic["failure_category"]:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=5)
                raise AssertionError(
                    "owned installed app shutdown failed; "
                    +diagnostic["failure_category"]
                )
        assert proc.returncode==0,(
            "owned installed app exited nonzero without harness termination",
            proc.returncode,
        )
        wait_owned_runtime_processes(root,label)


def shutdown_probe(runtime_root):
    runtime_root=runtime_root.resolve()
    assert (runtime_root/"flyExplorer.exe").is_file(),runtime_root
    token=uuid.uuid4().hex[:10]
    profile=LOGS/f"shutdown-probe-profile-{token}"
    profile.mkdir(parents=True)
    try:
        launch_installed(runtime_root,profile,"shutdown-probe")
        print("OWNED_RUNTIME_SHUTDOWN_PROBE_PASS",True,flush=True)
    finally:
        if profile.exists():shutil.rmtree(profile,ignore_errors=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--runtime-root",type=Path)
    args=parser.parse_args()
    if args.runtime_root is not None:
        shutdown_probe(args.runtime_root)
        return

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
                    "licenses/PAYLOAD_PROVENANCE.json",
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
        provenance=runtime_provenance(root)
        assert_runtime_manifest_covered(root,provenance)
        print("OWNED_INSTALLER_RUNTIME_PROVENANCE_PASS",True,flush=True)
        launch_installed(root,profile,"clean-install")

        # Same-version repair must remove a prior manifest-owned obsolete file
        # and restore a corrupted current runtime byte-for-byte.
        obsolete=root/"obsolete-owned-runtime.bin"
        obsolete.write_bytes(b"owned obsolete payload")
        with (root/"install-manifest.txt").open("a",encoding="utf-8",newline="") as stream:
            stream.write("obsolete-owned-runtime.bin\r\n")
        repair_target=root/"StatusFooter.xbf"
        assert repair_target.is_file()
        repair_target.write_bytes(b"owned stale runtime")
        run(["/S",f"/TESTROOT={root}","/TESTDISPLAYVERSION=1.0.0.0"])
        assert not obsolete.exists()
        provenance=runtime_provenance(root)
        assert_runtime_manifest_covered(root,provenance)
        assert reg_value("DisplayVersion")=="1.0.0.0"
        print("OWNED_INSTALLER_STALE_MANIFEST_CLEANUP_PASS",True,flush=True)

        # Bounded installer-state upgrade and rollback use the exact current
        # payload. Cross-version signed rollback remains a separate external gate.
        run(["/S",f"/TESTROOT={root}","/TESTDISPLAYVERSION=1.0.0.1"])
        assert reg_value("DisplayVersion")=="1.0.0.1"
        provenance=runtime_provenance(root)
        assert_runtime_manifest_covered(root,provenance)
        launch_installed(root,profile,"update")
        print("OWNED_INSTALLER_UPDATE_LAUNCH_PASS",True,flush=True)

        run(["/S",f"/TESTROOT={root}","/TESTDISPLAYVERSION=1.0.0.0"])
        assert reg_value("DisplayVersion")=="1.0.0.0"
        provenance=runtime_provenance(root)
        assert_runtime_manifest_covered(root,provenance)
        launch_installed(root,profile,"rollback")
        print("OWNED_INSTALLER_ROLLBACK_LAUNCH_PASS",True,flush=True)

        uninstaller=root/"flyExplorerUninstall.exe"
        result=subprocess.run([str(uninstaller),"/UNINSTALL","/S",f"/TESTROOT={root}"],
                              cwd=root,timeout=45)
        assert result.returncode==0,result.returncode
        assert wait_absent(root),root
        assert not reg_exists()
        assert sentinel.is_file()
        print("OWNED_INSTALLER_CLEAN_INSTALL_REPAIR_UPDATE_ROLLBACK_UNINSTALL",True)
        print("USER_SETTINGS_SENTINEL_PRESERVED",True)
    finally:
        if reg_exists():
            try:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,REG_PATH)
            except OSError:pass
        if root.exists():shutil.rmtree(root,ignore_errors=True)
        if profile.exists():shutil.rmtree(profile,ignore_errors=True)


if __name__=="__main__":
    main()

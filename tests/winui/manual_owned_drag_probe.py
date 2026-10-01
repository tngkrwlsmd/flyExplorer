"""Human-pointer event discriminator; never moves real user files."""
import argparse
import hashlib
import os
from pathlib import Path
from paths import ROOT, APP, app_exe
import subprocess
import sys
import tempfile

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("configuration",choices=("Debug","Release"))
    args=ap.parse_args()
    if not sys.stdin.isatty():
        print("MANUAL_ONLY: interactive human console required; no GUI launched.")
        return 2
    here=APP
    root=ROOT
    exe=app_exe(args.configuration)
    assert exe.is_file(), "Compile the chosen configuration first."
    base=root/"logs"/"m23"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="manual-owned-drag-",dir=base))
    left=owned/"Left"
    right=owned/"Right"
    left.mkdir()
    right.mkdir()
    name="드래그_소유_파일.txt"
    (left/name).write_text("test-owned drag content",encoding="utf-8")
    env=os.environ.copy()
    env.update({"APPDATA":str(owned/"appdata"),
                "LOCALAPPDATA":str(owned/"localdata"),
                "TEMP":str(owned/"temp"),
                "TMP":str(owned/"temp"),
                "FLY_M23_OWNED_DRAG_TRACE":"YES"})
    for key in ("appdata","localdata","temp"):
        (owned/key).mkdir()
    for key in ("FLY_M23_OWNED_DRAG_TEST","FLY_M18_EXHAUST_TIMEOUT",
                "FLY_M18_OWNED_COM_HANG","FLY_M18_OWNED_SHELL_NOTIFY",
                "FLY_M18_LOOPBACK_UNC"):
        env.pop(key,None)
    names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
           "fxfile-coolbar.dat","fxfile-dlg_state.conf",
           "fxfile-folder_layout.conf")
    conf=Path(os.environ.get("APPDATA",""))/"fxfile"/"conf"
    before={n:hashlib.sha256((conf/n).read_bytes()).digest()
            for n in names if (conf/n).is_file()}
    product=Path(os.environ.get("LOCALAPPDATA",""))/"flyExplorer"
    def tree_hashes(root):
        return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob("*") if p.is_file()} if root.is_dir() else {}
    product_before=tree_hashes(product)
    process=subprocess.Popen([str(exe),str(left)],cwd=exe.parent,env=env,
                              stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    print("MANUAL_OWNED_PID",process.pid,flush=True)
    print("LEFT",left,flush=True)
    print("RIGHT",right,flush=True)
    print("TEST_NAME",name,flush=True)
    print("Select the right pane and enter RIGHT in its address box.")
    print("Hold the left mouse button on TEST_NAME in the left file list.")
    print("Move into the right file list and release. Observe the status")
    print("messages for list/row start, target over, and drop independently.")
    print("Close ONLY this newly launched flyExplorer instance before continuing.")
    try:
        input("After closing flyExplorer, press Enter here: ")
    except (EOFError, KeyboardInterrupt):
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=8)
        print("MANUAL_RESULT=INCONCLUSIVE (interactive console lost)")
        return 2
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        print("MANUAL_RESULT=INCONCLUSIVE (owned child did not close)")
        process.terminate()
        process.wait(timeout=5)
    copied=right/name
    copied_ok=(copied.is_file() and (left/name).is_file() and
               copied.read_bytes()==(left/name).read_bytes())
    print("OWNED_FILE_COPY="+("PASS" if copied_ok else "NOT_OBSERVED"),
          flush=True)
    print("OWNED_FLYEXPLORER_EXIT_ZERO",process.returncode==0,flush=True)
    legacy_unchanged=all((conf/n).is_file() and
                  hashlib.sha256((conf/n).read_bytes()).digest()==digest
                  for n,digest in before.items())
    product_unchanged=tree_hashes(product)==product_before
    unchanged=legacy_unchanged and product_unchanged
    print("ORIGINAL_USER_SETTINGS_UNCHANGED",unchanged,flush=True)
    print("OWNED_EVIDENCE_DIR",owned,flush=True)
    print("Leave drag-event arrival UNVERIFIED unless you personally")
    print("observed the corresponding live status text.")
    return 0 if unchanged and process.returncode==0 and copied_ok else 2

if __name__=="__main__":
    sys.exit(main())

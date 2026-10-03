$ErrorActionPreference = "Stop"
$dirty = @(git status --porcelain)
if ($dirty.Count -eq 0) {
    throw "Expected Known Folder artwork development changes."
}

$script = Join-Path $env:TEMP "fly_known_folder_after_factory.py"
@'
import base64, ctypes as c, hashlib, io, os, shutil, subprocess, time
from pathlib import Path
from PIL import Image
from pywinauto import Desktop

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
user=Path(os.environ["USERPROFILE"])
real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
before={name:hashlib.sha256((real/name).read_bytes()).digest()
        for name in LEGACY if (real/name).is_file()}

root=Path(os.environ["TEMP"])/"fly-known-after-factory-env"
if root.exists():
    shutil.rmtree(root)
for key in ("localappdata","appdata","temp","tmp"):
    (root/key).mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env["LOCALAPPDATA"]=str(root/"localappdata")
env["APPDATA"]=str(root/"appdata")
env["TEMP"]=str(root/"temp")
env["TMP"]=str(root/"tmp")
pref=Path(env["LOCALAPPDATA"])/"flyExplorer"
pref.mkdir(parents=True,exist_ok=True)
(pref/"ui-preferences-v1.txt").write_text(
    "schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=large-icons\r\n",
    encoding="ascii",newline="")

exe=Path(r"C:\dev\flyExplorer\out\winui\Release\flyExplorer.exe")
child=subprocess.Popen([str(exe),str(user)],cwd=exe.parent,env=env)
fw=None
deadline=time.time()+24
while time.time()<deadline:
    if child.poll() is not None:
        raise RuntimeError(f"flyExplorer exited early {child.returncode}")
    wins=[w for w in Desktop(backend="uia").windows(process=child.pid)
          if "flyExplorer" in w.window_text()]
    if len(wins)==1:
        fw=wins[0]
        break
    time.sleep(.25)
if not fw:
    raise RuntimeError("flyExplorer after window not found")

fw.set_focus()
try:
    fw.move_window(x=30,y=30,width=972,height=720,repaint=True)
except Exception:
    pass
time.sleep(3.0)

panes=[x for x in fw.descendants()
       if x.element_info.automation_id=="LeftFiles"]
if len(panes)!=1:
    raise RuntimeError(f"LeftFiles count {len(panes)}")
pane=panes[0]
rows=pane.descendants(control_type="ListItem")
known=[]
generic=[]
for item in rows:
    try:
        names=[x.element_info.name for x in item.descendants(control_type="Image")]
        if "Windows Known Folder artwork" in names:
            known.append(item)
        if "Windows Shell folder icon" in names:
            generic.append(item)
    except Exception:
        pass

print("KNOWN_FOLDER_ARTWORK_COUNT",len(known))
print("GENERIC_FOLDER_ICON_COUNT",len(generic))
for item in known:
    print("KNOWN_FOLDER_ARTWORK_ROW",repr(item.window_text()))
if len(known)<6:
    raise AssertionError(f"Expected at least 6 Known Folder artworks, got {len(known)}")

target=known[0]
try:
    target.iface_scroll_item.ScrollIntoView()
except Exception:
    try:
        target.select()
        target.set_focus()
    except Exception:
        pass
time.sleep(1.5)

print("VISIBLE_KNOWN_FOLDER_ROWS")
for item in known:
    try:
        r=item.rectangle()
        if r.width()>0 and r.height()>0:
            print(repr((item.window_text(),r.left,r.top,r.width(),r.height())))
    except Exception:
        pass

img=fw.capture_as_image().convert("RGB")
img.thumbnail((486,360))
buf=io.BytesIO()
img.save(buf,format="JPEG",quality=82,optimize=True)
print("FLY_AFTER_FACTORY_SCREENSHOT_BEGIN")
print(base64.b64encode(buf.getvalue()).decode("ascii"))
print("FLY_AFTER_FACTORY_SCREENSHOT_END")

c.windll.user32.PostMessageW(fw.handle,0x10,0,0)
try:
    child.wait(timeout=10)
except subprocess.TimeoutExpired:
    child.terminate()
    child.wait(timeout=8)
print("FLY_AFTER_FACTORY_EXIT",child.returncode)

unchanged=all((real/name).is_file() and
    hashlib.sha256((real/name).read_bytes()).digest()==digest
    for name,digest in before.items())
print("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",unchanged)
if child.returncode!=0 or not unchanged:
    raise AssertionError("Owned after visual acceptance did not exit cleanly")
shutil.rmtree(root,ignore_errors=True)
'@ | Set-Content -LiteralPath $script -Encoding utf8

python -X utf8 $script
$rc = $LASTEXITCODE
Remove-Item -LiteralPath $script -Force -ErrorAction SilentlyContinue
if ($rc -ne 0) { exit $rc }

Write-Output "KNOWN_FOLDER_FACTORY_VISUAL_ACCEPTANCE_PASS"

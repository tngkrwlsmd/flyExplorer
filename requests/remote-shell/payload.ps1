$ErrorActionPreference = "Stop"
$dirty = @(git status --porcelain)
if ($dirty.Count -ne 0) {
    $dirty | ForEach-Object { Write-Output $_ }
    throw "Expected clean checkout before Known Folder BEFORE capture."
}
$script = Join-Path $env:TEMP "fly_known_before_payload.py"
@'
import base64, io, os, shutil, subprocess, time, ctypes as c
from pathlib import Path
from PIL import Image
from pywinauto import Desktop

user=Path(os.environ["USERPROFILE"])
root=Path(os.environ["TEMP"])/"fly-known-before-env"
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
deadline=time.time()+20
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
    raise RuntimeError("flyExplorer before window not found")
fw.set_focus()
try:
    fw.move_window(x=30,y=30,width=972,height=720,repaint=True)
except Exception:
    pass
time.sleep(2.5)
panes=[x for x in fw.descendants()
       if x.element_info.automation_id=="LeftFiles"]
if len(panes)!=1:
    raise RuntimeError(f"LeftFiles count {len(panes)}")
pane=panes[0]
print("FLY_BEFORE_ITEMS")
for item in pane.descendants(control_type="ListItem"):
    try:
        r=item.rectangle()
        images=[x.element_info.name for x in item.descendants(control_type="Image")]
        print(repr((item.window_text(),r.left,r.top,r.width(),r.height(),images)))
    except Exception:
        pass
img=fw.capture_as_image().convert("RGB")
img.thumbnail((486,360))
buf=io.BytesIO()
img.save(buf,format="JPEG",quality=78,optimize=True)
print("FLY_BEFORE_KNOWN_SCREENSHOT_BEGIN")
print(base64.b64encode(buf.getvalue()).decode("ascii"))
print("FLY_BEFORE_KNOWN_SCREENSHOT_END")
c.windll.user32.PostMessageW(fw.handle,0x10,0,0)
try:
    child.wait(timeout=10)
except subprocess.TimeoutExpired:
    child.terminate()
    child.wait(timeout=8)
print("FLY_BEFORE_EXIT",child.returncode)
shutil.rmtree(root,ignore_errors=True)
'@ | Set-Content -LiteralPath $script -Encoding utf8
python -X utf8 $script
$rc = $LASTEXITCODE
Remove-Item -LiteralPath $script -Force -ErrorAction SilentlyContinue
if ($rc -ne 0) { exit $rc }

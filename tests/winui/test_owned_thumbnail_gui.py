"""Owned actual WinUI Windows Shell PNG thumbnail integration fixture."""
import ctypes as c
import hashlib
import os
from pathlib import Path
from paths import ROOT, APP, app_exe
import shutil
import subprocess
import sys
import tempfile
import time
from PIL import Image,ImageDraw
from pywinauto import Desktop
import psutil

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
def until(fn,why,timeout=22):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  try:
   if fn():return
  except Exception:pass
  time.sleep(.24)
 raise AssertionError(why)
def run(configuration="Debug"):
 here=APP
 root=ROOT
 exe=app_exe(configuration)
 assert exe.is_file()
 real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
 before={name:hashlib.sha256((real/name).read_bytes()).digest()
         for name in LEGACY if (real/name).is_file()}
 base=root/"logs"/"m24"
 base.mkdir(parents=True,exist_ok=True)
 owned=Path(tempfile.mkdtemp(prefix="thumb-owned-",dir=base))
 folder=owned/"images"
 folder.mkdir()
 picture=folder/"test-owned-png.png"
 img=Image.new("RGBA",(64,64),(207,40,24,255))
 ImageDraw.Draw(img).rectangle((23,0,63,63),fill=(33,105,209,255))
 img.save(picture)
 env=os.environ.copy()
 for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
  target=owned/key.lower()
  target.mkdir()
  env[key]=str(target)
 for key in ("FLY_M23_OWNED_DRAG_TEST","FLY_M23_OWNED_SESSION",
             "FLY_M23_OWNED_DRAG_TRACE"):
  env.pop(key,None)
 process=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
 ownedhwnd=None
 passed=False
 try:
  def get():
   nonlocal ownedhwnd
   if process.poll() is not None:return None
   if Path(psutil.Process(process.pid).exe()).resolve()!=exe.resolve():
    raise AssertionError("Owned GUI process executable changed")
   matches=[v for v in Desktop(backend="uia").windows(process=process.pid)
            if "flyExplorer - WinUI 3" in v.window_text()]
   if len(matches)!=1:return None
   ownedhwnd=matches[0].handle
   return Desktop(backend="uia").window(handle=ownedhwnd)
  win=None
  until(lambda:get() is not None,"Exact thumbnail owned GUI missing")
  win=get()
  def image_ready():
   pane=win.child_window(auto_id="LeftFiles")
   if not pane.exists(timeout=.2):return False
   rows=[item for item in pane.descendants()
         if item.element_info.control_type=="ListItem" and
            "test-owned-png.png" in item.window_text()]
   if len(rows)!=1:return False
   images=[v for v in rows[0].descendants()
           if v.element_info.control_type=="Image" and
           "Windows Shell image thumbnail" in v.element_info.name]
   return len(images)==1 and images[0].is_visible()
  until(image_ready,
        "Exact test-owned .png Windows thumbnail never rendered",24)
  print("ACTUAL_OWNED_OS_PNG_IMAGE_THUMBNAIL_IN_WINUI",True,flush=True)
  passed=True
 finally:
  if process.poll() is None:
   if Path(psutil.Process(process.pid).exe()).resolve()==exe.resolve():
    if ownedhwnd is not None:
     c.windll.user32.PostMessageW(ownedhwnd,0x10,0,0)
     try:process.wait(timeout=10)
     except subprocess.TimeoutExpired:
      process.terminate();process.wait(timeout=8)
    else:process.terminate();process.wait(timeout=8)
  unchanged=all((real/n).is_file() and
      hashlib.sha256((real/n).read_bytes()).digest()==data
      for n,data in before.items())
  print("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",unchanged,flush=True)
  if passed and unchanged:shutil.rmtree(owned)
  else:print("OWNED_THUMBNAIL_FIXTURE_RETAINED",owned,flush=True)
 return 0 if passed and unchanged else 1
if __name__=="__main__":
 sys.exit(run(sys.argv[1] if len(sys.argv)>1 else "Debug"))

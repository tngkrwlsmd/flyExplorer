"""Manual actual OS DPI/High Contrast/Narrator/IME in a separate Windows VM.

Must be run from that VM's interactive terminal AFTER a person selects the
actual Windows scale/contrast theme and enables Narrator. Does not mutate
global accessibility settings or create a user account. Successful UIA
enumeration is NOT a substitute for human Narrator announcement confirmation.
"""
import argparse,ctypes as c,hashlib,json,os,subprocess,sys,tempfile,time
from ctypes import wintypes as w
from pathlib import Path
import psutil
from pywinauto import Desktop
u=c.WinDLL("user32",use_last_error=True)
u.GetDpiForWindow.argtypes=(w.HWND,)
u.GetDpiForWindow.restype=w.UINT
class HC(c.Structure):
 _fields_=(("cbSize",w.UINT),("dwFlags",w.DWORD),
           ("lpszDefaultScheme",w.LPWSTR))
def current_hc():
 cstate=HC();cstate.cbSize=c.sizeof(cstate)
 assert u.SystemParametersInfoW(0x0042,cstate.cbSize,c.byref(cstate),0)
 return bool(cstate.dwFlags&1)
def wait_for(fn,t=22):
 end=time.monotonic()+t
 while time.monotonic()<end:
  if fn():return True
  time.sleep(.3)
 return False
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--expected-scale",type=int,choices=(100,125,150,200),required=True)
 ap.add_argument("--contrast",choices=("on","off"),required=True)
 ap.add_argument("--configuration",choices=("Debug","Release"),default="Release")
 args=ap.parse_args()
 if os.name!="nt" or not sys.stdin.isatty():
  print("BLOCKED: actual interactive test VM and human Narrator/IME required.")
  return 2
 a=Path(__file__).resolve().parents[2]/"app"/"winui"
 exe=a/"x64"/args.configuration/"FlyExplorerWinUIShell"/"FlyExplorerWinUIShell.exe"
 assert exe.is_file()
 real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
 names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
 protected={n:hashlib.sha256((real/n).read_bytes()).digest()
            for n in names if (real/n).is_file()}
 base=a.parents[1]/"logs"/"m24";base.mkdir(parents=True,exist_ok=True)
 owned=Path(tempfile.mkdtemp(prefix="manual-os-a11y-",dir=base))
 folder=owned/"source";folder.mkdir()
 korean=chr(0xD55C)+chr(0xAE00)
 (folder/(korean+"-owned.txt")).write_text("test-only",encoding="utf-8")
 env=os.environ.copy()
 for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
  target=owned/key.lower();target.mkdir();env[key]=str(target)
 proc=None;hwnd=None;accepted=False
 try:
  proc=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
  def ready():
   nonlocal hwnd
   if proc.poll() is not None:return False
   if Path(psutil.Process(proc.pid).exe()).resolve()!=exe.resolve():
    raise AssertionError("Preview PID mismatch")
   matches=[x for x in Desktop(backend="uia").windows(process=proc.pid)
            if "flyExplorer - WinUI 3" in x.window_text()]
   if len(matches)!=1:return False
   hwnd=matches[0].handle
   return True
  assert wait_for(ready),"Actual OS scale preview failed to launch"
  dpi=u.GetDpiForWindow(hwnd)
  contrast=current_hc()
  expected={100:96,125:120,150:144,200:192}[args.expected_scale]
  assert dpi==expected,("ACTUAL_OS_DPI_MISMATCH",dpi,expected)
  assert contrast==(args.contrast=="on"),(
      "ACTUAL_HIGH_CONTRAST_MISMATCH",contrast)
  ui=Desktop(backend="uia").window(handle=hwnd)
  names=("LeftFiles","RightFiles","LeftNameWidthSlider",
         "RightNameWidthSlider","AddressBox","SortPicker")
  for key in names:
   x=ui.child_window(auto_id=key)
   assert x.exists(timeout=3) and x.element_info.name,key
  print("ACTUAL_OS_DPI_HC_AND_UIA_MATCH",dpi,contrast,flush=True)
  print("HUMAN: using Narrator, read both pane accessible names and the")
  print("Korean file row; verify that spoken output is correct.")
  print("HUMAN: select FileNameBox and compose the exact Korean string")
  print(repr(korean+"??"),"with an ACTUAL Korean IME; do not click Create.")
  if input("Type YES only after real Narrator + IME checks: ").strip()!="YES":
   print("MANUAL_NARRATOR_OR_IME_UNVERIFIED")
   return 2
  typed=ui.child_window(auto_id="FileNameBox").window_text()
  assert typed==korean+chr(0xC785)+chr(0xB825),(
      "Actual owned IME input did not match expected Korean composition")
  accepted=True
  (owned/"observations.json").write_text(json.dumps({
    "actual_dpi":dpi,"os_high_contrast":contrast,
    "owned_uia_names":True,"human_real_narrator_confirmation":True,
    "human_real_korean_ime_match":True},indent=2),encoding="utf-8")
  print("MANUAL_REAL_OS_DPI_HC_NARRATOR_KOREAN_IME_PASS",True,flush=True)
 finally:
  if proc is not None and proc.poll() is None:
   if hwnd:u.PostMessageW(hwnd,0x10,0,0)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:
    proc.terminate();proc.wait(timeout=7)
  assert all((real/n).is_file() and
    hashlib.sha256((real/n).read_bytes()).digest()==h
    for n,h in protected.items())
  print("ORIGINAL_MFC_SETTINGS_UNCHANGED",True,flush=True)
  print("MANUAL_TEST_EVIDENCE_DIRECTORY",owned,flush=True)
 return 0 if accepted else 2
if __name__=="__main__":sys.exit(main())

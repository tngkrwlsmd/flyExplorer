"""Manual actual OS DPI/High Contrast/Narrator/IME in a separate Windows VM.

Must be run from that VM's interactive terminal AFTER a person selects the
actual Windows scale/contrast theme and enables Narrator. Does not mutate
global accessibility settings or create a user account. Successful UIA
enumeration is NOT a substitute for human Narrator announcement confirmation.

Release-gate matrix: run Release at 125/off, 150/off, 200/off, then 150/on.
Each run records the exact executable, DPI/scale, High Contrast, window bounds,
UIA names, pane/tab/navigation/file-list/theme state, Korean IME rename,
Narrator confirmation, clean shutdown, and preservation of real user settings.
"""
import argparse,ctypes as c,hashlib,json,os,subprocess,sys,tempfile,time
from ctypes import wintypes as w
from pathlib import Path
from paths import APP, app_exe
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
 a=APP
 exe=app_exe(args.configuration)
 assert exe.is_file()
 legacy_settings=Path(os.environ["APPDATA"])/"fxfile"/"conf"
 names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
 protected={n:hashlib.sha256((legacy_settings/n).read_bytes()).digest()
            for n in names if (legacy_settings/n).is_file()}
 product_settings=Path(os.environ["LOCALAPPDATA"])/"flyExplorer"
 def tree_hashes(root):
  return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in root.rglob("*") if p.is_file()} if root.is_dir() else {}
 product_before=tree_hashes(product_settings)
 base=a.parents[1]/"logs"/"m24";base.mkdir(parents=True,exist_ok=True)
 owned=Path(tempfile.mkdtemp(prefix="manual-os-a11y-",dir=base))
 evidence_path=owned/"observations.json"
 evidence={"result":"NOT TESTED","configuration":args.configuration,
           "expected_scale_percent":args.expected_scale,
           "expected_high_contrast":args.contrast,
           "executable":str(exe.resolve()),"narrator":"NOT TESTED",
           "korean_ime":"NOT TESTED","shutdown":"NOT TESTED",
           "user_settings_preserved":"NOT TESTED"}
 def save_evidence():
  evidence_path.write_text(json.dumps(evidence,indent=2,ensure_ascii=False),
                           encoding="utf-8")
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
    raise AssertionError("flyExplorer PID mismatch")
   matches=[x for x in Desktop(backend="uia").windows(process=proc.pid)
            if "flyExplorer" in x.window_text()]
   if len(matches)!=1:return False
   hwnd=matches[0].handle
   return True
  assert wait_for(ready),"flyExplorer failed to launch at the actual OS scale"
  dpi=u.GetDpiForWindow(hwnd)
  contrast=current_hc()
  expected={100:96,125:120,150:144,200:192}[args.expected_scale]
  assert dpi==expected,("ACTUAL_OS_DPI_MISMATCH",dpi,expected)
  assert contrast==(args.contrast=="on"),(
      "ACTUAL_HIGH_CONTRAST_MISMATCH",contrast)
  ui=Desktop(backend="uia").window(handle=hwnd)
  uia_ids=("LeftFiles","RightFiles","LeftNameWidthSlider",
           "RightNameWidthSlider","AddressBox","SortPicker",
           "LeftTabs","RightTabs","BackButton","ForwardButton","UpButton",
           "ThemeStateText","FileNameBox")
  uia_names={}
  for key in uia_ids:
   x=ui.child_window(auto_id=key)
   assert x.exists(timeout=3) and x.element_info.name,key
   uia_names[key]=x.element_info.name
  assert wait_for(lambda:str(folder).lower() in
                  ui.child_window(auto_id="AddressBox").get_value().lower()),(
                  "owned startup navigation did not reach the address box")
  assert wait_for(lambda:any((korean+"-owned.txt") in x.window_text()
      for x in ui.child_window(auto_id="LeftFiles").descendants()
      if x.element_info.control_type=="ListItem")),"owned Korean file row missing"
  rect=ui.rectangle()
  theme=ui.child_window(auto_id="ThemeStateText").window_text()
  renamed=korean+chr(0xC785)+chr(0xB825)+".txt"
  evidence.update({"actual_dpi":dpi,"actual_scale_percent":dpi*100//96,
    "os_high_contrast":contrast,"window_rect":[rect.left,rect.top,rect.right,rect.bottom],
    "uia_names":uia_names,"pane_tab_navigation":True,"owned_file_list":True,
    "theme_state_text":theme,"startup":"PASS"})
  save_evidence()
  print("ACTUAL_OS_DPI_HC_AND_UIA_MATCH",dpi,contrast,flush=True)
  print("HUMAN: using Narrator, read both pane accessible names and the")
  print("Korean file row; verify spoken output and current theme readability.")
  print("HUMAN: select the Korean owned file row, choose Rename, compose")
  print(repr(renamed),"with the ACTUAL Korean IME, then activate Rename.")
  if input("Type YES only after Narrator + IME + owned rename checks: ").strip()!="YES":
   evidence["result"]="NOT TESTED";save_evidence()
   print("MANUAL_NARRATOR_IME_OR_RENAME_UNVERIFIED")
   return 2
  typed=ui.child_window(auto_id="FileNameBox").window_text()
  assert typed==renamed,(
      "Actual owned IME input did not match expected Korean composition")
  assert (folder/renamed).is_file() and not (folder/(korean+"-owned.txt")).exists(),(
      "Actual owned Korean rename was not observed on disk")
  accepted=True
  evidence.update({"narrator":"PASS","korean_ime":"PASS",
                   "korean_filename_rename":"PASS","human_theme_readability":"PASS"})
  save_evidence()
  print("MANUAL_REAL_OS_DPI_HC_NARRATOR_KOREAN_IME_RENAME_PASS",True,flush=True)
 finally:
  if proc is not None and proc.poll() is None:
   if hwnd:u.PostMessageW(hwnd,0x10,0,0)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:
    proc.terminate();proc.wait(timeout=7)
  legacy_unchanged=all((legacy_settings/n).is_file() and
    hashlib.sha256((legacy_settings/n).read_bytes()).digest()==h
    for n,h in protected.items())
  product_unchanged=tree_hashes(product_settings)==product_before
  shutdown_ok=proc is not None and proc.returncode==0
  evidence.update({"shutdown":"PASS" if shutdown_ok else "FAIL",
    "user_settings_preserved":"PASS" if legacy_unchanged and product_unchanged else "FAIL"})
  if accepted:evidence["result"]="PASS" if shutdown_ok and legacy_unchanged and product_unchanged else "FAIL"
  save_evidence()
  print("ORIGINAL_USER_SETTINGS_UNCHANGED",legacy_unchanged and product_unchanged,flush=True)
  print("MANUAL_TEST_EVIDENCE_DIRECTORY",owned,flush=True)
 return 0 if evidence["result"]=="PASS" else 2
if __name__=="__main__":sys.exit(main())

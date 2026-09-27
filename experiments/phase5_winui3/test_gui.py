"""Actual WinUI 3 UI Automation and pointer/keyboard verification; local synthetic directories only."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import subprocess,time
from pywinauto import Desktop, mouse
from PIL import ImageGrab
base=Path(__file__).resolve().parent
root=base.parents[1]
exe=base/'x64/Debug/FlyExplorerWinUI3NavPoC/FlyExplorerWinUI3NavPoC.exe'
fixture=base/'out/fixture/My Documents'
music=fixture/'My Music'
pictures=fixture/'My Pictures'
for path in (music,pictures):path.mkdir(parents=True,exist_ok=True)
assert exe.is_file(),exe
p=subprocess.Popen([str(exe),str(music)],cwd=exe.parent,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
u=C.windll.user32
CB=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CB,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
own=[]
@CB
def walk(hwnd,_):
 pp=W.DWORD();u.GetWindowThreadProcessId(hwnd,C.byref(pp))
 if pp.value==p.pid and u.IsWindowVisible(hwnd):
  own.append(int(hwnd))
 return True
def eventual(pred,label,timeout=4):
 until=time.monotonic()+timeout
 while time.monotonic()<until:
  try:
   if pred():return
  except Exception:pass
  time.sleep(.12)
 raise AssertionError(label)
try:
 for _ in range(40):
  own.clear();u.EnumWindows(walk,0)
  if own or p.poll() is not None:break
  time.sleep(.2)
 assert own and p.poll() is None,'actual WinUI 3 GUI did not launch'
 win=Desktop(backend='uia').window(handle=own[0])
 back=win.child_window(auto_id='BackButton',control_type='Button')
 forward=win.child_window(auto_id='ForwardButton',control_type='Button')
 up=win.child_window(auto_id='UpButton',control_type='Button')
 addr=win.child_window(auto_id='AddressBox',control_type='Edit')
 status=win.child_window(auto_id='StatusText',control_type='Text')
 for el in (back,forward,up,addr,status):assert el.exists(timeout=3)
 def title():
  buf=C.create_unicode_buffer(1600)
  u.GetWindowTextW(own[0],buf,len(buf))
  return buf.value.lower()
 def status_text():return status.window_text()
 assert title().endswith('my music'),title()
 assert not back.is_enabled() and not forward.is_enabled() and up.is_enabled()
 up.click_input()
 print('DIAG_AFTER_UP','TITLE',repr(title()),'STATUS',repr(status_text()),'ADDRESS',repr(addr.window_text()),flush=True)
 eventual(lambda:title().endswith('my documents'),'Up did not navigate to parent')
 assert back.is_enabled()
 back.click_input()
 eventual(lambda:title().endswith('my music'),'Back did not navigate')
 assert forward.is_enabled()
 forward.click_input()
 eventual(lambda:title().endswith('my documents'),'Forward did not navigate')
 addr.click_input()
 addr.set_edit_text(str(pictures))
 addr.type_keys('{ENTER}',set_foreground=True)
 eventual(lambda:title().endswith('my pictures'),'Edit ENTER did not navigate to existing directory')
 assert not forward.is_enabled(),'new route should clear forward history'
 addr.click_input()
 addr.set_edit_text(str(fixture/'Missing Folder'))
 addr.type_keys('{ENTER}',set_foreground=True)
 eventual(lambda:'Not a folder' in status_text(),'Invalid path validation missing')
 assert title().endswith('my pictures'),'Invalid input unexpectedly navigated'
 addr.type_keys('{ESC}',set_foreground=True)
 eventual(lambda:addr.window_text().lower().endswith('my pictures'),'Escape failed to restore address')
 # Input, pointer hover and responsive window resizing on the real XAML controls.
 win.set_focus()
 rr=back.rectangle()
 mouse.move(coords=(rr.left+rr.width()//2,rr.top+rr.height()//2))
 time.sleep(.25)
 u.MoveWindow(own[0],100,95,1080,330,True)
 time.sleep(.35)
 assert not u.IsHungAppWindow(own[0]),'real WinUI3 UI unresponsive after resize'
 img=base/'out/real-winui3-navigation-96dpi-LOCAL-PRIVATE.png'
 rr=win.rectangle()
 ImageGrab.grab(bbox=(rr.left,rr.top,rr.right,rr.bottom),include_layered_windows=True).save(img)
 print('WINUI3_REAL_GUI_PASS Up Back Forward AddressEnter InvalidPath Escape Resize Hover',flush=True)
 print('DPI',u.GetDpiForWindow(own[0]),'IMAGE_LOCAL_ONLY',img.name,'FINAL_PATH',addr.window_text(),flush=True)
finally:
 for h in own:u.PostMessageW(h,0x10,0,0)
 try:p.wait(timeout=9)
 except subprocess.TimeoutExpired:
  p.terminate();p.wait(timeout=4)
  raise RuntimeError('Own WinUI3 test process did not close')
 print('OWN_WINUI3_PROCESS_EXIT',p.returncode,flush=True)
 if p.returncode!=0:raise RuntimeError('Isolated WinUI3 test process exit nonzero')

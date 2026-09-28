"""Explicitly test-owned product -> real MainFrame/CommandContext/ExplorerCtrl bridge.
All settings are private copies and both child processes must be owned by this test.
"""
from pathlib import Path
import os,re,shutil,hashlib,subprocess,tempfile,time,ctypes as C
from ctypes import wintypes as W
from pywinauto import Desktop

folder=Path(__file__).resolve().parent
repo=folder.parents[1]
product=Path(r'C:\dev\flyExplorer\bin\x64\fxfile.exe')
winui=folder/'x64/Debug/FlyExplorerWinUI3NavPoC/FlyExplorerWinUI3NavPoC.exe'
source=Path(os.environ['APPDATA'])/'fxfile'/'conf'
files=('fxfile.conf','fxfile-main.conf','fxfile-toolbar.dat','fxfile-coolbar.dat',
       'fxfile-dlg_state.conf','fxfile-folder_layout.conf')
assert product.is_file() and winui.is_file()
assert source.is_dir() and all((source/f).is_file() for f in files),'source configuration unavailable: do not touch'
original={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in files}
work=Path(tempfile.mkdtemp(prefix='isolated-owned-bridge-',dir=folder/'out'))
copy=work/'conf';copy.mkdir()
for f in files:shutil.copy2(source/f,copy/f)
raw=(copy/'fxfile.conf').read_bytes()
enc='utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8'
s=raw.decode(enc)
keys=('config.global_hotkey.enable','config.global_hotkey.show_tray',
      'config.global_hotkey.windows_startup','config.register_shell_context_menu','config.single_process')
for key in keys:
 s,n=re.subn(r'(?m)^(\s*'+re.escape(key)+r'\s*=\s*)[^\r\n]*',
             lambda m:m.group(1)+'0',s)
 assert n==1,'unknown cloned side-effect protection key: '+key
(copy/'fxfile.conf').write_bytes(s.encode(enc))
fixture=work/'fixture'/'My Documents'/'My Music';fixture.mkdir(parents=True)
(fixture/'child-sentinel.txt').write_text('synthetic\n',encoding='utf-8')
(fixture.parent/'parent-sentinel.txt').write_text('synthetic\n',encoding='utf-8')
appdata=work/'appdata';appdata.mkdir()
env=dict(os.environ,APPDATA=str(appdata))
u=C.windll.user32
CB=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CB,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
def title(hwnd):
 b=C.create_unicode_buffer(1200)
 u.GetWindowTextW(hwnd,b,1200)
 return b.value
def top_for(pid,pred):
 owned=[]
 @CB
 def scan(hwnd,_):
  p=W.DWORD();u.GetWindowThreadProcessId(hwnd,C.byref(p))
  if p.value==pid and u.IsWindowVisible(hwnd) and pred(title(hwnd)):
   owned.append(int(hwnd))
  return True
 u.EnumWindows(scan,0)
 return owned[0] if len(owned)==1 else 0
def waitfor(f,description,seconds=6):
 until=time.monotonic()+seconds
 last=None
 while time.monotonic()<until:
  try:
   last=f()
   if last:return last
  except Exception as ex:last=repr(ex)
  time.sleep(.13)
 raise AssertionError(description+' last='+str(last))
owned=[]
prod=None;ui=None
ph=wh=0
try:
 prod=subprocess.Popen([str(product),'--conf_dir',str(copy),str(fixture)],cwd=str(work),env=env,
                       stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 owned.append(prod)
 ph=waitfor(lambda:top_for(prod.pid,lambda t:t.endswith(' - fxfile')),
            'isolated real flyExplorer MainFrame')
 waitfor(lambda:title(ph).lower().endswith('my music - fxfile'),'product opening synthetic initial path')
 ui=subprocess.Popen([str(winui),str(fixture),
                      '--test-product-pid='+str(prod.pid),'--test-product-hwnd='+str(ph)],
                     cwd=str(winui.parent),stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 owned.append(ui)
 wh=waitfor(lambda:top_for(ui.pid,lambda t:t.lower().startswith('phase5 bridge -')),
            'actual WinUI 3 bridge should bind to test-owned real product',seconds=13)
 win=Desktop(backend='uia').window(handle=wh)
 btn={name:win.child_window(auto_id=name+'Button',control_type='Button')
      for name in ('Up','Back','Forward')}
 address=win.child_window(auto_id='AddressBox',control_type='Edit')
 status=win.child_window(auto_id='StatusText',control_type='Text')
 for item in list(btn.values())+[address,status]:
  assert item.exists(timeout=3),'missing actual WinUI 3 automation control'
 assert 'my music' in address.window_text().lower(),'not displaying real product initial title'
 print('REAL_BRIDGE_BOUND_TO_TEST_OWNED_PRODUCT',
       {'test_product_pid':prod.pid,'product_hwnd':ph,'winui_pid':ui.pid,'winui_hwnd':wh},flush=True)
 time.sleep(.65)
 for command,ending in [('Up','my documents - fxfile'),
                        ('Back','my music - fxfile'),
                        ('Forward','my documents - fxfile')]:
  # Invoke the actual XAML UIA button without shared-desktop pointer races; test_gui.py tests pointer/keyboard separately.
  btn[command].invoke()
  time.sleep(.22)
  print('BRIDGE_EXEC_TRACE',command,'WINUI_STATUS',repr(status.window_text()),'PRODUCT_TITLE',repr(title(ph)),'WINUI_TITLE',repr(title(wh)),flush=True)
  current=waitfor(lambda:title(ph) if title(ph).lower().endswith(ending) else None,
                  'real product did not obey WinUI control '+command)
  mirrored=waitfor(lambda:title(wh) if title(wh).lower().endswith(ending) else None,
                   'WinUI bridge title did not follow real product '+command)
  assert 'actual product command handled' in status.window_text().lower()
  print('WINUI_CONTROL_TO_EXISTING_REAL_ROUTER_PASS',command,current,flush=True)
  time.sleep(.7)
 assert not u.IsHungAppWindow(wh) and not u.IsHungAppWindow(ph)
 print('LIVE_REAL_PRODUCT_ROUTING_VIA_REAL_WINUI3_GUI_PASS',flush=True)
finally:
 # Release external automation COM references before closing the owned WinUI process.
 try:
  btn.clear()
  del btn,address,status,win
 except NameError: pass
 import gc
 gc.collect()
 for proc in reversed(owned):
  if proc.poll() is not None:continue
  # The WinUI process also has a visible notification-host HWND. A generic
  # "one visible titled window" search can find two and silently post nothing.
  # Close the exact main HWND validated earlier for this test-owned process.
  hwnd=wh if proc is ui else ph if proc is prod else 0
  owner=W.DWORD()
  if hwnd and u.IsWindow(hwnd):
   u.GetWindowThreadProcessId(hwnd,C.byref(owner))
  if hwnd and owner.value==proc.pid:
   assert u.PostMessageW(hwnd,0x10,0,0), 'WM_CLOSE post failed for owned main window'
  else:
   print('OWNED_MAIN_WINDOW_NOT_AVAILABLE_AT_CLOSE',proc.pid,flush=True)
  try:proc.wait(timeout=8)
  except subprocess.TimeoutExpired:
   proc.terminate();proc.wait(timeout=5)
   print('OWN_TEST_CHILD_TERMINATED_AFTER_TIMEOUT',proc.pid,flush=True)
 after={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in files}
 print('OWN_TEST_PROCESS_EXITS',[(p.pid,p.returncode) for p in owned],
       'ORIGINAL_USER_CONFIG_HASHES_UNCHANGED',original==after,flush=True)
 if original!=after:raise RuntimeError('Original user profile unexpectedly modified')
 if any(item.returncode != 0 for item in owned): raise RuntimeError('Test-owned child did not exit cleanly')

"""Only run against a separately built test-owned flyExplorer on a private profile.
The opt-in DLL is loaded INSIDE the real product's existing MFC UI process.
"""
from pathlib import Path
import ctypes as C,hashlib,os,re,shutil,subprocess,tempfile,time
from ctypes import wintypes as W
from pywinauto import Desktop

folder=Path(__file__).resolve().parent
repo=folder.parents[1]
product=repo/'bin/x64/fxfile.exe'
dll=folder/'x64/Debug/FlyExplorerIslandBridge/FlyExplorerIslandBridge.dll'
source=Path(os.environ['APPDATA'])/'fxfile'/'conf'
names=('fxfile.conf','fxfile-main.conf','fxfile-toolbar.dat',
       'fxfile-coolbar.dat','fxfile-dlg_state.conf','fxfile-folder_layout.conf')
assert product.is_file() and dll.is_file(),'build both isolated products before running'
assert source.is_dir() and all((source/f).is_file() for f in names),'read-only profile prerequisite'
original={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in names}
out=folder/'out'
out.mkdir(exist_ok=True)
work=Path(tempfile.mkdtemp(prefix='real-owned-island-',dir=out))
copy=work/'conf'
copy.mkdir()
for f in names:shutil.copy2(source/f,copy/f)
raw=(copy/'fxfile.conf').read_bytes()
enc='utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8'
content=raw.decode(enc)
for key in ('config.global_hotkey.enable','config.global_hotkey.show_tray',
            'config.global_hotkey.windows_startup','config.register_shell_context_menu',
            'config.single_process'):
 content,n=re.subn(r'(?m)^(\s*'+re.escape(key)+r'\s*=\s*)[^\r\n]*',
                   lambda m:m.group(1)+'0',content)
 assert n==1,'cloned side effect key not uniquely found: '+key
(copy/'fxfile.conf').write_bytes(content.encode(enc))
fixture=work/'fixture'/'My Documents'/'My Music'
fixture.mkdir(parents=True)
(fixture/'synthetic.txt').write_text('test fixture only\n')
trace=work/'island-dll-trace.log'
env={**os.environ,'APPDATA':str(work/'appdata'),
     'FLYEXP_PHASE5_TEST_ISLAND_DLL':str(dll),
     'FLYEXP_MFC_DLL_TRACE':str(trace)}
(work/'appdata').mkdir()
u=C.windll.user32
CB=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CB,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
def title(hwnd):
 buffer=C.create_unicode_buffer(1024)
 u.GetWindowTextW(hwnd,buffer,1024)
 return buffer.value
def main_window(pid):
 matches=[]
 @CB
 def scan(hwnd,_):
  p=W.DWORD()
  u.GetWindowThreadProcessId(hwnd,C.byref(p))
  if p.value==pid and title(hwnd).endswith(' - fxfile') and u.IsWindowVisible(hwnd):
   matches.append(int(hwnd))
  return True
 u.EnumWindows(scan,0)
 return matches[0] if len(matches)==1 else None
def eventually(fn,description,timeout=9):
 stop=time.monotonic()+timeout
 while time.monotonic()<stop:
  try:
   result=fn()
   if result:return result
  except Exception:pass
  time.sleep(.15)
 raise AssertionError(description+'; DLL trace='+trace.read_text(errors='replace') if trace.exists() else description)
proc=None
hwnd=None
try:
 proc=subprocess.Popen([str(product),'--conf_dir',str(copy),str(fixture)],
                       cwd=str(work),env=env,stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 hwnd=eventually(lambda:main_window(proc.pid),'actual isolated MFC MainFrame',13)
 eventually(lambda:title(hwnd).lower().endswith('my music - fxfile'),'initial folder')
 frame=Desktop(backend='uia').window(handle=hwnd)
 # Trigger the native MainFrame's WM_SIZE after DLL attachment. Native
 # toolbar creation can otherwise leave an island-sized zero rectangle.
 dimensions=frame.rectangle()
 assert u.MoveWindow(hwnd,100,100,(max)(1200,dimensions.width()),(max)(780,dimensions.height()),True)
 time.sleep(.45)
 buttons={x:frame.child_window(auto_id='Phase5Island'+x+'Button',control_type='Button')
          for x in ('Up','Back','Forward')}
 address=frame.child_window(auto_id='Phase5IslandAddressBox',control_type='Edit')
 status=frame.child_window(auto_id='Phase5IslandStatusText',control_type='Text')
 if not buttons['Up'].exists(timeout=2):
  from pywinauto.findwindows import find_elements
  ids=find_elements(backend='uia',process=proc.pid,
                    auto_id='Phase5IslandUpButton',top_level_only=False)
  children=[(d.element_info.automation_id,d.friendly_class_name())
            for d in frame.descendants()
            if (d.element_info.automation_id or '').startswith('Phase5Island')]
  trace_text=trace.read_text(errors='replace') if trace.exists() else ''
  all_hwnds=re.findall(r'dll-island-hwnd=(\d+)',trace_text)
  print('ISLAND_UIA_DIAGNOSTIC','globally_found',len(ids),
        'native_frame_descendants',children[:12],
        'bridge_hwnds',all_hwnds[-4:],flush=True)
 for control in [*buttons.values(),address,status]:
  assert control.exists(timeout=5),'missing in-process XAML: '+str(control)
 assert buttons['Up'].element_info.process_id==proc.pid,'XAML lives in another process'
 assert 'my music' in address.window_text().lower()
 print('REAL_PRODUCT_SAME_PROCESS_ISLAND_MFC_PASS','PID',proc.pid,flush=True)
 for command,ending in [('Up','my documents - fxfile'),
                        ('Back','my music - fxfile'),
                        ('Forward','my documents - fxfile')]:
  buttons[command].invoke()
  observed=eventually(lambda:title(hwnd) if title(hwnd).lower().endswith(ending) else None,
                      'native product ignored in-process XAML '+command)
  assert 'actual product command handled' in status.window_text().lower()
  assert ending.split(' - fxfile')[0] in address.window_text().lower()
  print('REAL_PRODUCT_COMMAND_VIA_IN_PROCESS_MFC_WINUI_PASS',command,observed,flush=True)
 assert not u.IsHungAppWindow(hwnd)
 rect=frame.rectangle()
 assert u.MoveWindow(hwnd,rect.left,rect.top,rect.width()+90,rect.height()+60,True)
 assert not u.IsHungAppWindow(hwnd)
 print('REAL_PRODUCT_IN_PROCESS_RESIZE_RESPONSIVE_PASS',flush=True)
finally:
 try:del buttons,address,status,frame
 except NameError:pass
 import gc
 gc.collect()
 if proc is not None and proc.poll() is None:
  if hwnd and u.IsWindow(hwnd):assert u.PostMessageW(hwnd,0x10,0,0)
  try:proc.wait(timeout=9)
  except subprocess.TimeoutExpired:
   proc.terminate()
   proc.wait(timeout=5)
   print('OWN_PRODUCT_FORCED_SHUTDOWN',flush=True)
 after={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in names}
 print('ORIGINAL_SIX_USER_CONFIG_HASHES_UNCHANGED',after==original,
       'PRODUCT_EXIT',None if proc is None else proc.returncode,
       'DLL_TRACE',trace.read_text(errors='replace') if trace.exists() else 'missing',flush=True)
 assert after==original,'Original user configuration was modified'
 if proc is not None:assert proc.returncode==0,'Owned product did not exit cleanly'

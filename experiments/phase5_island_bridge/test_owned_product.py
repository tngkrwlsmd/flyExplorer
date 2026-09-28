"""Only run against a separately built test-owned flyExplorer on a private profile.
The opt-in DLL is loaded INSIDE the real product's existing MFC UI process.
"""
from pathlib import Path
import ctypes as C,hashlib,os,re,shutil,subprocess,tempfile,time
from ctypes import wintypes as W
from pywinauto import Desktop,mouse

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
 # Trigger native layout after DLL attachment, then identify the exact child HWND
 # reported by the in-process XAML bridge itself.
 dimensions=frame.rectangle()
 assert u.MoveWindow(hwnd,100,100,(max)(1200,dimensions.width()),(max)(780,dimensions.height()),True)
 time.sleep(.45)
 def island_handle():
  if not trace.exists(): return 0
  values=re.findall(r'dll-island-hwnd=(\d+) visible=1',trace.read_text(errors='replace'))
  return int(values[-1]) if values else 0
 island=eventually(island_handle,'visible in-process XAML child HWND')
 island_pid=W.DWORD()
 u.GetWindowThreadProcessId(island,C.byref(island_pid))
 assert island_pid.value==proc.pid and u.IsChild(hwnd,island),'island must be a child in the real product PID'
 print('REAL_PRODUCT_SAME_PROCESS_ISLAND_MFC_PASS','PID',proc.pid,'ISLAND_HWND',island,flush=True)
 island_ui=Desktop(backend='uia').window(handle=island)
 descendants=[(d.element_info.automation_id,d.friendly_class_name(),d.window_text())
              for d in island_ui.descendants()]
 print('ISLAND_DIRECT_UIA_DESCENDANTS',descendants[:16],flush=True)
 controls={name:island_ui.child_window(auto_id='Phase5Island'+name+'Button',
                                     control_type='Button')
           for name in ('Up','Back','Forward')}
 for name,control in controls.items():
  assert control.exists(timeout=3),'missing actual XAML '+name+' button'
 assert 'Phase5IslandCurrentFolderText' in {item[0] for item in descendants}
 print('REAL_PRODUCT_TEST_DPI',u.GetDpiForWindow(hwnd),flush=True)
 rect_t=W.RECT()
 assert u.GetWindowRect(island,C.byref(rect_t))
 before=(rect_t.left,rect_t.top,rect_t.right,rect_t.bottom)
 command_id={'Up':32004,'Back':32006,'Forward':32007}
 for command,ending in [('Up','my documents - fxfile'),
                        ('Back','my music - fxfile'),
                        ('Forward','my documents - fxfile')]:
  actual=controls[command].rectangle()
  assert actual.width()>0 and actual.height()>0,'invalid actual XAML button geometry'
  mouse.click(coords=(actual.left+actual.width()//2,actual.top+actual.height()//2))
  observed=eventually(lambda:title(hwnd) if title(hwnd).lower().endswith(ending) else None,
                      'native product ignored in-process XAML pointer '+command)
  marker='dll-command='+str(command_id[command])+' result='
  eventually(lambda:marker in trace.read_text(errors='replace'),'missing XAML command trace '+command)
  eventually(lambda:'dll-focus-'+command.lower() in trace.read_text(errors='replace'),
             'XAML focus did not reach '+command)
  print('REAL_PRODUCT_COMMAND_VIA_IN_PROCESS_MFC_WINUI_PASS',command,observed,flush=True)
 assert not u.IsHungAppWindow(hwnd)
 host=frame.rectangle()
 assert u.MoveWindow(hwnd,host.left,host.top,host.width()+90,host.height()+60,True)
 time.sleep(.35)
 assert not u.IsHungAppWindow(hwnd)
 after_rect=W.RECT()
 assert u.GetWindowRect(island,C.byref(after_rect))
 after_island=(after_rect.left,after_rect.top,after_rect.right,after_rect.bottom)
 assert after_island!=before,'XAML child did not move/resize with MFC host'
 print('REAL_PRODUCT_IN_PROCESS_RESIZE_RESPONSIVE_PASS',before,'->',after_island,flush=True)
finally:
 try:del controls,island_ui,frame
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

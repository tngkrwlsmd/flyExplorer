"""Owned PX15 compact search overflow and file-pane usability check."""
from pathlib import Path
import base64, ctypes as c, hashlib, json, os, platform, shutil, subprocess, sys, tempfile, time, traceback
from ctypes import wintypes as w
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'/'winui'))
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop
from PIL import ImageGrab
import psutil
import argparse
parser=argparse.ArgumentParser(description='Owned compact search scrolling and matched visual captures')
parser.add_argument('--phase',choices=('before','after'),required=True)
PHASE=parser.parse_args().phase
BASE=ROOT/'logs'/'px15-search-layout-owned'
BASE.mkdir(parents=True,exist_ok=True)
exe=ROOT/'out'/'winui'/'Release'/'flyExplorer.exe'
owned=Path(tempfile.mkdtemp(prefix=PHASE+'-',dir=BASE)).resolve()
fixture=owned/'fixture'; fixture.mkdir()
for name in ('search-owned-one.txt','second-owned.txt','owned-note.md'):
    (fixture/name).write_text('owned search visual fixture',encoding='utf-8')
original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture.iterdir()}
env={k:v for k,v in os.environ.items() if not k.startswith('FLY')}
for key in ('APPDATA','LOCALAPPDATA','USERPROFILE','TEMP','TMP'):
    p=owned/key.lower(); p.mkdir(); env[key]=str(p)
legacy_root,legacy=snapshot_legacy_profile()
u=c.windll.user32
u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.MoveWindow.argtypes=(w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.BOOL)
u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.GetDpiForWindow.argtypes=(w.HWND,)
u.GetDpiForWindow.restype=w.UINT
app=subprocess.Popen([str(exe),str(fixture)],cwd=exe.parent,env=env)
hwnd=None; complete=False; images=[]
result={'phase':PHASE,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'windows':platform.version(),'captures':[]}
def wait(fn,label,seconds=20):return wait_until(fn,label,seconds=seconds,interval=.15)
def pid(h):
    n=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(n));return n.value
def rect(e):
    r=e.rectangle();return [r.left,r.top,r.right,r.bottom]
try:
    def view():
        global hwnd
        assert app.poll() is None
        assert Path(psutil.Process(app.pid).exe()).resolve()==exe.resolve()
        wins=[x for x in Desktop(backend='uia').windows(process=app.pid) if 'flyExplorer' in x.window_text()]
        if len(wins)!=1:return None
        hwnd=wins[0].handle;assert pid(hwnd)==app.pid
        return Desktop(backend='uia').window(handle=hwnd)
    win=wait(view,'owned app unavailable')
    el=lambda name:win.child_window(auto_id=name,visible_only=False)
    wait(lambda:'search-owned-one.txt' in ' '.join(x.window_text() for x in el('LeftFiles').descendants(control_type='ListItem')),'fixture not rendered')
    win.set_focus()
    assert pid(u.GetForegroundWindow())==app.pid
    sw,sh=u.GetSystemMetrics(0),u.GetSystemMetrics(1)
    assert sw>=1000 and sh>=620,(sw,sh)
    el('SearchPanelButton').invoke()
    wait(lambda:el('SearchTermBox').is_visible(),'search not open')
    el('SearchTermBox').set_edit_text('search-owned-one')
    el('SearchRunButton').invoke()
    wait(lambda:el('SearchMatches').descendants(control_type='ListItem'),'owned search empty')
    for theme,index in (('light',1),('dark',2)):
        el('ThemePicker').select(index)
        wait(lambda:('라이트' if index==1 else '다크') in el('ThemeStateText').window_text(),'theme not set')
        for label,width,height in (('wide',min(1220,sw-40),min(700,sh-60)),('compact',960,519)):
            assert u.MoveWindow(hwnd,20,20,width,height,True)
            time.sleep(.6)
            win.set_focus()
            assert pid(u.GetForegroundWindow())==app.pid
            r=win.rectangle()
            assert 0<=r.left<r.right<=sw and 0<=r.top<r.bottom<=sh
            if PHASE=='after':
                el('SearchPanel').wrapper_object().iface_scroll.SetScrollPercent(-1,0)
                time.sleep(.2)
            name=f'{PHASE}-{theme}-{label}'
            p=BASE/(name+'.png');ImageGrab.grab(bbox=tuple(rect(win)),include_layered_windows=True).save(p)
            images.append((name,p))
            nodes={node.element_info.automation_id:node for node in win.descendants()}
            controls={key:(rect(nodes[key]) if key in nodes else None) for key in
                      ('SearchRunButton','SearchCancelButton','SearchMatches','SearchLocateButton','LeftFiles','RightFiles')}
            result['captures'].append({'name':name,'window':rect(win),'dpi':u.GetDpiForWindow(hwnd),'controls':controls})
            if PHASE=='after':
                for key in ('LeftFiles','RightFiles'):
                    box=controls[key];assert box and box[3]-box[1]>=80,(key,box)
                    assert r.top<=box[1]<box[3]<=r.bottom,(key,box)
                for key in ('SearchRunButton','SearchCancelButton'):
                    box=controls[key];assert box and r.left<=box[0]<box[2]<=r.right and r.top<=box[1]<box[3]<=r.bottom,(key,box)
                if label=='compact':
                    el('SearchPanel').wrapper_object().iface_scroll.SetScrollPercent(-1,100)
                    time.sleep(.3)
                    matches=el('SearchMatches').descendants(control_type='ListItem')
                    assert len(matches)==1 and 'search-owned-one.txt' in matches[0].window_text()
                    matches[0].select()
                    assert el('SearchLocateButton').is_enabled()
                    panel=el('SearchPanel').rectangle(); button=el('SearchLocateButton').rectangle()
                    assert panel.top<=button.top<button.bottom<=panel.bottom
                    name=f'{PHASE}-{theme}-{label}-results';p=BASE/(name+'.png')
                    assert pid(u.GetForegroundWindow())==app.pid
                    ImageGrab.grab(bbox=tuple(rect(win)),include_layered_windows=True).save(p)
                    images.append((name,p))
        if PHASE=='after':
            # The selected result remains actionable after resize and scroll.
            el('SearchLocateButton').invoke()
            wait(lambda:not any(node.element_info.automation_id=='SearchPanel' for node in win.descendants()),'result folder navigation did not collapse search')
            wait(lambda:'search-owned-one.txt' in ' '.join(x.window_text() for x in el('LeftFiles').descendants(control_type='ListItem')),'result folder not rendered')
            result['selected_result_navigation']=True
            if index==1:
                el('SearchPanelButton').invoke()
                el('SearchRunButton').invoke()
                wait(lambda:el('SearchMatches').descendants(control_type='ListItem'),'owned search empty')
    complete=True
finally:
    if app.poll() is None:
        if hwnd:u.PostMessageW(hwnd,0x10,0,0)
        try:app.wait(timeout=15)
        except subprocess.TimeoutExpired:app.terminate();app.wait(timeout=6)
    result['normal_exit']=app.returncode==0
    assert_legacy_profile_unchanged(legacy_root,legacy);result['legacy_profile_unchanged']=True
    assert original=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture.iterdir()}
    result['owned_original_preserved']=True
    if complete and result['normal_exit']:
        assert owned.parent==BASE and not owned.is_symlink();shutil.rmtree(owned)
        result['owned_fixture_profiles_removed']=True
    print('PX15_SEARCH_RESULT='+json.dumps(result),flush=True)
    for name,p in images:print('OWNED_PNG_'+name+'='+base64.b64encode(p.read_bytes()).decode(),flush=True)
assert complete and result['normal_exit']

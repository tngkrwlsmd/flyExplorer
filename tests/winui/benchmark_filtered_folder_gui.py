"""Owned pending-navigation, sparse name-filter timings and zero-match pixels.

Two matched retained runtimes, one 8k local fixture, no clipboard/recycle actions.
"""
from pathlib import Path
import argparse,base64,ctypes as c,hashlib,json,os,re,shutil,statistics,subprocess,tempfile,time
from ctypes import wintypes as w
from paths import ROOT
from profile_guard import snapshot_legacy_profile,assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop,keyboard
from PIL import ImageGrab
import psutil
BASE=ROOT/'logs'/'five-goals-20261029'/'filtered'
u=c.windll.user32;u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.MoveWindow.argtypes=(w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.BOOL)
u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.GetDpiForWindow.argtypes=(w.HWND,);u.GetDpiForWindow.restype=w.UINT
u.GetCursorPos.argtypes=(c.POINTER(w.POINT),);u.GetCursorPos.restype=w.BOOL

def wait(fn,label,seconds=30):return wait_until(fn,label,seconds=seconds,interval=.06)
def owner(h):
    n=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(n));return n.value

class App:
    def __init__(self,exe,path,label,theme='light'):
        self.exe=exe;self.path=path;self.label=label;self.theme=theme;self.images=[];self.report={}
    def __enter__(self):
        point=w.POINT();assert u.GetCursorPos(c.byref(point)),'INPUT_DESKTOP_UNAVAILABLE'
        self.profile=Path(tempfile.mkdtemp(prefix='profile-',dir=BASE)).resolve()
        env={k:v for k,v in os.environ.items() if not k.startswith('FLY')}
        for key in ('APPDATA','LOCALAPPDATA','USERPROFILE','TEMP','TMP'):
            p=self.profile/key.lower();p.mkdir();env[key]=str(p)
        self.legacy_root,self.legacy=snapshot_legacy_profile()
        self.app=subprocess.Popen([str(self.exe),str(self.path)],cwd=self.exe.parent,env=env)
        try:
            self.hwnd=None
            def view():
                assert self.app.poll() is None,'owned app exited'
                assert Path(psutil.Process(self.app.pid).exe()).resolve()==self.exe.resolve()
                wins=[v for v in Desktop(backend='uia').windows(process=self.app.pid) if 'flyExplorer' in v.window_text()]
                if len(wins)!=1:return None
                self.hwnd=wins[0].handle;assert owner(self.hwnd)==self.app.pid
                return Desktop(backend='uia').window(handle=self.hwnd)
            self.win=wait(view,'owned window absent');self.win.set_focus()
            assert u.MoveWindow(self.hwnd,20,20,1160,640,True)
            self.el('ThemePicker').select(1 if self.theme=='light' else 2)
            wait(lambda:self.first(),'initial owned rows absent')
            self.process=psutil.Process(self.app.pid)
            self.report={'label':self.label,'theme':self.theme,'exe_sha256':hashlib.sha256(self.exe.read_bytes()).hexdigest()}
            return self
        except BaseException as exc:
            self.__exit__(type(exc),exc,exc.__traceback__)
            raise

    def el(self,key):return self.win.child_window(auto_id=key,visible_only=False)
    def rows(self,side='Left'):return self.el(side+'Files').descendants(control_type='ListItem')
    def first(self,side='Left'):
        rows=self.rows(side);return rows[0].window_text() if rows else ''
    def count(self):
        text=self.el('ItemCountText').window_text();m=re.match(r'(\d+)',text)
        return int(m[1]) if m else -1
    def keys(self,text):
        assert owner(u.GetForegroundWindow())==self.app.pid
        keyboard.send_keys(text,pause=0)
    def navigate(self,path,expected):
        self.keys('^l');self.el('AddressBox').set_edit_text(str(path));self.el('AddressBox').set_focus();self.keys('{ENTER}')
        wait(lambda:self.el('AddressBox').get_value().casefold()==str(path).casefold() and expected in self.first() and self.el('UpButton').is_enabled(),'owned navigation did not settle')
    def capture(self,tag):
        assert owner(u.GetForegroundWindow())==self.app.pid
        r=self.win.rectangle();assert 0<=r.left<r.right<=u.GetSystemMetrics(0) and 0<=r.top<r.bottom<=u.GetSystemMetrics(1)
        p=BASE/(self.label+'-'+self.theme+'-'+tag+'.png')
        ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom),include_layered_windows=True).save(p)
        self.images.append((tag,p));self.report['window']=[r.left,r.top,r.right,r.bottom];self.report['dpi']=u.GetDpiForWindow(self.hwnd)
    def __exit__(self,kind,value,tb):
        if self.app.poll() is None:
            if self.hwnd:u.PostMessageW(self.hwnd,0x10,0,0)
            else:self.app.terminate()
            try:self.app.wait(timeout=15)
            except subprocess.TimeoutExpired:self.app.terminate();self.app.wait(timeout=6)
        self.report['normal_exit']=self.app.returncode==0
        assert_legacy_profile_unchanged(self.legacy_root,self.legacy);self.report['original_settings_unchanged']=True
        if kind is None and self.report['normal_exit']:
            assert self.profile.parent==BASE.resolve() and not self.profile.is_symlink();shutil.rmtree(self.profile);self.report['profile_removed']=True
        print('FILTER_APP_RESULT='+json.dumps(self.report),flush=True)
        for tag,p in self.images:print('OWNED_PNG_'+self.label+'-'+self.theme+'-'+tag+'='+base64.b64encode(p.read_bytes()).decode(),flush=True)
        if kind is None:assert self.report['normal_exit'],'owned app did not exit normally'

def validate_filtered_order(app,mode):
    expected=[f'keep-{i:05d}.txt' for i in range(0,8000,100)]
    if mode==1:expected.reverse()
    rank={name:i for i,name in enumerate(expected)};seen=set();scroll=app.el('LeftFiles').iface_scroll
    for percent in range(0,101,10):
        if scroll.CurrentVerticallyScrollable:scroll.SetScrollPercent(-1,float(percent))
        names=[]
        for row in app.rows():
            match=re.search(r'keep-\d{5}\.txt',row.window_text())
            if match:names.append(match[0]);seen.add(match[0])
        assert all(x in rank for x in names)
        assert [rank[x] for x in names]==sorted(rank[x] for x in names),names
        if len(seen)==80:break
        time.sleep(.04)
    assert seen==set(expected),('filtered rows not fully observed',len(seen))
    if scroll.CurrentVerticallyScrollable:scroll.SetScrollPercent(-1,0)

def filtered(exe,big,label,review=False):
    with App(exe,big,label) as app:
        app.el('SortPicker').select(1)
        wait(lambda:'other-07999.txt' in app.first() and app.count()==8000,'full owned folder not sorted',60)
        app.el('LeftFiles').set_focus();app.keys('^+f')
        box=app.el('LeftNameFilterBox');wait(lambda:box.has_keyboard_focus(),'filter not revealed')
        opposite=app.first('Right');results=[]
        for mode in (0,1):
            box.set_edit_text('');app.el('SortPicker').select(mode)
            all_first='keep-00000.txt' if mode==0 else 'other-07999.txt'
            wait(lambda:app.count()==8000 and all_first in app.first(),'unfiltered ready state missing')
            samples=[]
            for trial in range(3):
                box.set_edit_text('');wait(lambda:app.count()==8000 and all_first in app.first(),'filter reset failed')
                started=time.perf_counter();box.set_edit_text('keep-*')
                expected='keep-00000.txt' if mode==0 else 'keep-07900.txt'
                wait(lambda:app.count()==80 and expected in app.first(),'filtered projection not ready')
                samples.append(round((time.perf_counter()-started)*1000,3))
            validate_filtered_order(app,mode)
            results.append({'mode':mode,'samples_ms':samples,'median_ms':statistics.median(samples),'visible_order_equivalent':True,'rss_mib':round(app.process.memory_info().rss/1048576,3)})
        app.report['items']=8000;app.report['survivors']=80;app.report['filter']='keep-*';app.report['measurements']=results
        if review:
            committed=app.el('AddressBox').get_value()
            for theme,index in (('light',1),('dark',2)):
                app.el('ThemePicker').select(index)
                box.set_edit_text('owned-no-match-*')
                wait(lambda:app.count()==0 and not app.rows(),'zero-match state did not settle')
                assert app.el('AddressBox').get_value()==committed and app.first('Right')==opposite
                app.capture(theme+'-zero-match')
                box.set_edit_text('keep-*');wait(lambda:app.count()==80,'filter clear/reapply failed')
            box.set_edit_text('');wait(lambda:app.count()==8000,'unfiltered list not restored')
            app.report['zero_match_clear_restored']=True
        assert app.first('Right')==opposite

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--scope',choices=('filter',),default='filter')
    args=parser.parse_args();BASE.mkdir(parents=True,exist_ok=True)
    assert args.baseline.resolve()==ROOT/'logs'/'five-goals-20261029'/'baseline-runtime'/'flyExplorer.exe'
    assert args.candidate.resolve()==ROOT/'out'/'winui'/'Release'/'flyExplorer.exe'
    data=BASE/('fixture-'+args.scope);assert not data.exists(),'owned fixture already exists';data.mkdir()
    a=data/'A';b=data/'B';big=data/'Big'
    for path in (a,b,big):path.mkdir()
    (a/'owned-a.txt').write_bytes(b'owned-a');(b/'owned-b.txt').write_bytes(b'owned-b')
    for i in range(8000):(big/(('keep' if i%100==0 else 'other')+f'-{i:05d}.txt')).write_bytes(f'owned-{i}'.encode())
    before={str(p.relative_to(data)):hashlib.sha256(p.read_bytes()).hexdigest() for p in data.rglob('*') if p.is_file()}
    passed=False
    try:
        if args.scope=='filter':
            filtered(args.baseline,big,'before-filter')
            filtered(args.candidate,big,'after-filter',review=True)
        passed=True
    finally:
        after={str(p.relative_to(data)):hashlib.sha256(p.read_bytes()).hexdigest() for p in data.rglob('*') if p.is_file()}
        assert before==after,'owned fixture bytes/names changed'
        print('FILTER_OWNED_BYTES_UNCHANGED=true',flush=True)
        if passed:
            assert data.parent==BASE.resolve() and not data.is_symlink();shutil.rmtree(data);print('FILTER_FIXTURE_REMOVED=true',flush=True)

if __name__=='__main__':main()

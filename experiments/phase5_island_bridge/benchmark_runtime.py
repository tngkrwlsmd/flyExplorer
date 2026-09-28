"""Opt-in isolated same-binary runtime sampling; local evidence, NOT formal benchmarking."""
from pathlib import Path
import ctypes as c, hashlib, json, os, re, shutil, subprocess, tempfile, time
from ctypes import wintypes as w
import psutil
repo=Path(__file__).resolve().parents[2]
product=repo/"bin/x64/fxfile.exe"
dll=repo/"experiments/phase5_island_bridge/x64/Debug/FlyExplorerIslandBridge/FlyExplorerIslandBridge.dll"
source=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
       "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
assert all((source/name).is_file() for name in names)
original={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in names}
out=repo/'experiments/phase5_island_bridge/out'
out.mkdir(exist_ok=True)
u=c.windll.user32
CB=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
u.EnumWindows.argtypes=[CB,w.LPARAM]
u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
def frame(pid):
    matches=[]
    @CB
    def scan(hwnd,_):
        actual=w.DWORD();u.GetWindowThreadProcessId(hwnd,c.byref(actual))
        if actual.value==pid and u.IsWindowVisible(hwnd):
            buff=c.create_unicode_buffer(800);u.GetWindowTextW(hwnd,buff,800)
            if buff.value.lower().endswith("my music - fxfile"):matches.append(int(hwnd))
        return True
    u.EnumWindows(scan,0)
    return matches[0] if len(matches)==1 else None
results=[]
for round_id in range(1,4):
    for mode in ("native","island"):
        work=Path(tempfile.mkdtemp(prefix=f"sample-{mode}-",
            dir=repo/"experiments/phase5_island_bridge/out"))
        config=work/"conf"; config.mkdir()
        for name in names:shutil.copy2(source/name,config/name)
        raw=(config/"fxfile.conf").read_bytes()
        enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
        settings=raw.decode(enc)
        for key in ("config.global_hotkey.enable","config.global_hotkey.show_tray",
                    "config.global_hotkey.windows_startup",
                    "config.register_shell_context_menu","config.single_process"):
            settings,count=re.subn(r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*",
                                   lambda m:m.group(1)+"0",settings)
            assert count==1,key
        (config/"fxfile.conf").write_bytes(settings.encode(enc))
        fixture=work/"fixture"/"My Documents"/"My Music"
        fixture.mkdir(parents=True)
        trace=work/"island-trace.log"
        appdata=work/"appdata";appdata.mkdir()
        env={**os.environ,"APPDATA":str(appdata)}
        env.pop("FLYEXP_PHASE5_TEST_ISLAND_DLL",None)
        env.pop("FLYEXP_MFC_DLL_TRACE",None)
        if mode=="island":
            env["FLYEXP_PHASE5_TEST_ISLAND_DLL"]=str(dll)
            env["FLYEXP_MFC_DLL_TRACE"]=str(trace)
        p=None
        try:
            t0=time.perf_counter()
            p=subprocess.Popen([str(product),"--conf_dir",str(config),str(fixture)],
                               cwd=str(work),env=env,stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            deadline=time.monotonic()+14
            hwnd=frame(p.pid)
            while not hwnd and time.monotonic()<deadline:
                if p.poll() is not None:raise RuntimeError(f"{mode} exited during startup")
                time.sleep(.08);hwnd=frame(p.pid)
            assert hwnd,f"{mode} frame timeout"
            frame_s=time.perf_counter()-t0
            ready_s=None
            if mode=="island":
                while time.monotonic()<deadline:
                    if trace.exists() and "dll-root-loaded" in trace.read_text(errors="replace"):
                        ready_s=time.perf_counter()-t0;break
                    time.sleep(.08)
                assert ready_s is not None,"Island XAML root did not load"
            time.sleep(.8)
            stats=psutil.Process(p.pid).memory_info()
            record={"round":round_id,"mode":mode,"frame_visible_s":round(frame_s,3),
                    "island_root_loaded_s":None if ready_s is None else round(ready_s,3),
                    "rss_mib":round(stats.rss/1048576,2),
                    "private_mib":round(stats.private/1048576,2),
                    "dpi":int(u.GetDpiForWindow(hwnd))}
            assert u.PostMessageW(hwnd,0x10,0,0),"WM_CLOSE failed"
            try:p.wait(timeout=9)
            except subprocess.TimeoutExpired:
                p.terminate();p.wait(timeout=5)
                raise AssertionError(f"{mode} did not shut down")
            assert p.returncode==0,(mode,p.returncode)
            if mode=="island":
                assert "dll-runtime-shutdown-complete" in trace.read_text(errors="replace")
            assert all(hashlib.sha256((source/name).read_bytes()).hexdigest()==original[name]
                       for name in names),"original config modified"
            results.append(record)
            print("SAMPLE",json.dumps(record,sort_keys=True),flush=True)
        finally:
            if p is not None and p.poll() is None:
                p.terminate();p.wait(timeout=5)
print("PAIRED_SAMPLE_COUNT",len(results))
for mode in ("native","island"):
    rows=[r for r in results if r["mode"]==mode]
    print("MEDIAN",mode,{key:round(sorted(r[key] for r in rows)[1],3)
         for key in ("frame_visible_s","rss_mib","private_mib")})
print("ALL_CONFIG_HASHES_MATCH",all(hashlib.sha256((source/name).read_bytes()).hexdigest()==original[name]
                                   for name in names))

"""Run F05 native extensions in a repo checkout with current base F05 files."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
TESTS=(
    'native_f05_group_projection.cpp',
    'native_f05_group_presentation.cpp',
    'native_f05_group_tab_cache.cpp',
    'native_f05_group_modes.cpp',
)

def main():
    compiler=shutil.which('cl.exe' if os.name=='nt' else 'g++')
    if not compiler:
        raise RuntimeError('F05_COMPILER_UNAVAILABLE')
    target=ROOT/'out/f05-native'
    if target.is_symlink() or ROOT.is_symlink():
        raise RuntimeError('F05_REFUSE_SYMLINK_OUTPUT')
    target.mkdir(parents=True,exist_ok=True)
    for name in TESTS:
        source=ROOT/'tests/winui'/name
        if not source.is_file():
            raise FileNotFoundError(source)
        binary=target/(source.stem+('.exe' if os.name=='nt' else ''))
        if binary.is_symlink():
            raise RuntimeError('F05_REFUSE_SYMLINK_BINARY')
        if os.name=='nt':
            cmd=[compiler,'/nologo','/std:c++17','/W4','/WX','/EHsc',str(source),'/Fe:'+str(binary)]
        else:
            cmd=[compiler,'-std=c++17','-Wall','-Wextra','-Werror','-pedantic','-O2',str(source),'-o',str(binary)]
        subprocess.run(cmd,cwd=target,check=True,timeout=90)
        subprocess.run([str(binary)],cwd=target,check=True,timeout=20)
    print('F05_EXTENDED_NATIVE_FOUR_CASES=PASS')

if __name__=='__main__':
    try:
        main()
    except (RuntimeError,OSError,subprocess.SubprocessError) as error:
        print('F05_EXTENDED_NATIVE=FAIL',str(error),file=sys.stderr)
        raise SystemExit(1)

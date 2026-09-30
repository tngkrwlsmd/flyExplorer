"""Read-only access to the retired MFC baseline stored only in Git history."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
MFC_REV="cbffb487635a94e625070d5bee9d5e6680006f12"

def _git(*args: str, check: bool=True):
    return subprocess.run(["git",*args],cwd=ROOT,capture_output=True,
                          check=check)

def text(path: str) -> str:
    result=_git("show",f"{MFC_REV}:{path}")
    return result.stdout.decode("utf-8-sig",errors="replace")

def exists(path: str) -> bool:
    return _git("cat-file","-e",f"{MFC_REV}:{path}",check=False).returncode==0

def revision_exists() -> bool:
    return _git("cat-file","-e",MFC_REV+"^{commit}",check=False).returncode==0

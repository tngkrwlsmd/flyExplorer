"""Canonical repository paths for WinUI tests and manual probes."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"
OUT=ROOT/"out"

def app_dir(configuration: str) -> Path:
    assert configuration in ("Debug","Release")
    return OUT/"winui"/configuration

def app_exe(configuration: str) -> Path:
    return app_dir(configuration)/"flyExplorer.exe"

def helper_exe(configuration: str) -> Path:
    assert configuration in ("Debug","Release")
    return OUT/"helper"/configuration/"FlyShellIsolationHelper.exe"

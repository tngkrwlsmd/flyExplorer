"""Low-cost Windows GUI runner health check used before GUI acceptance."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from high_contrast_state import query

ROOT = Path(__file__).resolve().parents[2]


def collect(configuration: str, require_exe: bool) -> dict[str, object]:
    if os.name != "nt":
        raise RuntimeError("runner health requires Windows")

    import psutil
    from pywinauto import Desktop

    current_session = psutil.Process(os.getpid()).terminal()
    explorer_pids: list[int] = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if (proc.info.get("name") or "").lower() != "explorer.exe":
                continue
            if current_session is None or proc.terminal() == current_session:
                explorer_pids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    windows = Desktop(backend="uia").windows()
    hc = query()
    exe = ROOT / "out" / "winui" / configuration / "flyExplorer.exe"
    if require_exe and not exe.is_file():
        raise RuntimeError(f"flyExplorer binary missing: {exe}")

    return {
        "python": sys.version.split()[0],
        "interactive_explorer_count": len(explorer_pids),
        "uia_window_count": len(windows),
        "high_contrast_enabled": hc.enabled,
        "high_contrast_scheme": hc.scheme,
        "configuration": configuration,
        "flyexplorer_exe_exists": exe.is_file(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--configuration", choices=("Debug", "Release"), default="Release"
    )
    parser.add_argument("--require-exe", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    result = collect(args.configuration, args.require_exe and not args.check)
    if result["interactive_explorer_count"] == 0:
        raise RuntimeError("no interactive Explorer desktop was found")
    print(
        "RUNNER_HEALTH_PASS " + json.dumps(result, ensure_ascii=False),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

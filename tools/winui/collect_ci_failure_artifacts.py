"""Collect bounded, privacy-conscious evidence for a failed self-hosted CI run."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "logs"
OUT = LOGS / "ci-failure-artifacts"
MAX_FILES_PER_KIND = 12
MAX_FILE_BYTES = 10 * 1024 * 1024


def _recent_files(root: Path, pattern: str, since: float) -> list[Path]:
    if not root.is_dir():
        return []
    items = [
        p for p in root.rglob(pattern)
        if p.is_file()
        and p.stat().st_mtime >= since
        and p.stat().st_size <= MAX_FILE_BYTES
    ]
    return sorted(
        items, key=lambda p: p.stat().st_mtime, reverse=True
    )[:MAX_FILES_PER_KIND]


def _copy(files: list[Path], destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for index, source in enumerate(files):
        target = destination / f"{index:02d}-{source.name}"
        shutil.copy2(source, target)
        copied.append(str(target.relative_to(OUT)))
    return copied


def _exe_for_window(hwnd: int) -> str:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    if not pid.value:
        return ""
    handle = kernel32.OpenProcess(0x1000, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(
            handle, 0, buffer, ctypes.byref(size)
        ):
            return ""
        return buffer.value
    finally:
        kernel32.CloseHandle(handle)


def _capture_flyexplorer_windows(
    destination: Path,
) -> tuple[list[str], list[str]]:
    notes: list[str] = []
    try:
        from PIL import ImageGrab
    except Exception as exc:
        return [], [f"Pillow/ImageGrab unavailable: {exc}"]

    user32 = ctypes.windll.user32
    windows: list[tuple[int, tuple[int, int, int, int]]] = []
    enum_proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )

    @enum_proc
    def visit(hwnd, _):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            exe = Path(_exe_for_window(int(hwnd))).name.casefold()
            if exe != "flyexplorer.exe":
                return True
            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            box = (rect.left, rect.top, rect.right, rect.bottom)
            if box[2] - box[0] > 100 and box[3] - box[1] > 100:
                windows.append((int(hwnd), box))
        except Exception as exc:
            notes.append(f"window enumeration warning: {exc}")
        return True

    user32.EnumWindows(visit, 0)
    destination.mkdir(parents=True, exist_ok=True)
    captures: list[str] = []
    for index, (_, box) in enumerate(windows[:3]):
        try:
            target = destination / f"live-flyexplorer-window-{index}.png"
            ImageGrab.grab(
                bbox=box, include_layered_windows=True
            ).save(target)
            captures.append(str(target.relative_to(OUT)))
        except Exception as exc:
            notes.append(f"window capture {index} failed: {exc}")
    if not windows:
        notes.append(
            "No visible flyExplorer.exe window remained at collection time."
        )
    return captures, notes


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.STDOUT,
            timeout=10,
        ).strip()
    except Exception as exc:
        return f"<unavailable: {exc}>"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--marker", required=True)
    parser.add_argument("--scope", default="")
    args = parser.parse_args()

    marker = ROOT / args.marker
    since = marker.stat().st_mtime - 2.0 if marker.is_file() else 0.0

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    copied_logs = _copy(
        _recent_files(LOGS / "winui-scoped", "*.log", since),
        OUT / "scoped-logs",
    )
    copied_pngs = _copy(
        _recent_files(LOGS / "phase6-winui", "*.png", since),
        OUT / "screenshots",
    )
    live_pngs, capture_notes = _capture_flyexplorer_windows(
        OUT / "screenshots"
    )

    metadata = {
        "collected_utc": datetime.now(timezone.utc).isoformat(),
        "scope": args.scope,
        "github_sha": os.environ.get("GITHUB_SHA", ""),
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "runner_name": os.environ.get("RUNNER_NAME", ""),
        "runner_os": os.environ.get("RUNNER_OS", ""),
        "head": _git(["rev-parse", "HEAD"]),
        "status": _git(["status", "--short"]),
        "copied_logs": copied_logs,
        "copied_screenshots": copied_pngs + live_pngs,
        "capture_notes": capture_notes,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = [
        "flyExplorer failed CI evidence report",
        f"scope={args.scope}",
        f"sha={metadata['github_sha'] or metadata['head']}",
        f"run_id={metadata['github_run_id']}",
        f"run_attempt={metadata['github_run_attempt']}",
        f"runner={metadata['runner_name']} / {metadata['runner_os']}",
        "",
        "Collected scoped logs:",
        *(f"- {item}" for item in copied_logs),
        "",
        "Collected screenshots:",
        *(f"- {item}" for item in metadata["copied_screenshots"]),
        "",
        "Capture notes:",
        *(f"- {item}" for item in capture_notes),
        "",
        "Bounded test-log tails:",
    ]
    for rel in copied_logs:
        path = OUT / rel
        report.append(f"\n===== {rel} =====")
        try:
            lines = path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            report.extend(lines[-120:])
        except Exception as exc:
            report.append(f"<unable to read: {exc}>")

    (OUT / "failure-report.txt").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(
        "CI_FAILURE_ARTIFACTS",
        f"logs={len(copied_logs)}",
        f"screenshots={len(metadata['copied_screenshots'])}",
        f"out={OUT}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

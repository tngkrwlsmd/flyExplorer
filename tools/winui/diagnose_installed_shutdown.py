"""Observe installed flyExplorer shutdown without hiding the failure boundary.

This helper owns only shutdown observation. It never builds, packages, installs,
or mutates product state beyond posting WM_CLOSE and, when requested by the
caller after evidence is captured, allowing the caller to terminate a stuck
process.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import time

import psutil

WM_CLOSE = 0x0010
USER32 = ctypes.windll.user32


def _window_text(hwnd: int) -> str:
    length = USER32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(max(length + 1, 1))
    USER32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value


def top_level_windows(pid: int) -> list[dict]:
    windows: list[dict] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _):
        owner = wintypes.DWORD()
        USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            windows.append(
                {
                    "hwnd": int(hwnd),
                    "exists": bool(USER32.IsWindow(hwnd)),
                    "visible": bool(USER32.IsWindowVisible(hwnd)),
                    "enabled": bool(USER32.IsWindowEnabled(hwnd)),
                    "title": _window_text(hwnd),
                }
            )
        return True

    if not USER32.EnumWindows(callback, 0):
        raise ctypes.WinError()
    return windows


def _process_snapshot(pid: int, known_children: set[int]) -> tuple[bool, list[dict]]:
    alive = psutil.pid_exists(pid)
    observed: dict[int, psutil.Process] = {}
    if alive:
        try:
            owner = psutil.Process(pid)
            observed[pid] = owner
            for child in owner.children(recursive=True):
                observed[child.pid] = child
                known_children.add(child.pid)
        except (psutil.Error, OSError):
            pass
    for child_pid in sorted(known_children):
        if child_pid in observed or not psutil.pid_exists(child_pid):
            continue
        try:
            observed[child_pid] = psutil.Process(child_pid)
        except (psutil.Error, OSError):
            pass

    processes: list[dict] = []
    for process_pid, process in sorted(observed.items()):
        try:
            processes.append(
                {
                    "pid": process_pid,
                    "name": process.name(),
                    "exe": process.exe(),
                    "status": process.status(),
                    "threads": len(process.threads()),
                    "is_main": process_pid == pid,
                }
            )
        except (psutil.Error, OSError, RuntimeError):
            processes.append(
                {
                    "pid": process_pid,
                    "is_main": process_pid == pid,
                    "unavailable": True,
                }
            )
    return alive, processes


def snapshot(pid: int, hwnd: int, started: float, known_children: set[int]) -> dict:
    pid_alive, processes = _process_snapshot(pid, known_children)
    windows = top_level_windows(pid) if pid_alive else []
    return {
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "pid_alive": pid_alive,
        "hwnd_exists": bool(USER32.IsWindow(hwnd)),
        "top_level_windows": windows,
        "processes": processes,
    }


def _print_snapshot(item: dict) -> None:
    children = [
        process["pid"]
        for process in item["processes"]
        if not process.get("is_main") and not process.get("unavailable")
    ]
    print(
        "SHUTDOWN_TIMELINE "
        f"T+{item['elapsed_seconds']:.3f} "
        f"HWND_EXISTS={str(item['hwnd_exists']).lower()} "
        f"PID_ALIVE={str(item['pid_alive']).lower()} "
        f"TOP_LEVEL_WINDOWS={len(item['top_level_windows'])} "
        f"CHILD_PIDS={children}",
        flush=True,
    )


def classify_final(final: dict, proc_poll: int | None) -> str | None:
    if proc_poll is not None:
        return None
    if not final["pid_alive"]:
        return "INSTALLED_APP_HARNESS_OBSERVATION_FAILURE"
    if final["hwnd_exists"]:
        return "INSTALLED_APP_WINDOW_CLOSE_TIMEOUT"
    if final["top_level_windows"]:
        return "INSTALLED_APP_WINDOW_REPLACED_TIMEOUT"
    return "INSTALLED_APP_PROCESS_EXIT_TIMEOUT"


def post_close_and_observe(
    proc: subprocess.Popen,
    hwnd: int,
    *,
    label: str,
    evidence_dir: Path,
    timeout: float = 16.0,
    interval: float = 0.1,
) -> dict:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    known_children: set[int] = set()
    before = snapshot(proc.pid, hwnd, started, known_children)
    _print_snapshot(before)

    posted = bool(USER32.PostMessageW(hwnd, WM_CLOSE, 0, 0))
    print(
        "SHUTDOWN_TIMELINE "
        f"T+{time.monotonic() - started:.3f} "
        f"WM_CLOSE_POSTED={str(posted).lower()} "
        f"PID={proc.pid} HWND={hwnd}",
        flush=True,
    )

    timeline = [before]
    next_periodic = 1.0
    prior_state = (
        before["pid_alive"],
        before["hwnd_exists"],
        len(before["top_level_windows"]),
    )
    deadline = started + timeout
    while time.monotonic() < deadline:
        item = snapshot(proc.pid, hwnd, started, known_children)
        timeline.append(item)
        state = (
            item["pid_alive"],
            item["hwnd_exists"],
            len(item["top_level_windows"]),
        )
        if state != prior_state or item["elapsed_seconds"] >= next_periodic:
            _print_snapshot(item)
            prior_state = state
            while item["elapsed_seconds"] >= next_periodic:
                next_periodic += 1.0
        if proc.poll() is not None or not item["pid_alive"]:
            break
        time.sleep(interval)

    final = snapshot(proc.pid, hwnd, started, known_children)
    if not timeline or final != timeline[-1]:
        timeline.append(final)
    _print_snapshot(final)

    proc_poll = proc.poll()
    category = (
        "INSTALLED_APP_WM_CLOSE_POST_FAILURE"
        if not posted
        else classify_final(final, proc_poll)
    )
    payload = {
        "format": "flyexplorer-installed-shutdown-v1",
        "label": label,
        "pid": proc.pid,
        "hwnd": hwnd,
        "wm_close_posted": posted,
        "timeout_seconds": timeout,
        "interval_seconds": interval,
        "proc_poll": proc_poll,
        "failure_category": category,
        "timeline": timeline,
    }
    path = evidence_dir / "installed-shutdown-result.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"INSTALLED_APP_SHUTDOWN_RESULT={path}", flush=True)
    if category:
        print(f"FAILURE_CATEGORY={category}", flush=True)
    else:
        print("INSTALLED_APP_SHUTDOWN_OBSERVED=PASS", flush=True)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--hwnd", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=16.0)
    args = parser.parse_args()

    class ExistingProcess:
        def __init__(self, pid: int):
            self.pid = pid

        def poll(self):
            return None if psutil.pid_exists(self.pid) else 0

    payload = post_close_and_observe(
        ExistingProcess(args.pid),
        args.hwnd,
        label=args.label,
        evidence_dir=args.evidence_dir,
        timeout=args.timeout,
    )
    return 2 if payload["failure_category"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

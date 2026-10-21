"""Owned fixed-local-folder helper latency; not WinUI end-to-end acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

from wire_client import parse, request

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/winui"))
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged


def roundtrip(helper, env, folder, offset, limit, timeout):
    started = time.perf_counter()
    child = subprocess.run(
        [str(helper)], input=request(folder, offset=offset, limit=limit),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        cwd=helper.parent, timeout=timeout, creationflags=0x08000000,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    if child.returncode:
        raise RuntimeError(f"helper exit {child.returncode}")
    # Validate the entire bounded reply before accepting any timing sample.
    return parse(child.stdout), elapsed_ms


def run_case(folder, count, helper, env, timeout, page_size=1024):
    if not 1 <= count <= 20000 or not 1 <= page_size <= 1024:
        raise ValueError("owned fixture/page bound")
    folder.mkdir()
    expected = {f"bench-{n:05d}.txt" for n in range(count)}
    started = time.perf_counter()
    for name in sorted(expected):
        (folder / name).write_bytes(b"synthetic\n")
    fixture_ms = (time.perf_counter() - started) * 1000
    seen = set()
    pages = []
    offset = 0
    while offset < count:
        reply, elapsed = roundtrip(helper, env, folder, offset, page_size, timeout)
        if reply["hr"] != 0 or Path(reply["folder"]["filesystem_path"]).resolve() != folder.resolve():
            raise AssertionError("helper returned an unsuccessful or foreign folder")
        names = [entry["name"] for entry in reply["entries"]]
        if len(names) != min(page_size, count - offset):
            raise AssertionError("helper page omitted owned entries")
        if len(set(names)) != len(names) or seen.intersection(names) or not set(names) <= expected:
            raise AssertionError("duplicate or foreign page entry")
        if bool(reply["flags"] & 1) != (offset + len(names) < count):
            raise AssertionError("helper continuation flag mismatch")
        seen.update(names)
        pages.append({"offset": offset, "entries": len(names), "elapsed_ms": round(elapsed, 3)})
        offset += len(names)
    if seen != expected or {p.name for p in folder.iterdir()} != expected:
        raise AssertionError("owned fixture inventory changed")
    if any((folder / name).read_bytes() != b"synthetic\n" for name in expected):
        raise AssertionError("owned fixture content changed")
    return {
        "items": count, "fixture_create_ms": round(fixture_ms, 3), "pages": pages,
        "first_page_ms": pages[0]["elapsed_ms"],
        "all_pages_ms": round(sum(p["elapsed_ms"] for p in pages), 3),
        "slowest_page_ms": max(p["elapsed_ms"] for p in pages),
        "all_entries_unique_and_preserved": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=int, choices=(200, 8000, 20000), default=200)
    parser.add_argument("--configuration", choices=("Debug", "Release"), default="Release")
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args(argv)
    if os.name != "nt" or not 0 < args.timeout <= 60:
        parser.error("Windows and a per-page timeout in (0, 60] are required")
    helper = ROOT / "out/winui" / args.configuration / "FlyShellIsolationHelper.exe"
    if not helper.is_file():
        parser.error("build the canonical app/runtime first")
    import ctypes
    if ctypes.windll.kernel32.GetDriveTypeW(str(ROOT.resolve().anchor)) != 3:
        parser.error("fixture must be on a fixed local drive")
    base = ROOT / "logs/helper-page-benchmark"
    base.mkdir(parents=True, exist_ok=True)
    report = {
        "scope": "native helper path-page IPC only; not GUI/model/sort/index latency",
        "cache": "uncontrolled OS caches; first sample is not a cold-cache guarantee",
        "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "helper_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
        "configuration": args.configuration, "platform": platform.platform(),
        "python": platform.python_version(), "timeout_seconds": args.timeout,
        "page_size": 1024, "cases": [], "status": "FAIL",
    }
    report_path = base / ("benchmark-" + str(time.time_ns()) + ".json")
    legacy_root, legacy = snapshot_legacy_profile()
    private = Path(os.environ["LOCALAPPDATA"]) / "flyExplorer"

    def private_snapshot():
        return None if not private.exists() else {
            str(p.relative_to(private)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in private.rglob("*") if p.is_file()
        }

    original_private = private_snapshot()
    try:
        with tempfile.TemporaryDirectory(prefix="owned-", dir=base) as directory:
            owned = Path(directory).resolve()
            if owned.parent != base.resolve() or not owned.name.startswith("owned-"):
                raise RuntimeError("unexpected disposable fixture path")
            env = {k: v for k, v in os.environ.items() if not k.startswith("FLY_")}
            for key in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "TEMP", "TMP"):
                location = owned / key.lower()
                location.mkdir()
                env[key] = str(location)
            # Prove the exact lifecycle on a small fixture before allocating more.
            for count in ([200] if args.items == 200 else [200, args.items]):
                report["cases"].append(run_case(owned / str(count), count, helper, env, args.timeout))
        report["status"] = "PASS"
    finally:
        try:
            assert_legacy_profile_unchanged(legacy_root, legacy)
            if private_snapshot() != original_private:
                raise AssertionError("original WinUI profile changed")
            report["original_user_settings_unchanged"] = True
        except BaseException:
            report["status"] = "FAIL"
            report["original_user_settings_unchanged"] = False
            raise
        finally:
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps({"report": str(report_path), **report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

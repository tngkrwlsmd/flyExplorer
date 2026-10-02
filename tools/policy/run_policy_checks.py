"""Validate the vendored agent policy with hash-locked dependencies."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / ".agent-policy"
CACHE = ROOT / ".cache" / "policy-validation"
LOCK = POLICY / "requirements.lock"
MARKER = CACHE / ".environment.sha256"


def environment_key() -> str:
    payload = LOCK.read_bytes() + (
        f"\n{sys.implementation.cache_tag}\n{sys.platform}\n{platform.machine()}\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ensure_dependencies() -> None:
    key = environment_key()
    if (
        MARKER.is_file()
        and MARKER.read_text(encoding="utf-8").strip() == key
        and (CACHE / "jsonschema").is_dir()
    ):
        return

    if CACHE.exists():
        shutil.rmtree(CACHE)
    CACHE.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable, "-m", "pip", "install",
        "--disable-pip-version-check", "--require-hashes", "--no-deps",
        "--target", str(CACHE), "-r", str(LOCK),
    ]
    print("POLICY_DEPENDENCY_INSTALL=" + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    MARKER.write_text(key + "\n", encoding="utf-8")


def run(command: list[str], env: dict[str, str]) -> None:
    print("POLICY_CHECK=" + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> int:
    ensure_dependencies()
    env = os.environ.copy()
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(CACHE) + (os.pathsep + prior if prior else "")
    run([
        sys.executable, "-X", "utf8", str(POLICY / "scripts" / "validate.py"),
        "--project-root", str(ROOT),
        "--project-file", str(POLICY / "PROJECT.md"),
        "--readiness", "development",
    ], env)
    run([
        sys.executable, "-X", "utf8",
        str(POLICY / "scripts" / "conformance.py"), "--coverage",
    ], env)
    print("POLICY_VALIDATION_COMPLETE=PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

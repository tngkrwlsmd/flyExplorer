"""Isolated Windows packaging contract test; NEVER calls dist/copy.bat in the repo."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "dist" / "copy.bat"
source = BATCH.read_text(encoding="utf-8-sig")
native = re.findall(r'(?im)^\s*call :require_input "([^"]+)"', source)
assert native, "copy.bat prereqs missing"
native = [s for s in native if s.lower().startswith(("..\\bin\\", "..\\src\\"))]
optional = {
    "FlyExplorerIslandBridge.dll": b"dummy-bridge-only\n",
    "FlyExplorerIslandBridge.pri": b"dummy-pri-only\n",
    "Microsoft.WindowsAppRuntime.Bootstrap.dll": b"dummy-bootstrap-only\n",
    "Microsoft.Web.WebView2.Core.dll": b"dummy-webview2-only\n",
}


def run_batch(dist: Path, enabled: bool) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.pop("FLYEXP_PHASE5_INCLUDE_WINUI", None)
    if enabled:
        env["FLYEXP_PHASE5_INCLUDE_WINUI"] = "1"
    return subprocess.run(
        ["cmd", "/d", "/c", "copy.bat"], cwd=dist, env=env,
        capture_output=True, text=True, errors="replace", timeout=35
    )


with tempfile.TemporaryDirectory(prefix="phase5-safe-package-",
                                 dir=ROOT / "logs" / "phase5") as tmp:
    base = Path(tmp)
    dist = base / "dist"
    dist.mkdir()
    shutil.copy2(BATCH, dist / "copy.bat")
    for raw in native:
        target = dist.joinpath(*raw.split("\\")).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"native-stub:" + target.name.encode("utf-8"))
    languages = base / "src" / "fxfile" / "Languages"
    languages.mkdir(parents=True, exist_ok=True)
    (languages / "English.xml").write_text("<test/>\n", encoding="utf-8")

    result = run_batch(dist, enabled=False)
    assert result.returncode == 0, ("default staging", result.stdout[-600:], result.stderr[-600:])
    regular = dist / "bin" / "x64"
    assert (regular / "fxfile.exe").exists(), "default x64 product not staged"
    assert not (regular / "resources.pri").exists(), "default unexpectedly includes WinUI PRI"
    assert not (regular / "FlyExplorerIslandBridge.dll").exists(), "default unexpectedly includes WinUI DLL"
    print("NORMAL_DIST_STAGE_UNCHANGED_PASS")

    release = base / "experiments" / "phase5_island_bridge" / "x64" / "Release" / "FlyExplorerIslandBridge"
    release.mkdir(parents=True)
    for name, value in optional.items():
        (release / name).write_bytes(value)
    result = run_batch(dist, enabled=True)
    assert result.returncode == 0, ("opt-in staging", result.stdout[-600:], result.stderr[-600:])
    assert (regular / "resources.pri").read_bytes() == optional["FlyExplorerIslandBridge.pri"]
    for name in ("FlyExplorerIslandBridge.dll",
                 "Microsoft.WindowsAppRuntime.Bootstrap.dll",
                 "Microsoft.Web.WebView2.Core.dll"):
        assert (regular / name).read_bytes() == optional[name], name
        assert not (dist / "bin" / "x86-unicode" / name).exists(), name
        assert not (dist / "bin" / "x86-multibyte" / name).exists(), name
    print("OPTIONAL_X64_RELEASE_PRI_AND_DEPENDENCIES_STAGE_PASS")

    sentinel = regular / "prior-stage-sentinel.txt"
    sentinel.write_bytes(b"keep-existing-output")
    (base / "bin" / "x64" / "resources.pri").write_bytes(b"preexisting-owned-pri")
    result = run_batch(dist, enabled=True)
    assert result.returncode != 0, "pre-existing PRI collision not rejected"
    assert sentinel.read_bytes() == b"keep-existing-output", "collision destroyed prior stage"
    print("RESOURCE_COLLISION_BLOCKS_BEFORE_STAGING_PASS")
    (base / "bin" / "x64" / "resources.pri").unlink()

    (release / "Microsoft.Web.WebView2.Core.dll").unlink()
    result = run_batch(dist, enabled=True)
    assert result.returncode != 0, "missing opt-in dependency not rejected"
    assert sentinel.read_bytes() == b"keep-existing-output", "missing dependency destroyed prior stage"
    print("MISSING_DEPENDENCY_TRANSACTIONAL_ABORT_PASS")

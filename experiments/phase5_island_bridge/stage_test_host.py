"""Reproducible experiment-only host staging. Never mutate the regular product output.

The DLL's generated PRI must be presented as resources.pri in the executable
directory of this separately copied unpackaged MFC host.
"""
from pathlib import Path
from typing import Optional
import hashlib
import shutil


def stage_test_host(source_exe: Path, generated_pri: Path, destination: Path,
                    bridge_dll: Optional[Path] = None) -> tuple[Path, Path]:
    source_exe = source_exe.resolve(strict=True)
    generated_pri = generated_pri.resolve(strict=True)
    destination.mkdir(parents=True, exist_ok=False)
    # The opt-in experiment launches this copied executable and its native
    # app-local dependencies, not the user's installed flyExplorer executable.
    copied_exe = destination / source_exe.name
    shutil.copy2(source_exe, copied_exe)
    for dependency in source_exe.parent.glob("*.dll"):
        shutil.copy2(dependency, destination / dependency.name)
    languages = source_exe.parent / "Languages"
    if languages.is_dir():
        shutil.copytree(languages, destination / "Languages")
    if bridge_dll is not None:
        bridge_dll = bridge_dll.resolve(strict=True)
        target_bridge = destination / bridge_dll.name
        assert not target_bridge.exists(), "refuse to overwrite host DLL"
        shutil.copy2(bridge_dll, target_bridge)
        assert hashlib.sha256(target_bridge.read_bytes()).digest() == hashlib.sha256(bridge_dll.read_bytes()).digest()
        # The unpackaged Windows App SDK release DLL imports bootstrap and
        # WebView2 native loader dependencies from its original build output.
        # Copy those *exact*, built companion DLLs into the owned host.
        for name in ("Microsoft.WindowsAppRuntime.Bootstrap.dll",
                     "Microsoft.Web.WebView2.Core.dll"):
            dependency = bridge_dll.parent / name
            if not dependency.is_file():
                raise FileNotFoundError(f"required opt-in bridge dependency missing: {dependency}")
            target = destination / name
            if target.exists():
                raise FileExistsError(f"refusing to overwrite host dependency: {target}")
            shutil.copy2(dependency, target)
            assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(dependency.read_bytes()).digest()
    target_pri = destination / "resources.pri"
    assert not target_pri.exists(), "refuse to overwrite any host resources.pri"
    shutil.copy2(generated_pri, target_pri)
    assert hashlib.sha256(target_pri.read_bytes()).digest() == hashlib.sha256(generated_pri.read_bytes()).digest()
    return copied_exe, target_pri

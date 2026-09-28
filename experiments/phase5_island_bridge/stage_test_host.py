"""Reproducible experiment-only host staging. Never mutate the regular product output.

The DLL's generated PRI must be presented as resources.pri in the executable
directory of this separately copied unpackaged MFC host.
"""
from pathlib import Path
import hashlib
import shutil


def stage_test_host(source_exe: Path, generated_pri: Path, destination: Path) -> tuple[Path, Path]:
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
    target_pri = destination / "resources.pri"
    assert not target_pri.exists(), "refuse to overwrite any host resources.pri"
    shutil.copy2(generated_pri, target_pri)
    assert hashlib.sha256(target_pri.read_bytes()).digest() == hashlib.sha256(generated_pri.read_bytes()).digest()
    return copied_exe, target_pri

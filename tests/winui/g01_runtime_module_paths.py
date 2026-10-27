"""Classify only the loaded CoreMessagingXP.dll origin of a test-owned app.

No private paths, mapped memory, process IDs or raw module addresses leave this
function. The caller supplies a verified PID's mapping filenames.
"""
from __future__ import annotations

import ntpath


def classify_coremsg_paths(executable, mapped_paths, program_files, windows_root):
    appdir = ntpath.normcase(ntpath.normpath(ntpath.dirname(executable)))
    package_root = ntpath.normcase(
        ntpath.normpath(ntpath.join(program_files, "WindowsApps")))
    system_root = ntpath.normcase(
        ntpath.normpath(ntpath.join(windows_root, "System32")))
    if not appdir or not program_files or not windows_root:
        raise ValueError("missing classification anchor")
    prefixes = {
        "APPLOCAL": appdir + "\\",
        "WINDOWSAPPS": package_root + "\\",
        "SYSTEM": system_root + "\\",
    }
    unique = set()
    counts = {name: 0 for name in ("APPLOCAL", "WINDOWSAPPS", "SYSTEM", "OTHER")}
    for value in mapped_paths:
        if not isinstance(value, str):
            continue
        path = ntpath.normcase(ntpath.normpath(value))
        if ntpath.basename(path) != "coremessagingxp.dll" or path in unique:
            continue
        unique.add(path)
        # Cap each visible counter at 9: never leak unusual mapping breadth.
        for name in ("APPLOCAL", "WINDOWSAPPS", "SYSTEM"):
            if path.startswith(prefixes[name]):
                counts[name] = min(counts[name] + 1, 9)
                break
        else:
            counts["OTHER"] = min(counts["OTHER"] + 1, 9)
    return counts

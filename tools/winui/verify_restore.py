"""Validate NuGet restore inputs needed by the canonical WinUI build."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

DIRECT = {
    "Microsoft.WindowsAppSDK": "2.5.1",
    "Microsoft.Windows.CppWinRT": "2.0.250303.1",
    "Microsoft.Windows.SDK.BuildTools": "10.0.26100.9169",
    "Microsoft.Windows.ImplementationLibrary": "1.0.260126.7",
}


def fail(message: str) -> None:
    raise SystemExit("ERROR: " + message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assets", type=Path)
    parser.add_argument("packages", type=Path)
    args = parser.parse_args()

    if not args.assets.is_file():
        fail(f"NuGet assets file missing after restore: {args.assets}")
    data = json.loads(args.assets.read_text(encoding="utf-8"))
    libraries = set(data.get("libraries", {}))
    for package, version in DIRECT.items():
        key = f"{package}/{version}"
        if key not in libraries:
            fail(f"direct PackageReference did not resolve exactly: {key}")
        folder = args.packages / package.lower() / version.lower()
        if not folder.is_dir():
            fail(f"restored package directory missing: {folder}")

    winui = [
        key for key in sorted(libraries)
        if key.startswith("Microsoft.WindowsAppSDK.WinUI/")
    ]
    if len(winui) != 1:
        fail(
            "expected exactly one Microsoft.WindowsAppSDK.WinUI transitive "
            f"package; found {winui}"
        )

    winui_version = winui[0].split("/", 1)[1]
    winui_root = (
        args.packages / "microsoft.windowsappsdk.winui" / winui_version.lower()
    )
    required = (
        winui_root / "build" / "Microsoft.WindowsAppSDK.WinUI.targets",
        winui_root / "build" / "Microsoft.UI.Xaml.Markup.Compiler.targets",
        winui_root / "build" / "Microsoft.WinUI.targets",
        winui_root / "metadata" / "Microsoft.UI.Xaml.winmd",
    )
    for path in required:
        if not path.is_file():
            fail(f"WinUI/XAML restored build asset missing: {path}")

    transitive = sorted(
        key for key in libraries
        if key.startswith("Microsoft.WindowsAppSDK.")
        or key.startswith("Microsoft.Web.WebView2/")
    )
    print(
        "RESTORE_DIRECT_PACKAGES_OK",
        " ".join(f"{name}={version}" for name, version in DIRECT.items()),
    )
    print("RESTORE_WINUI_XAML_OK", winui[0])
    print("RESTORE_TRANSITIVE", " ".join(transitive))
    return 0


if __name__ == "__main__":
    sys.exit(main())

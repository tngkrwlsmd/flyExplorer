# flyExplorer packaging

package.bat Release builds one x64 setup executable from the canonical
out\winui\Release runtime set.

The installer is a repository-owned native Win32 bootstrap. This workstation
has no WiX, NSIS or Inno Setup toolchain installed, while Visual Studio and the
Windows SDK are already canonical build dependencies. The installer therefore
preserves the current unpackaged WinUI 3 execution model instead of introducing
MSIX identity changes.

Normal install scope:
- %ProgramFiles%\flyExplorer
- all-users Start Menu shortcut
- optional current-user desktop shortcut
- 64-bit HKLM Add/Remove Programs entry
- user settings under %LOCALAPPDATA%\flyExplorer are preserved on uninstall

The setup self-elevates for normal machine-wide install/uninstall. A bounded
/TESTROOT=<owned path> mode uses an owned directory and HKCU test uninstall key
so installer lifecycle can be validated without modifying Program Files.

The packaged payload also carries `licenses/` distribution materials: the
application license notice, the full GPLv3 text, current CREDITS, a hash-based
payload provenance snapshot, and every license/NOTICE/ThirdPartyNotices file
from the NuGet package/version sets that contributed runtime files (plus the
top-level Windows App SDK 2.5.1 terms). These files make notice delivery
explicit but do not by themselves constitute legal clearance for public
redistribution.

MSBuild is resolved through `tools/winui/resolve_msbuild.py`, which prefers an
explicit `MSBUILD` environment override, then `vswhere`, then the previously
validated Visual Studio 18 Community path as a compatibility fallback.

Production Authenticode signing order and secret-handling constraints are kept
in `packaging/SIGNING.md`; actual signing remains OPEN until a trusted signing
identity is available. GPL Corresponding Source publication is a separate
release gate documented in `packaging/SOURCE_DISTRIBUTION.md`; the current
private source repository is not treated as public source access for installer
recipients. Current copyright/rightsholder evidence and the remaining human
confirmation points are recorded in `packaging/RIGHTSHOLDER_REVIEW.md`.

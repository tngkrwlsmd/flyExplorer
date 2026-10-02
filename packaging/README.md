# flyExplorer packaging

From the repository root, package.bat Release builds one x64 setup executable
from the canonical out\winui\Release runtime set.

The installer project is reproducible: the tracked
packaging/installer/flyExplorerSetup.project-template.xml is materialized as the
ignored flyExplorerSetup.vcxproj by packaging/package.py before MSBuild runs.
The installer uses the same Visual Studio/MSBuild 18.x, v145 and Windows SDK
10.0.26100.0 contract as the app.

The installer is a repository-owned native Win32 bootstrap and preserves the
current unpackaged WinUI 3 execution model.

Normal install scope:
- %ProgramFiles%\flyExplorer
- all-users Start Menu shortcut
- optional current-user desktop shortcut
- 64-bit HKLM Add/Remove Programs entry
- user settings under %LOCALAPPDATA%\flyExplorer are preserved on uninstall

/TESTROOT=<owned path> is the bounded validation mode and avoids normal
Program Files/HKLM mutation.

## Current freshness

The tracked setup/provenance evidence was last produced on 2026-10-01 and
predates the v7 Window Tab/session product checkpoint. It must not be presented
as a package of the current product. Rebuild package.bat Release and rerun the
release payload/lifecycle checks before making a current package claim.

Tracked licenses/ materials improve notice/provenance evidence but do not clear
public redistribution.

See SIGNING.md, SOURCE_DISTRIBUTION.md, RIGHTSHOLDER_REVIEW.md and
docs/development/DISTRIBUTION_LICENSE_REVIEW.md for open release gates.

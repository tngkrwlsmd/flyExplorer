# flyExplorer packaging

For a single deliberate unsigned packaging operation from the repository root,
run:

    fly.bat package

This command executes the following sequence once, failing immediately if any
step fails:

1. `clean.bat build` (removes the ignored out/ directory)
2. `build.bat Release`
3. `python -X utf8 packaging\provenance.py --write`
4. `python -X utf8 packaging\provenance.py --check`
5. `package.bat Release`

The provenance write changes tracked
`packaging/licenses/PAYLOAD_PROVENANCE.json` and
`packaging/licenses/PAYLOAD_PROVENANCE.md`. Review those changes before
committing. Do not run the packaging pipeline on every normal test.
This installer exists only for private use; no public-release work is planned.

The provenance snapshot belongs to the exact Release byte set produced by step
2. It is not a cross-build reproducibility assertion. After any fresh rebuild,
run `--write` again before `--check` and package that same runtime; do not
reuse a snapshot generated from an earlier build merely because the source tree
is behaviorally unchanged.

`package.bat Release` builds one x64 setup executable from the canonical
`out\winui\Release` runtime set and fails closed if the generated provenance
snapshot does not match that runtime.

The native setup embeds an **XPRESS-HUFF compressed resource payload**
using the Windows built-in Cabinet Compression API. The canonical
`out/winui/Release` files and installed payload are not stripped,
and `PAYLOAD_PROVENANCE.json` still refers to the original raw bytes.
`packaging/package.py` round-trips each compressed file during packaging,
and the installer requires exact decompressed byte counts. On the
2026-10-22 exact Windows SHA `3219159c`, setup size dropped
from 124,933,120 to 55,290,368 bytes with the same 326 staged files.
This reduces download/storage size; the unpacked WinUI footprint is
intentionally unchanged.

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
- ordinary uninstall retains current-user settings under %LOCALAPPDATA%\flyExplorer
- interactive uninstall offers an **unchecked** opt-in to remove those settings
  and flyExplorer-owned cache/history/bookmarks as well
- unattended complete removal requires explicit
  `flyExplorerUninstall.exe /UNINSTALL /S /PURGEUSERDATA`
  (normal silent uninstall omits `/PURGEUSERDATA`)
- full removal targets only the current elevated process user's exact
  %LOCALAPPDATA%\flyExplorer folder, never other profiles or arbitrary
  user files. If UAC elevation switches accounts, it is **not** an all-users
  purge. Pre-existing untracked files inside the installation directory
  block removal instead of being deleted.
- an installed uninstaller schedules deletion of its own executable and
  install manifest after process exit; callers should wait for the root
  to disappear before interpreting removal as finished. A failed/
  incomplete operation must be investigated rather than ignored.

/TESTROOT=<owned path> is the bounded validation mode and avoids normal
Program Files/HKLM mutation. In TESTROOT mode an explicit purge applies
only to the exact matching synthetic `installer-profile-<token>` data
directory under the owned test parent, never real user settings.

## Private-use installer checkpoint

Retain the current installer/uninstaller for local personal installation.
When changing installation behavior, use only the affected safety-contract
suite and the explicitly owned /TESTROOT scenario; do not automatically
rebuild or exercise unrelated WinUI GUI features or machine-wide HKLM.
Former release, signing, public-source and publication plans are retired.
Preserve library/source notices already required by incorporated code.

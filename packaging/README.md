# flyExplorer packaging

From the repository root, the current unsigned packaging sequence is:

1. `clean.bat build`
2. `build.bat Release`
3. `python -X utf8 packaging\provenance.py --write`
4. `python -X utf8 packaging\provenance.py --check`
5. `package.bat Release`

`package.bat Release` builds one x64 setup executable from the canonical
`out\winui\Release` runtime set and fails closed if the generated provenance
snapshot does not match that runtime.

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

Remote Windows Task #382 (`37265695330`) accepted the current unsigned
packaging path from candidate
`8283ece6c4348a751f487a64230e1bc149a47a2f`, later merged through PR #27.
The run performed one clean Release build, generated and checked the exact
runtime provenance, built the setup and passed bounded `/TESTROOT`
clean-install, repair, update, rollback and uninstall.

The accepted runtime contained 305 files (17 product/generated and 288 exact
NuGet byte matches); the setup payload contained 326 files after distribution
materials were added. The checked-in shutdown probe also showed normal
`WM_CLOSE` process exit for clean-install, update and rollback.

This does not clear public redistribution. Production signing, clean-machine
Program Files/HKLM lifecycle, GPL source delivery and rightsholder review remain
separate gates.

See SIGNING.md, SOURCE_DISTRIBUTION.md, RIGHTSHOLDER_REVIEW.md and
docs/development/DISTRIBUTION_LICENSE_REVIEW.md for open release gates.

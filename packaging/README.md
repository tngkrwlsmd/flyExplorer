# flyExplorer packaging

From the repository root, the current unsigned packaging sequence is:

1. `clean.bat build`
2. `build.bat Release`
3. `python -X utf8 packaging\provenance.py --write`
4. `python -X utf8 packaging\provenance.py --check`
5. `package.bat Release`

The provenance snapshot belongs to the exact Release byte set produced by step
2. It is not a cross-build reproducibility assertion. After any fresh rebuild,
run `--write` again before `--check` and package that same runtime; do not
reuse a snapshot generated from an earlier build merely because the source tree
is behaviorally unchanged.

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

## Latest accepted package evidence

Remote Windows Task #435 (`37306799266`) accepted package candidate
`00f90c30800fb66f88184211442f6eeb05a950b7`. It clean-built the Release
runtime from candidate `1862231b271e9bb71d5adbf53439fe0d49b60af4`,
regenerated and checked provenance for that exact byte set, built the setup and
passed bounded `/TESTROOT` clean-install, repair, update, rollback and
uninstall.

The accepted runtime contains 305 files (17 product/generated and 288 exact
NuGet byte matches); the setup payload contains 326 files after distribution
materials are added. Runtime manifest SHA-256:
`40f0f12797c6731f823dd3e438b09fc575a78a54f9962c14fb572e5d70dfdcc5`.
Clean-install, update and rollback all launched owned content and exited normally
after `WM_CLOSE`.

Run #434 is retained as a useful fail-closed check: after a fresh rebuild it
correctly rejected provenance from an earlier build. The provenance snapshot is
exact-build evidence, not a cross-build reproducibility promise.

Public redistribution remains uncleared. Production signing, clean-machine
Program Files/HKLM lifecycle, GPL source delivery and rightsholder review remain
separate gates.

See SIGNING.md, SOURCE_DISTRIBUTION.md, RIGHTSHOLDER_REVIEW.md and
docs/development/DISTRIBUTION_LICENSE_REVIEW.md for open release gates.

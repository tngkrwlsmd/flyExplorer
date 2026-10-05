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

## Latest accepted package and source-identity evidence

Remote Windows Task #440 (`37376305779`) accepted binary source revision
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60`. It clean-built Release,
regenerated and checked exact runtime provenance, built the setup, generated and
checked the deterministic source bundle, bound both to a release identity, and
passed bounded `/TESTROOT` clean-install, repair, update, rollback and
uninstall.

Accepted hashes:
- runtime manifest:
  `61572e65c4a593e01607147596195041ce9d530e5f9fc21c9f9517f615b26c1d`;
- deterministic source ZIP:
  `5a263a42ecced3384be9a8ab131024ce309e4eb96b249bad1f8adc91f065ce1d`;
- unsigned setup:
  `825a644a8170acdaae43135604d6998ce517f882b3f8f228fa54cb30c1298a91`.

The tracked audit records are `SOURCE_BUNDLE_MANIFEST.json` and
`RELEASE_IDENTITY.json`. The concrete source ZIP and setup are preserved in
the private #440 Actions evidence artifact rather than committed to the
repository.

Public redistribution remains uncleared. Private source evidence is not public
recipient source availability; production signing, clean-machine Program
Files/HKLM lifecycle, GPL source-delivery/retention, final release tag and
rightsholder review remain separate gates.

For exact binary/source identity and the deterministic source bundle workflow,
see RELEASE_SOURCE.md.

See SIGNING.md, SOURCE_DISTRIBUTION.md, RIGHTSHOLDER_REVIEW.md and
docs/development/DISTRIBUTION_LICENSE_REVIEW.md for open release gates.

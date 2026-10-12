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
committing or publishing. Do not run the packaging pipeline on every normal
test, and do not treat an unsigned setup as a signed public release.

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

## Current product versus historical retained setup — 2026-10-12

The previously retained artifact below was built from
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60` and is
**not an installable copy of the current source**.
[Private Windows audit 38210591849](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38210591849)
recreated a separate unsigned test-only setup from
`2a736d85b22859a770138e4b50926ac125d1a052` and independently
verified exact-source bundle, runtime byte provenance and identity.
This fresh test build passed, but it was removed with its owned
workspace; only SHA-256 evidence remains in the Actions log.
The tracked `RELEASE_IDENTITY.json` and
`SOURCE_BUNDLE_MANIFEST.json` stay historical and must not be
advertised as fresh binaries. Rebuild, audit and **retain** all
matching final assets before release candidate acceptance.
No private test setup is signed or cleared for public distribution.

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

Public redistribution remains uncleared, but the source-delivery mechanism and
retention policy are now selected. Public binary conveyance uses GPLv3 section
6(d): the binary and deterministic source ZIP must be offered on the same public
GitHub Release page, without authentication or extra source charge. The reserved
tag is `v1.0.0.0`; it is intentionally not pre-created and will be locked by
GitHub Immutable Releases when the fully assembled draft is published.

Source remains available for the full public binary-availability period plus at
least 1095 days after binary withdrawal as an additional project commitment.
Production signing, clean-machine Program Files/HKLM lifecycle, public release
surface activation and rightsholder/legal review remain separate gates.

For exact binary/source identity and the deterministic source bundle workflow,
see RELEASE_SOURCE.md.

See SIGNING.md, SOURCE_DISTRIBUTION.md, RIGHTSHOLDER_REVIEW.md and
docs/development/DISTRIBUTION_LICENSE_REVIEW.md for open release gates.

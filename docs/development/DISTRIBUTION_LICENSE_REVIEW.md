# Distribution and license review — current release gate

This document records engineering evidence, not legal advice.

## 2026-10-22 optional complete removal and latest unsigned package evidence

Source revision `266a271f70da86da8be2bda0607ba29195cb8be6` introduced
explicit, opt-in current-user removal of flyExplorer-specific LocalAppData
settings/cache/bookmarks/history. Ordinary removal preserves settings.
An unattended complete purge requires all of `/UNINSTALL /S /PURGEUSERDATA`;
interactive removal presents an unchecked verification box. Remaining
untracked installation files prevent a successful uninstall result rather
than being deleted, and reparse points are rejected in owned-data cleanup.

On the interactive Windows desktop, the exact-SHA unsigned package
`flyExplorer-Setup-x64.exe` was 124,933,120 bytes (SHA-256
`c1d7d4248050aff56659cbb34ecee27f9407f488574c56739d8fff92c231f102`).
The full bounded `/TESTROOT` install/repair/test-update/test-rollback/
normal-uninstall/complete-uninstall and failure/retry lifecycle **PASS**,
exit 0; related Windows source contracts **9/9 PASS**. This candidate's
543-file deterministic corresponding-source ZIP SHA-256 is
`07ceacb5d823b6d9056fe8beabbc34f84fbfe6c177b3473bbfa27b2e4d311a10`;
runtime provenance SHA-256
`f0feca329fbc889800ffd36ddfb16b8d0798175c370f84a4cbd78604a016e1b2`;
the exact private release identity `--check` passed.

This does **not** establish clean-machine production install/uninstall,
administrator elevation across different Windows users, signed setup,
complete elimination of all OS metadata/traces, or public distribution
rights. `NotSigned` and other outstanding release permissions remain
blocking. Binary/source assets reside in a private Windows workspace,
not a public or immutable downloadable release.

## 2026-10-22 test-owned private setup / corresponding-source identity accepted

An isolated, interactive Windows user session generated an **unsigned**
setup from exact source commit `76559b0fd8499b866350d8b63e8980373f7792b7`,
then executed `tests/winui/test_installed_lifecycle.py` to successful
completion with exit 0. This verified `/TESTROOT` install,
owned-folder GUI launch, runtime-file provenance, same-version repair,
test display-version update/rollback using the same binary bytes,
uninstall, and preservation of an owned settings sentinel. The
dedicated HKCU test registration and temp installation folders were
absent after cleanup; seven Windows installer unit contracts also PASS.

The exact new setup was 124,923,392 bytes, SHA-256
`4d3d877121b7b78a23ddcb0d5977e75b395c096306e02dbb24a0a54a2ab3266a`.
Matching deterministic 543-file source ZIP SHA-256
`518af07865386fc7a13ca9f76d411c900df2d9cac87e720a8a546e9700fbdf7f`
and runtime manifest SHA-256
`979fbb3440b323b8c31ece58669c3d85092a89f59f6e5dcc8c5d109549a5dd65`
passed `release_identity.py --write/--check` together. Concrete
candidate files reside in a private test-owned Windows workspace, not
a published release. The setup reports Authenticode `NotSigned`.

**Public distribution remains NOT CLEARED.** A true clean-machine
Program Files/HKLM lifecycle, signed binaries and setup, the
rightsholder/license grants, immutable release assets and publicly
available corresponding source require separate acceptance. No
production publication/tag was created.

## 2026-10-22 F08 legacy ZIP source retirement (not release clearance)

After the separately accepted native Windows Explorer handoff (product
`1a5aece2df3fe9a6b548a511e949a62469d107d1`), the unused F08 archive
implementation and its pinned miniz 3.1.2 sources were removed from the
current source tree together with the nine ZIP-specific source-only tests.
No custom F08 codec remains in the active WinUI compile template. The
source-removal SHA `79b039453de5e56677e3f57f170ffc8817e1890f`
passed Windows source contracts, canonical Release build and owned functional
GUI in [central CI #39728188652](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39728188652).
This is not a new published source/binary package or license clearance.
The historical miniz version, original upstream
[richgel999/miniz](https://github.com/richgel999/miniz), MIT-style upstream
license, local `miniz_tinfl.c` / `miniz_tdef.c` include adaptations and
`miniz_tdef_compat.h` shim remain documented in Git history, including
the 2026-10-21 versions of this review and `UPSTREAM.md`.

This source removal is not a fresh package, legal audit, or declaration about
previous exact-SHA binaries. Do not remove or retroactively rewrite
historical release manifests, attribution or provenance snapshots.
`packaging/source_bundle.py` still writes the required deterministic GPL
source-distribution ZIP using Python's standard library, independently of
the deleted F08 engine. The current application's root `LICENSE`,
`CREDITS`, and `packaging/licenses/` payload-notice inputs are retained;
clean Release/package provenance and all public-distribution gates below
remain open until separately verified.

## Current product

The canonical product is the WinUI 3 application in app/winui plus src/base.
Retired MFC dependency findings are no longer part of the current runtime
inventory unless a component is reintroduced.

Release uses a self-contained Windows App SDK payload and tracked distribution
materials under packaging/licenses/.

## Latest package and source-identity evidence

Remote Windows Task #440 (`37376305779`) accepted the current unsigned setup
and exact binary/source identity from binary source revision
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60`. The clean Release runtime
contains 305 files (17 product/generated, 288 exact NuGet byte matches) with
manifest SHA-256
`61572e65c4a593e01607147596195041ce9d530e5f9fc21c9f9517f615b26c1d`.
The setup payload contains 326 files and the unsigned setup SHA-256 is
`825a644a8170acdaae43135604d6998ce517f882b3f8f228fa54cb30c1298a91`.

The deterministic source bundle contains all 382 tracked blobs from that exact
source revision and has SHA-256
`5a263a42ecced3384be9a8ab131024ce309e4eb96b249bad1f8adc91f065ce1d`.
`packaging/RELEASE_IDENTITY.json` binds source tree, source bundle, runtime
provenance and setup hashes. The #440 evidence artifact preserves the concrete
setup and source ZIP together with their manifests/identity record.

This closes the engineering requirement for an exact binary-to-source identity.
The GPL conveyance mechanism is now selected as section 6(d) network equivalent
access: binary and source are offered on the same public GitHub Release page at
no additional source charge. `v1.0.0.0` is reserved as the final tag, and
GitHub Immutable Releases is enabled so the published tag/assets become locked.
The project adds a 1095-day source-retention period after binary withdrawal in
addition to keeping source available for the full binary-download period.

This policy selection does not itself make the current private evidence public
and does not clear rightsholder, production-signing or clean-machine gates.

## Open public-distribution gates

Public binary redistribution remains not cleared. Current tracked engineering
evidence identifies these separate gates:

1. The root application license is GPLv3-or-later. The selected object-code
   conveyance path is GPLv3 section 6(d). Before publication, the designated
   GitHub Release surface must be public and provide the matching binary and
   deterministic source ZIP from the same release page without authentication
   or additional source charge.
2. The reserved tag `v1.0.0.0` must remain absent until the final draft has all
   signed binary/source/identity assets. Publishing under GitHub Immutable
   Releases must then lock the tag to the exact binary source revision and lock
   the assets. Release notes must carry direct source-access directions and
   hashes. Source retention is the full binary-availability period plus the
   project's 1095-day post-withdrawal minimum.
3. Rightsholder/contribution-grant authority still requires human confirmation.
   Git author metadata does not by itself establish copyright ownership,
   assignment, work-for-hire status or relicensing authority. See
   packaging/RIGHTSHOLDER_REVIEW.md.
4. Production signing remains open. The release path still requires signed
   payload/setup verification, regenerated final release identity and a
   clean-machine Program Files/HKLM install/update/rollback lifecycle check.

Tracked license, notice and provenance materials improve engineering evidence
but do not by themselves clear public redistribution.

Current source-of-truth details are maintained in
packaging/SOURCE_DISTRIBUTION.md, packaging/RIGHTSHOLDER_REVIEW.md,
packaging/SIGNING.md and packaging/README.md.

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.

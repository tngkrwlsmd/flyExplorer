# Distribution and license review — current release gate

This document records engineering evidence, not legal advice.

## 2026-10-22 F08 legacy ZIP source retirement (not release clearance)

After the separately accepted native Windows Explorer handoff (product
`1a5aece2df3fe9a6b548a511e949a62469d107d1`), the unused F08 archive
implementation and its pinned miniz 3.1.2 sources were removed from the
current source tree together with the nine ZIP-specific source-only tests.
No custom F08 codec remains in the active WinUI compile template. The
historical miniz version, original upstream
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

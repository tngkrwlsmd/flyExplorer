# Distribution and license review — current release gate

This document records engineering evidence, not legal advice.

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
It does not itself make source available to public recipients and therefore does
not clear GPLv3 section 6 delivery, retention/public-access, final release-tag,
rightsholder or signing gates.

## Open public-distribution gates

Public binary redistribution remains not cleared. Current tracked engineering
evidence identifies these separate gates:

1. The root application license is GPLv3-or-later. Object-code conveyance needs
   a GPLv3 section 6 compliant Corresponding Source delivery mechanism.
   The repository is private, so its normal clone access is not treated as
   public recipient source availability.
2. A current release needs an exact binary-to-source identity from the source
   actually packaged, plus clear source-access directions or another selected
   GPLv3 section 6 mechanism. A tracked GPL text alone does not establish
   Corresponding Source availability.
3. Rightsholder/contribution-grant authority still requires human confirmation.
   Git author metadata does not by itself establish copyright ownership,
   assignment, work-for-hire status or relicensing authority. See
   packaging/RIGHTSHOLDER_REVIEW.md.
4. Production signing remains open. The release path still requires signed
   payload/setup verification and a clean-machine Program Files/HKLM
   install/update/rollback lifecycle check.

Tracked license, notice and provenance materials improve engineering evidence
but do not by themselves clear public redistribution.

Current source-of-truth details are maintained in
packaging/SOURCE_DISTRIBUTION.md, packaging/RIGHTSHOLDER_REVIEW.md,
packaging/SIGNING.md and packaging/README.md.

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.

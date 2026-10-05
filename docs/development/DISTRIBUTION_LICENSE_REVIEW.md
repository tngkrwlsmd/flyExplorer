# Distribution and license review — current release gate

This document records engineering evidence, not legal advice.

## Current product

The canonical product is the WinUI 3 application in app/winui plus src/base.
Retired MFC dependency findings are no longer part of the current runtime
inventory unless a component is reintroduced.

Release uses a self-contained Windows App SDK payload and tracked distribution
materials under packaging/licenses/.

## Latest package evidence and current freshness

Remote Windows Task #382 (`37265695330`) clean-built candidate
`8283ece6c4348a751f487a64230e1bc149a47a2f`, generated and verified that
candidate's Release payload provenance, built the setup and passed bounded
`/TESTROOT` clean install, repair, update, rollback and uninstall. That
candidate was merged through PR #27.

The accepted run inventoried 305 runtime files, including 288 exact NuGet byte
matches, and packaged 326 files with the tracked license/notice material. It is
valid engineering evidence for that recorded candidate, but current main later
changed product code, including physical same-app drag and the active-pane
`Ctrl+Shift+N` create-folder shortcut. Therefore #382 is not exact
current-main package freshness or binary/source identity. Regenerate provenance,
build the package and rerun the required package acceptance before the next
current-product release claim.

The recorded #382 evidence is unsigned and does not certify production signing
or clean-machine machine-wide deployment.

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

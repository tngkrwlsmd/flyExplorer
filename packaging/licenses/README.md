# Release distribution license inputs

This directory contains notice/license inputs plus the last tracked payload
provenance snapshot.

PAYLOAD_PROVENANCE.md is the tracked 2026-10-05 snapshot generated from
Release runtime source revision
`067122c8e9b45d56c4fa8dde75fef9c2ef86f44f`. It records 305 runtime files
before distribution materials and belongs to the package lifecycle later
accepted through Remote Windows Task #382 / PR #27. Current main contains later
product changes, so this snapshot is historical evidence rather than provenance
for a current-main binary. Regenerate the provenance audit from the final
Release runtime before the next release claim.

The directory also retains:
- GPL-3.0.txt, the full GNU GPL version 3 text;
- NuGet license/NOTICE/ThirdPartyNotices material for packages represented in
  the tracked packaged snapshot;
- top-level Windows App SDK terms used by that package.

The installer also adds root LICENSE and CREDITS to its licenses directory.
Notice delivery and provenance evidence do not by themselves clear public
redistribution.

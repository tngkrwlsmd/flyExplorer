# Release distribution license inputs

This directory contains notice/license inputs plus the last tracked payload
provenance snapshot.

PAYLOAD_PROVENANCE.md currently describes the 2026-10-01 packaged runtime.
That snapshot predates v7 and is historical evidence, not provenance for the
current product binary. Regenerate the provenance audit when packaging the
current Release runtime.

The directory also retains:
- GPL-3.0.txt, the full GNU GPL version 3 text;
- NuGet license/NOTICE/ThirdPartyNotices material for packages represented in
  the tracked packaged snapshot;
- top-level Windows App SDK terms used by that package.

The installer also adds root LICENSE and CREDITS to its licenses directory.
Notice delivery and provenance evidence do not by themselves clear public
redistribution.

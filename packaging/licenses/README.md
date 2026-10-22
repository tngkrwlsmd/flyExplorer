# Private-use installer dependency notices and payload provenance

This directory contains notice/license inputs plus the last tracked payload
provenance snapshot.

PAYLOAD_PROVENANCE.md and PAYLOAD_PROVENANCE.json are the tracked snapshot
for the exact clean Release runtime used by the accepted package candidate.
They record the runtime source revision, per-file SHA-256 inventory, package
origins and the aggregate runtime manifest SHA-256. A fresh Release rebuild is
a new byte set for provenance purposes: regenerate the snapshot with
`packaging/provenance.py --write`, immediately verify it with `--check`, and
package that same runtime rather than expecting an older snapshot to match a
later rebuild.

The directory contains the dependency licenses and NOTICE materials for the
NuGet packages represented in the tracked runtime inventory, including the
Windows App SDK. The installer additionally carries the active asset notice
from CREDITS.
This installer is maintained for private personal use; public publication and
redistribution gates are inactive. Actual active dependency licenses remain.

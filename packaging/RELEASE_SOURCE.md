# flyExplorer release source bundle and binary/source identity

This document defines the technical release-source identity path. It is
engineering evidence, not legal advice and not public-distribution clearance.

## Identity model

A release identity binds one concrete setup artifact to the exact source and
runtime evidence that produced it:

- **binary source revision** — the Git commit used for the clean Release build;
- **source tree SHA** — the Git tree for that exact source revision;
- **source bundle SHA-256** — a deterministic ZIP containing every tracked blob
  from that source revision;
- **source manifest SHA-256** — the per-file path/mode/Git-object/SHA-256
  inventory for the source bundle;
- **runtime manifest SHA-256** — the exact-build runtime provenance digest;
- **setup SHA-256** — the actual unsigned or signed setup artifact bytes.

\`packaging/RELEASE_IDENTITY.json\` records these links after an accepted package
run. The source bundle itself is generated under ignored \`out/release/\` and is
not committed.

A fresh Release rebuild creates a new runtime byte set and therefore requires a
new provenance snapshot and release identity. Never reuse an older runtime
digest or setup hash merely because the source revision is unchanged.

## Generate and verify the source bundle

From the exact source revision used for the Release build:

    python -X utf8 packaging/source_bundle.py --write --revision HEAD
    python -X utf8 packaging/source_bundle.py --check --revision HEAD

The generator reads blobs directly from the Git object database rather than the
working-tree text representation. The ZIP uses stored entries, a fixed
timestamp and stable path order. It fails closed on symbolic links, unsupported
Git modes, unsafe paths, Unicode/case-fold collisions, excessive entry counts,
oversized files and excessive total source size.

The sidecar source manifest records every tracked path, Git object ID, mode,
size and SHA-256 plus the archive SHA-256 and source tree SHA.

## Bind source to the built setup

After \`packaging/provenance.py --write\`, \`--check\` and \`package.bat Release\`
have consumed the same clean Release runtime:

    python -X utf8 packaging/release_identity.py --write ^
      --source-bundle out/release/flyExplorer-source-<revision>.zip ^
      --source-manifest out/release/flyExplorer-source-<revision>.manifest.json ^
      --setup out/package/flyExplorer-Setup-x64.exe ^
      --identity out/release/RELEASE_IDENTITY.json

    python -X utf8 packaging/release_identity.py --check ^
      --source-bundle out/release/flyExplorer-source-<revision>.zip ^
      --source-manifest out/release/flyExplorer-source-<revision>.manifest.json ^
      --setup out/package/flyExplorer-Setup-x64.exe ^
      --identity out/release/RELEASE_IDENTITY.json

The identity writer refuses to bind a source bundle whose revision differs from
\`PAYLOAD_PROVENANCE.json\`'s \`runtime_source_revision\`.

For an accepted release candidate, preserve together the exact setup artifact,
deterministic source ZIP, source manifest, release identity JSON and
package/runtime provenance evidence.

Tracked \`packaging/RELEASE_IDENTITY.json\` and
\`packaging/SOURCE_BUNDLE_MANIFEST.json\` are audit records. The actual setup and
source ZIP remain release artifacts.

## Git reachability and release tags

The binary source revision must remain durably recoverable. During development
it must remain in \`main\` history (for example through a merge that preserves
the source commit) or behind another durable ref. Before a public release,
create the final approved immutable release tag and record that concrete tag in
a newly generated release identity.

Do not move a published release tag to a different source revision.

## Public source delivery remains a separate gate

A private Actions artifact proves the engineering path but does not make source
available to public binary recipients. Public release still requires the
selected GPLv3 section 6 source-delivery mechanism, public source-access
directions, required retention/availability, rightsholder confirmation and any
other release/legal approvals.

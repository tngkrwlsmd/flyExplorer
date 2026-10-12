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

## Git reachability and immutable release tag

The binary source revision must remain durably recoverable. During
development it remains in `main` history. The reserved public tag
`v1.0.0.0` matches product version 1.0.0.0, but has **not been created**.
The older private artifact's source
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60` is only historical.
The final tag target must be selected from the **exact final retained
signed-binary source revision**, not automatically reusing that
historical commit or the ephemeral private audit's revision.

Do **not** pre-create that tag. The current private-repository GitHub plan does
not provide repository tag rulesets, so a pre-created tag would remain movable.
GitHub Immutable Releases is enabled for this repository. The release workflow
is therefore: create a draft release targeting the exact binary source
revision, attach every final signed binary/source/identity asset, verify hashes
and public-access prerequisites, then publish the draft once. Published
immutable releases lock their associated tag and assets.

After publication, `RELEASE_IDENTITY.json` for the final signed setup must
record `release_tag: "v1.0.0.0"`, and the tag must resolve to the exact binary
source revision. Never delete/move/reuse a published release tag.

## Selected public source delivery

The selected GPL method is **GPLv3 section 6(d)** network equivalent access.
The matching object code and deterministic Corresponding Source ZIP are offered
from the same public GitHub Release page with no authentication requirement and
no additional source charge. Release notes must point directly to the source
asset and publish the setup/source/identity hashes.

The source must remain available for the entire time the matching binary is
publicly downloadable. In addition, flyExplorer adopts a project retention
minimum of 1095 days after the binary is withdrawn. That three-year
post-withdrawal period is a project policy; section 6(d) itself does not specify
a fixed three-year term.

The private repository is not yet a public delivery surface. Publication
therefore remains blocked until the designated release page is publicly
accessible, the final signed artifact identity is regenerated, and the
rightsholder/signing/clean-machine gates are cleared.

## Current pre-distribution technical audit (not a final release)

[Windows audit 38210591849](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38210591849)
clean-built the exact private source
`2a736d85b22859a770138e4b50926ac125d1a052`, verified unsigned
setup/runtime/source-bundle identity, and removed the generated files
as test-owned scratch after recording SHA-256 evidence in the run log.
This demonstrates the current source can be bound to a matching private
installer; it does **not** supersede the older *retained* #440 artifact
or authorize publication. Fresh final assets must be generated,
preserved, reviewed, signed if required, and verified once more.

## Current accepted private evidence

Remote Windows Task #440 (`37376305779`) accepted binary source revision
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60` with source tree
`8f1bc2e0181cc87e646dd2fad75ccdca0c8e8a66`.

- source bundle: 382 tracked files, 3,942,910 source bytes,
  SHA-256 `5a263a42ecced3384be9a8ab131024ce309e4eb96b249bad1f8adc91f065ce1d`;
- source manifest SHA-256:
  `4f96cb8b81414f3f64b6f5b2fa4c6a7ef1328e85de0bca0a93232bfa5f10a771`;
- runtime manifest SHA-256:
  `61572e65c4a593e01607147596195041ce9d530e5f9fc21c9f9517f615b26c1d`;
- unsigned setup: 124,107,776 bytes,
  SHA-256 `825a644a8170acdaae43135604d6998ce517f882b3f8f228fa54cb30c1298a91`.

The private Actions artifact `flyexplorer-remote-evidence-37376305779`
preserves the concrete setup, source ZIP, source manifest, runtime provenance
and release identity together. It is retained as engineering evidence only; it
is not a public GPL source-delivery endpoint.

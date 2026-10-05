# flyExplorer GPL source-distribution readiness

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.

The root LICENSE states GPLv3-or-later. A distributed setup conveys object code
but does not by itself provide Corresponding Source or a public source-access
direction. The repository is currently private, so its normal clone URL is not
treated as public recipient access.

Remote Windows Task #440 (`37376305779`) establishes the current technical
exact binary/source identity for binary source revision
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60`. The accepted private evidence
contains the concrete unsigned setup, deterministic exact-revision source ZIP,
source manifest, runtime provenance and `RELEASE_IDENTITY.json` together.
The source ZIP SHA-256 is
`5a263a42ecced3384be9a8ab131024ce309e4eb96b249bad1f8adc91f065ce1d`;
the setup SHA-256 is
`825a644a8170acdaae43135604d6998ce517f882b3f8f228fa54cb30c1298a91`.

This closes the engineering identity question but does not provide source to
public binary recipients. Before publicly conveying an installer, establish the
final immutable release tag and choose/implement a GPLv3 section 6 compliant
Corresponding Source delivery method with public source-access directions and
the required retention/availability.

A release record should include:
- exact Git commit/release tag corresponding to the binary;
- public source location or selected alternative section 6 mechanism;
- source archive/hash if an archive is published;
- build/package scripts and tracked license/notice materials;
- clear source-access directions placed with the binary download;
- retention/availability evidence required by the selected method.

Including GPL-3.0.txt alone does not establish source availability compliance.
Rightsholder/license compatibility remains a separate open gate.

The repository now has a technical source-identity path in
`packaging/RELEASE_SOURCE.md`: a deterministic exact-revision source ZIP and
per-file manifest are bound to runtime provenance and the concrete setup
SHA-256 by `packaging/release_identity.py`. Private validation of that path
does not by itself satisfy public recipient source availability.

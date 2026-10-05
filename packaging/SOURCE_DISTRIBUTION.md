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

This closes the engineering identity question. The public conveyance method is
now fixed to **GPLv3 section 6(d)** network distribution: the public object-code
download and the Corresponding Source download must be offered on the same
public GitHub Release page, in the same way and with no additional source
charge. The private repository and private Actions artifact are not public
source-access endpoints.

The reserved final tag name is `v1.0.0.0`, matching the product version.
Because this private repository cannot use tag rulesets on its current GitHub
plan, that tag must **not** be pre-created while it would remain mutable.
Repository-level GitHub Immutable Releases was enabled in Remote Windows Task
#446 (`37379026246`). The final release must be assembled as a draft with all
signed binary/source/identity assets, then published once. Publication creates
or adopts `v1.0.0.0` at the exact binary source revision and locks the
published tag/assets under GitHub release immutability.

Project retention policy is stronger than the fixed text of section 6(d):
Corresponding Source stays available for the full period that the matching
binary is publicly downloadable and for at least **1095 days (3 years)** after
the last public availability of that binary. GPLv3 section 6(d) itself does not
state a fixed three-year term; the explicit three-year written-offer minimum is
in section 6(b). The 1095-day period here is therefore an additional project
retention commitment, not a description of section 6(d)'s wording.

The selected release record must include:
- immutable GitHub Release tag `v1.0.0.0` resolving to the exact binary source
  revision;
- signed setup and deterministic source ZIP on the same public release page;
- source manifest, `RELEASE_IDENTITY.json` and runtime provenance assets;
- build/package scripts and tracked license/notice materials inside the exact
  source bundle;
- adjacent release-note directions identifying the source asset and its
  SHA-256;
- no authentication requirement and no additional charge for source access;
- retention evidence proving source availability while the binary is offered
  plus the 1095-day project post-withdrawal period.

The machine-readable policy is `packaging/PUBLIC_SOURCE_DELIVERY.json` and is
checked by `packaging/public_source_delivery.py`.

Including GPL-3.0.txt alone does not establish source availability compliance.
Rightsholder/license compatibility remains a separate open gate.

The repository now has a technical source-identity path in
`packaging/RELEASE_SOURCE.md`: a deterministic exact-revision source ZIP and
per-file manifest are bound to runtime provenance and the concrete setup
SHA-256 by `packaging/release_identity.py`. Private validation of that path
does not by itself satisfy public recipient source availability.

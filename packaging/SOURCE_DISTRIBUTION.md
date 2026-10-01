# flyExplorer GPL source-distribution readiness

Status: **OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION**.

The application root `LICENSE` states GPLv3-or-later. The current setup conveys
object code but does not include Corresponding Source and does not install a
written source offer or public source-access direction. The connected GitHub
repository `tngkrwlsmd/flyExplorer` is currently private, so its normal clone
URL is not equivalent public access for installer recipients.

## GPLv3 section 6 engineering gate

Before publicly conveying the installer, choose and implement one GPLv3 section
6-compliant Corresponding Source delivery method. The current M2.7 checkpoint is
still staged and uncommitted, so there is not yet an exact release commit/tag
that can serve as the durable binary-to-source identity. Create that release
identity only when the owner explicitly authorizes commit/tag publication. For an online installer
download workflow, the operationally direct candidate is section 6(d): provide
equivalent no-extra-charge access to the Corresponding Source and keep clear
source-location directions next to the object-code download. Other section 6
methods may be used if intentionally selected and satisfied.

Do not treat inclusion of `GPL-3.0.txt` alone as fulfillment of the source
availability requirement.

## Corresponding Source release bundle

The release source publication should be reproducible from the exact release
checkpoint and include the source and scripts needed to build/install the GPL
covered application, subject to GPLv3's Corresponding Source definition. Before
publishing, record:

- exact Git commit/release tag corresponding to the binary;
- public source location or selected alternative section 6 mechanism;
- source archive/hash if an archive is published;
- build/package scripts and tracked license/notice materials;
- clear source-access directions placed with the binary download;
- availability/retention policy required by the selected GPLv3 method.

This document is an engineering release gate, not a legal opinion. Final
rightsholder/license-compatibility review remains separate.

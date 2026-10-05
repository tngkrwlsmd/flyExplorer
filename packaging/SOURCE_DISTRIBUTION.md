# flyExplorer GPL source-distribution readiness

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.

The root LICENSE states GPLv3-or-later. The tracked setup conveys object code
but does not itself provide Corresponding Source or a public source-access
direction. The repository is currently private, so its normal clone URL is not
treated as public recipient access.

The current unsigned packaging path is accepted through Remote Windows Task
#382 and PR #27, but that engineering acceptance does not provide Corresponding
Source to public binary recipients. Before publicly conveying an installer,
create an exact binary-to-source release identity from the source actually
packaged and choose/implement a GPLv3 section 6 compliant Corresponding Source
delivery method.

A release record should include:
- exact Git commit/release tag corresponding to the binary;
- public source location or selected alternative section 6 mechanism;
- source archive/hash if an archive is published;
- build/package scripts and tracked license/notice materials;
- clear source-access directions placed with the binary download;
- retention/availability evidence required by the selected method.

Including GPL-3.0.txt alone does not establish source availability compliance.
Rightsholder/license compatibility remains a separate open gate.

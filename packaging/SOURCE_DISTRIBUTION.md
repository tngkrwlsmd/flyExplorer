# flyExplorer GPL source-distribution readiness

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.

The root LICENSE states GPLv3-or-later. A distributed setup conveys object code
but does not by itself provide Corresponding Source or a public source-access
direction. The repository is currently private, so its normal clone URL is not
treated as public recipient access.

The latest unsigned packaging lifecycle acceptance is Remote Windows Task #382
and PR #27 for candidate `8283ece6c4348a751f487a64230e1bc149a47a2f`.
Current main contains later product changes, so that evidence does not establish
an exact current-main binary-to-source identity. It also does not provide
Corresponding Source to public binary recipients. Before publicly conveying an
installer, regenerate the final package from the release source, record the
exact binary-to-source identity and choose/implement a GPLv3 section 6 compliant
Corresponding Source delivery method.

A release record should include:
- exact Git commit/release tag corresponding to the binary;
- public source location or selected alternative section 6 mechanism;
- source archive/hash if an archive is published;
- build/package scripts and tracked license/notice materials;
- clear source-access directions placed with the binary download;
- retention/availability evidence required by the selected method.

Including GPL-3.0.txt alone does not establish source availability compliance.
Rightsholder/license compatibility remains a separate open gate.

# flyExplorer GPL source-distribution readiness

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.

The root LICENSE states GPLv3-or-later. A distributed setup conveys object code
but does not by itself provide Corresponding Source or a public source-access
direction. The repository is currently private, so its normal clone URL is not
treated as public recipient access.

The latest unsigned packaging lifecycle acceptance is Remote Windows Task #435
(`37306799266`) for package candidate
`00f90c30800fb66f88184211442f6eeb05a950b7`. The package embeds provenance
for the exact clean Release runtime built during that acceptance, but this
engineering evidence does not itself provide Corresponding Source to public
binary recipients. Before publicly conveying an installer, establish the final
release tag/commit and exact binary-to-source release identity, then
choose/implement a GPLv3 section 6 compliant Corresponding Source delivery
method.

A release record should include:
- exact Git commit/release tag corresponding to the binary;
- public source location or selected alternative section 6 mechanism;
- source archive/hash if an archive is published;
- build/package scripts and tracked license/notice materials;
- clear source-access directions placed with the binary download;
- retention/availability evidence required by the selected method.

Including GPL-3.0.txt alone does not establish source availability compliance.
Rightsholder/license compatibility remains a separate open gate.

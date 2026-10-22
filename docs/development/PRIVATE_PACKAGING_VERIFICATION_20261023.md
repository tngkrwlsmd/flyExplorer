# Private installer license-input checkpoint — 2026-10-23

## Current fact check

- At flyExplorer main `8d49d84572ced01b2cbb7d93eb2df47f9b5bc022`, the root
  `LICENSE` and standalone `packaging/licenses/GPL-3.0.txt` are absent.
- `src/base/shell_navigation_core.h` and `src/base/directory_change_bridge.h`
  no longer contain the old project-level GPL header comment.
- `packaging/package.py` no longer stages `licenses/flyExplorer-LICENSE.txt`.
  `packaging/provenance.py` records active NuGet dependency notices and
  the Fluent icon credit from `CREDITS` instead.
- Active NuGet `license.txt`, `LICENSE.txt`, `NOTICE.txt` and
  `ThirdPartyNotices.txt` remain in `packaging/licenses/nuget/**`.
  The separate `.agent-policy/LICENSE` is the vendored agent-policy license.

## Focused verification (no product rebuild)

- Windows direct-run evidence:
  https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39861607284
- Exact source SHA: `8d49d84572ced01b2cbb7d93eb2df47f9b5bc022`.
- Five methods in `tests/winui/test_release_payload_contract.py` passed:
  required product payload, tracked NuGet notice inventory, provenance
  synthetic hashes/notice requirements, generated payload manifest, and
  runtime-source exclusion. The bounded exact-SHA scratch clone was retired.
- This is not a package build, installation/uninstallation lifecycle, binary
  run, GUI test or acceptance of the unbuilt latest source.

## Historical snapshot clarification

- `packaging/licenses/PAYLOAD_PROVENANCE.json` and `.md` are snapshots of an
  older `2026-10-06` Release runtime/source, not current packaged artifacts.
- The stale notice-policy paragraphs in `packaging/licenses/README.md`
  and the generated Markdown snapshot were corrected on 2026-10-23. The
  generated Markdown now matches `packaging/provenance.py` applied to the
  checked-in `PAYLOAD_PROVENANCE.json` exactly (4,656 characters).
- The snapshot still describes the older 2026-10-06 binary, not the latest
  private-use application binary. A fresh package must regenerate both
  provenance snapshots against the exact newly built Release runtime before
  its `--check` gate; this document-only repair does not certify that build.
- Distinct actual dependency/asset notices remain valid. Removing a tracked
  notice file does not itself change rights applicable to retained source.


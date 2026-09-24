# Dependency and Mixed-Architecture Audit — 2026-09-24

## Scope and evidence level

This audit records repository-observed dependency and architecture facts for the current VS 2026/v145 build. It does not treat age alone as permission to upgrade or delete a dependency.

- Observed sources: root/component GYP files, `copy_lib.bat`, package validators, direct source includes/call sites, `CREDITS`, and the current repository tree.
- Runtime ABI inspection of bundled DLLs: NOT TESTED.
- Fresh Windows Release-x64-Unicode build: NOT TESTED.
- External CVE/vendor-support verification: NOT VERIFIED in this work unit.

## Mixed architecture

| Component | Current observed role | Current architecture contract | Assessment |
| --- | --- | --- | --- |
| `fxfile` | Main MFC file manager | x64 for active Release-x64-Unicode; x86 configs retained | Keep current x64 active path |
| `xpr` | Shared runtime/XML/charset layer | x64 active plus x86 retained | Keep; bundled libxml2/iconv ABI is a migration blocker |
| `fxfile-crash` | Crash/reporting support | native x64 active; vendored zlib source builds per architecture | Keep |
| `fxfile-keyhook` | Keyboard hook helper | Win32 helper mapped/staged for x64 product | Keep until hook/consumer bitness contract is proven replaceable |
| `fxfile-launcher` | Launch helper | Win32 helper mapped/staged for x64 product | Candidate for isolated x64 feasibility study; no migration performed |
| `fxfile-upchecker` | Updater checker | x86 Multibyte helper, separately staged under x64/upchecker | Highest-value architecture simplification candidate, but blocked by prebuilt libcurl/libxml2/iconv/mingw runtime and updater compatibility |
| `fxfile-tests` | Native functional regression | x64 active with x86 configs retained | Keep aligned with product architecture |

Current conclusion: mixed architecture is intentional and still has real ABI/runtime packaging dependencies. Converting all helpers to x64 in one step would be unjustified.

### Migration sequence

1. Record PE/import/runtime dependencies of each Win32 helper on a Windows build.
2. Separate architecture-neutral command/version/config logic from helper UI/process shells where not already separated.
3. Prove one helper, preferably launcher, builds and behaves equivalently as x64 without changing packaging contracts.
4. Treat upchecker separately because its prebuilt network/XML runtime is the strongest x86/Multibyte coupling.
5. Change the default release matrix only after functional and installer/package equivalence is demonstrated.

## Vendored dependency inventory

| Dependency | Repository evidence | Build/runtime status | Risk / next action |
| --- | --- | --- | --- |
| GFL SDK | `fxfile.gyp` links `libgfl.lib`; thumbnail/picture viewer/conversion call sites; x86/x64 prebuilt DLL trees | Active, prebuilt, architecture-specific | Keep. Major ABI and redistribution/licensing dependency; do not replace casually. Review license before any distribution-scope change. |
| libxml2 | `xpr.gyp` includes/links `libxml2.dll.a`; package copies `libxml2-2.dll` for x86/x64 | Active, prebuilt runtime | Keep. Candidate for a future independently pinned upgrade after XML regression coverage and ABI check. |
| libiconv | XPR charset conversion includes `iconv.h`, lazy-loads `libiconv-2.dll`; package stages x86/x64 DLLs | Active runtime | Keep while current charset/XML path remains. |
| libcurl | upchecker includes and links `libcurl.lib`; package stages `libcurl.dll` in updater payload | Active, updater-only, prebuilt | Keep until updater architecture/runtime migration. Isolate upgrade from UI work. |
| zlib | `fxfile-crash.gyp` builds vendored zlib source; libxml2 runtime also stages `zlib1.dll` | Active in two forms | Keep. Document/version-align later; avoid assuming the source-built crash copy and runtime DLL are interchangeable. |
| MinGW runtime | `copy_lib.bat` stages `libgcc_s_sjlj-1.dll`/`libwinpthread-1.dll`; package validation expects them | Active transitive runtime for bundled GNU-built libraries | Keep until dependent prebuilt binaries are replaced or rebuilt with a different toolchain. |
| Visual Leak Detector | Debug include is conditional on `FXFILE_CHECK_MEMORY_LEAK`; GYP has VLD library paths; copy script stages binaries | Development/debug dependency, not core product logic | Candidate to stop staging in release only after verifying current packaging expectations; no removal yet. |
| Google Test | Repository tree/CREDITS contain vendored headers; no project GYP or production source consumer was found in current code search | No active build reference observed | Removal candidate only after confirming no external/manual tooling consumes it. Do not delete from this audit alone. |
| libxslt | Vendored tree/CREDITS present; no flyExplorer GYP or source consumer was found in current code search | No active build reference observed | Strong removal candidate for a dedicated cleanup unit after packaging/license/reference verification. |

## Highest-value technical-debt order

1. **Unused-tree confirmation:** prove `libxslt` and `gtest` have no build, package, script, dynamic-load, or external documented consumer; remove only in a dedicated reversible change.
2. **Updater runtime isolation:** document exact PE imports and runtime DLL provenance for `fxfile-upchecker`; this is prerequisite to x64/Unicode migration.
3. **GFL containment:** keep current behavior but isolate image-format calls behind existing image/thumbnail boundaries so a future replacement does not spread through UI code.
4. **Runtime provenance:** record versions/architectures/checksums or reproducible source origins for prebuilt libxml2/iconv/libcurl/GFL/MinGW artifacts.
5. **VLD release staging:** verify whether Release packaging needs VLD at all; if not, remove release staging without touching debug leak-detection support.

## Explicit non-actions

- No third-party directory was deleted.
- No bundled library was upgraded.
- No helper architecture was changed.
- No release/package matrix was expanded.
- No license claim beyond repository-observed `CREDITS`/bundled metadata is treated as legal advice.

## Verification status

- Repository tree/GYP/source/package reference audit: PASS (connector/source evidence).
- Binary dependency/PE import audit: NOT TESTED.
- Release-x64-Unicode compile/link: NOT TESTED.
- x86 compatibility/package/installer: NOT TESTED by policy.

## Post-audit verification note (2026-09-24; historical audit results retained)

A later local `local_ci.bat x64` run for the `6b18c58f` OS-classification
fix used its parent revision plus then-uncommitted source changes. The
recorded result was Release-x64-Unicode compile/link PASS, native functional
regression 17 passed / 0 failed, overall PASS WITH SKIPS because existing
HKCU state prevented launch smoke. Post-fix interactive visual evidence
remains NOT TESTED. This result does not retroactively change the build
evidence available at the time of this dependency audit, nor validate
third-party binary PE imports/ABI, x86 compatibility, packages or installers.
See `docs/development/ERROR_HISTORY.md` for the precise record.

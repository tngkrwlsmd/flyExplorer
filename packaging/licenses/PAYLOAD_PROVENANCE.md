# Current packaged payload provenance snapshot — 2026-10-05

This snapshot is generated from the exact canonical Release runtime before
distribution materials are added to the installer. Runtime bytes are matched
by SHA-256 against package versions in the build's project.assets.json and
the repository-local NuGet cache.

- Runtime source revision: `a84ff56597ca638b31fdcb4a5b0bc1356cb443f3`
- Runtime files before distribution materials: **305**
- Product/generated files with no NuGet byte match: **17**
- Files with an exact NuGet package byte match: **288**
- Runtime manifest SHA-256: `8ffbde6a94840cae874a761e6a26148616f167fb0db1fedb3939aa2f18968856`

## Exact NuGet payload matches

- `microsoft.web.webview2 1.0.3719.77`: 2 files
- `microsoft.windows.ai.machinelearning 2.1.74`: 3 files
- `microsoft.windowsappsdk.ai 2.5.5`: 47 files
- `microsoft.windowsappsdk.dwrite 2.1.0`: 1 files
- `microsoft.windowsappsdk.foundation 2.3.12`: 27 files
- `microsoft.windowsappsdk.interactiveexperiences 2.1.9`: 20 files
- `microsoft.windowsappsdk.search 2.5.5`: 2 files
- `microsoft.windowsappsdk.widgets 2.0.5`: 2 files
- `microsoft.windowsappsdk.winui 2.3.9`: 184 files

## Product/generated files

- `App.xbf` — 1963 bytes — `sha256:b3be7467102b933fa4f21735a3779356eafb96fc31e99a56da39ca0f41a1c9b6`
- `Assets/LockScreenLogo.scale-200.png` — 432 bytes — `sha256:688f384ef8832609d1f4d5e7fa9f6e08a81a6f52bba2c67070e385a015dfb42b`
- `Assets/SplashScreen.scale-200.png` — 5372 bytes — `sha256:209a614557ff28be5a307c55ec17e2126f1ad34f54a88c5d4226441891c5892f`
- `Assets/Square150x150Logo.scale-200.png` — 1755 bytes — `sha256:0b2ecc4b0e160157f55e43d1cd9532751cfa265be816227681c633b9c69a9381`
- `Assets/Square44x44Logo.scale-200.png` — 637 bytes — `sha256:0be34ccbed90a09a51d56abc1b9ab279154d454e43906057b45762ba00b38854`
- `Assets/Square44x44Logo.targetsize-24_altform-unplated.png` — 283 bytes — `sha256:7799103c81a408b8dfc465764a5a8e693ebe1048a2e0f4690ae467398390030a`
- `Assets/StoreLogo.png` — 456 bytes — `sha256:5a44b2f15b76ff4cfcb315e8b62b2ac1e4a1f616bbfee0b8be29f9e2e116172c`
- `Assets/Wide310x150Logo.scale-200.png` — 2097 bytes — `sha256:4938ed44d7d63f44ca959eafb942be36459939a9c679bfcbf4f5c837fdf3475c`
- `FileToolbar.xbf` — 4993 bytes — `sha256:6fb066df97fceda4397c370768a6bae1a2e980cf3be72f4238af05ec0ce89374`
- `flyExplorer.exe` — 1806336 bytes — `sha256:ba7ba0d20a0384ab75ab6d1a542a68d3f8df1ae3221d4480e9270cf9c6229fd5`
- `flyExplorer.pri` — 2221824 bytes — `sha256:57918bd72c8a10486bc61f40e4eb2e0e9d003a3456dfc9215b73d9de4c0158fc`
- `FlyExplorer.winmd` — 3584 bytes — `sha256:826e69f1aac81fcae62a1f65baff3a75d3d907a11c94ba7cb64ad39475d80e46`
- `FlyShellIsolationHelper.exe` — 184320 bytes — `sha256:19aa8bbfbf07ec6af034ede60424cb2579f7a75d70983f1d05058f274ced9c2d`
- `MainWindow.xbf` — 19323 bytes — `sha256:c0683a2755cd79a44c266a7102a7ff77e3b8a5c2ee64fbf1056d02b3de88c608`
- `NavigationSidebar.xbf` — 4015 bytes — `sha256:f2c289b8787e8c1a1f2e0b0f676a9d984768be0a867891e5ae04daa030c362b6`
- `ShellHeader.xbf` — 2014 bytes — `sha256:1c1557c62a13345b457fc62112892ca75a0f9e4b71ba9b60c806ac3ee8a5f6c3`
- `StatusFooter.xbf` — 1175 bytes — `sha256:f54a46a7ab23a015203adabb403c6323e315acf8b496ad76d2fe63351cf77624`

## Tracked redistribution notices

- `microsoft.web.webview2 1.0.3719.77`: `LICENSE.txt`, `NOTICE.txt`
- `microsoft.windows.ai.machinelearning 2.1.74`: `ThirdPartyNotices.txt`, `license.txt`
- `microsoft.windowsappsdk 2.5.1`: `NOTICE.txt`, `license.txt`
- `microsoft.windowsappsdk.ai 2.5.5`: `license.txt`
- `microsoft.windowsappsdk.dwrite 2.1.0`: `license.txt`
- `microsoft.windowsappsdk.foundation 2.3.12`: `license.txt`
- `microsoft.windowsappsdk.interactiveexperiences 2.1.9`: `license.txt`
- `microsoft.windowsappsdk.search 2.5.5`: `license.txt`
- `microsoft.windowsappsdk.widgets 2.0.5`: `license.txt`
- `microsoft.windowsappsdk.winui 2.3.9`: `NOTICE.txt`, `license.txt`, `tools/NOTICE.txt`

## Distribution-material policy

- The installer additionally carries the repository root `LICENSE` and `CREDITS`.
- `packaging/licenses/GPL-3.0.txt` is the full GPLv3 text.
- `packaging/licenses/nuget/` must contain notice/license material for every
  package version identified above, plus the top-level Microsoft.WindowsAppSDK
  package terms from the active restore graph.
- `PAYLOAD_PROVENANCE.json` is the machine-readable per-file SHA-256 inventory
  corresponding to this summary.
- Direct build-only PackageReferences whose bytes do not appear in the Release
  runtime are not classified as redistributed runtime components by this audit.

Any runtime byte set, restored package origin, or tracked notice change makes
this snapshot stale and must fail packaging until the audit is regenerated.

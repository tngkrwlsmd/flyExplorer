# Historical packaged payload provenance snapshot - 2026-10-01 (predates v7)

This snapshot describes the exact WinUI Release runtime used for the 2026-10-01 installer. It predates the v7 Window Tab/session checkpoint and is not provenance for the current product binary. Hash matching was performed against the repository-local NuGet cache after that Release restore/build. Preserve it as historical package evidence and regenerate the audit before packaging the current product.

- Runtime files before distribution materials: **305**
- flyExplorer/generated files with no NuGet hash match: **17**
- files with an exact NuGet package hash match: **288**

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

- `App.xbf`
- `Assets/LockScreenLogo.scale-200.png`
- `Assets/SplashScreen.scale-200.png`
- `Assets/Square150x150Logo.scale-200.png`
- `Assets/Square44x44Logo.scale-200.png`
- `Assets/Square44x44Logo.targetsize-24_altform-unplated.png`
- `Assets/StoreLogo.png`
- `Assets/Wide310x150Logo.scale-200.png`
- `FileToolbar.xbf`
- `flyExplorer.exe`
- `flyExplorer.pri`
- `FlyExplorer.winmd`
- `FlyShellIsolationHelper.exe`
- `MainWindow.xbf`
- `NavigationSidebar.xbf`
- `ShellHeader.xbf`
- `StatusFooter.xbf`

## Distribution-material policy

- The installer additionally carries the repository root `LICENSE` and `CREDITS`.
- `packaging/licenses/GPL-3.0.txt` is the full GPLv3 text fetched from GNU/FSF.
- `packaging/licenses/nuget/` retains every license/NOTICE/ThirdPartyNotices file found in the NuGet package/version sets that contributed hash-matched runtime files, plus the top-level `Microsoft.WindowsAppSDK 2.5.1` package terms.
- Direct build-only PackageReferences whose files do not appear in the installer payload are not treated as redistributed runtime components by this snapshot.

Any dependency version, runtime file set, or package provenance change requires regenerating this audit before public release.

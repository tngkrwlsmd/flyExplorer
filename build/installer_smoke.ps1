param(
    [string]$DistDir = "dist",
    [switch]$ExecuteInstall
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-File {
    param([string]$Path, [string]$Description)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Description is missing: $Path"
    }
    if ((Get-Item -LiteralPath $Path).Length -le 0) {
        throw "$Description is empty: $Path"
    }
}

function Get-RegSnapshot {
    param([string[]]$Arguments)

    $output = & reg.exe @Arguments 2>&1 | Out-String
    return ($LASTEXITCODE.ToString() + [Environment]::NewLine + $output)
}

function Assert-SnapshotUnchanged {
    param([hashtable]$Before, [hashtable]$After)

    foreach ($key in $Before.Keys) {
        if ($Before[$key] -ne $After[$key]) {
            throw "Installer smoke changed protected Registry state: $key"
        }
    }
}

$dist = (Resolve-Path -LiteralPath $DistDir).Path
$installer = Join-Path $dist "fxfile_v2.0.4-dev.exe"
$setupPath = Join-Path $dist "setup.nsi"

Assert-File $installer "NSIS installer"
Assert-File $setupPath "NSIS source"

$setup = Get-Content -LiteralPath $setupPath -Raw
foreach ($token in @(
    'Var SMOKE_MODE',
    '/FXFILE_SMOKE=',
    'StrCmp $SMOKE_MODE "1" SkipInstallProcessKill',
    'StrCmp $SMOKE_MODE "1" CreateUninstaller',
    'StrCmp $SMOKE_MODE "1" DesktopShortcutDone',
    'StrCmp $SMOKE_MODE "1" QuickLaunchShortcutDone',
    'StrCmp $SMOKE_MODE "1" OnInstSuccessDone',
    'StrCmp $SMOKE_MODE "1" unSkipProcessKill',
    'StrCmp $SMOKE_MODE "1" unSmokeCleanup'
)) {
    if (-not $setup.Contains($token)) {
        throw "setup.nsi is missing isolated installer-smoke contract: $token"
    }
}

Write-Host "Installer smoke contract inspection PASS."

if (-not $ExecuteInstall) {
    Write-Host "Installer install/uninstall execution SKIPPED."
    Write-Host "Set FXFILE_INSTALLER_SMOKE=1 to opt into the isolated payload install test."
    exit 3
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Installer install/uninstall execution SKIPPED: elevated token required."
    exit 3
}

$registryQueries = @{
    "HKCU-fxfile" = @("query", "HKCU\Software\fxfile")
    "HKLM-uninstall-64" = @("query", "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\fxfile", "/reg:64")
    "HKLM-uninstall-32" = @("query", "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\fxfile", "/reg:32")
    "HKCR-shell-64" = @("query", "HKCR\Folder\shell\fxfile로 열기", "/reg:64")
    "HKCR-shell-32" = @("query", "HKCR\Folder\shell\fxfile로 열기", "/reg:32")
    "HKCU-run-launcher" = @("query", "HKCU\Software\Microsoft\Windows\CurrentVersion\Run", "/v", "fxfile-launcher")
    "HKCU-run-upchecker" = @("query", "HKCU\Software\Microsoft\Windows\CurrentVersion\Run", "/v", "fxfile-upchecker")
}

$before = @{}
foreach ($name in $registryQueries.Keys) {
    $before[$name] = Get-RegSnapshot $registryQueries[$name]
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("flyExplorer-installer-smoke-" + [guid]::NewGuid().ToString("N"))
$installDir = Join-Path $tempRoot "install"
$runtimeSkipped = $false

try {
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

    $installProcess = Start-Process -FilePath $installer -ArgumentList @("/S", "/FXFILE_SMOKE=$installDir") -Wait -PassThru
    if ($installProcess.ExitCode -ne 0) {
        throw "Isolated installer exited with code $($installProcess.ExitCode)."
    }

    foreach ($relative in @(
        "fxfile.exe",
        "fxfile-crash.dll",
        "fxfile-launcher.exe",
        "fxfile-keyhook.dll",
        "Uninstall.exe"
    )) {
        Assert-File (Join-Path $installDir $relative) "installed payload"
    }

    $xpr = @(
        (Join-Path $installDir "libxprw.dll"),
        (Join-Path $installDir "libxpr.dll")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
    if ($xpr.Count -ne 1) {
        throw "Expected exactly one installed xpr runtime; found $($xpr.Count)."
    }

    if ((Test-Path -LiteralPath (Join-Path $installDir "x64") -PathType Container) -or
        (Test-Path -LiteralPath (Join-Path $installDir "x86-unicode") -PathType Container) -or
        (Test-Path -LiteralPath (Join-Path $installDir "x86-multibyte") -PathType Container)) {
        throw "Installer left architecture staging directories in the install root."
    }

    $afterInstall = @{}
    foreach ($name in $registryQueries.Keys) {
        $afterInstall[$name] = Get-RegSnapshot $registryQueries[$name]
    }
    Assert-SnapshotUnchanged $before $afterInstall

    $runtimeSmoke = Join-Path $PSScriptRoot "runtime_smoke.ps1"
    & $runtimeSmoke -SourceDir $installDir -Configuration "Installer smoke payload" -SkipIfUserStateExists
    if ($LASTEXITCODE -eq 3) {
        $runtimeSkipped = $true
        Write-Host "Installed payload runtime smoke SKIPPED due to protected existing user state."
    }
    elseif ($LASTEXITCODE -ne 0) {
        throw "Installed payload runtime smoke failed with exit code $LASTEXITCODE."
    }

    $uninstaller = Join-Path $installDir "Uninstall.exe"
    Assert-File $uninstaller "smoke uninstaller"

    $uninstallProcess = Start-Process -FilePath $uninstaller -ArgumentList @("/S", "/FXFILE_SMOKE=1") -Wait -PassThru
    if ($uninstallProcess.ExitCode -ne 0) {
        throw "Isolated uninstaller exited with code $($uninstallProcess.ExitCode)."
    }

    if (Test-Path -LiteralPath $installDir) {
        throw "Isolated uninstaller left the temporary install directory behind: $installDir"
    }

    $afterUninstall = @{}
    foreach ($name in $registryQueries.Keys) {
        $afterUninstall[$name] = Get-RegSnapshot $registryQueries[$name]
    }
    Assert-SnapshotUnchanged $before $afterUninstall

    Write-Host "Isolated installer install/uninstall smoke PASS."
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($runtimeSkipped) {
    exit 3
}

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

function Get-PathSnapshot {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return "<missing>"
    }

    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $item = Get-Item -LiteralPath $Path
        $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        return "file|$($item.Length)|$hash"
    }

    $root = (Resolve-Path -LiteralPath $Path).Path
    $entries = @(
        Get-ChildItem -LiteralPath $root -Recurse -Force |
            ForEach-Object {
                $relative = $_.FullName.Substring($root.Length).TrimStart("\")
                if ($_.PSIsContainer) {
                    "dir|$relative"
                }
                else {
                    $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                    "file|$relative|$($_.Length)|$hash"
                }
            } |
            Sort-Object
    )
    return ($entries -join [Environment]::NewLine)
}

function Get-PeMachine {
    param([string]$Path)

    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    try {
        $reader = [System.IO.BinaryReader]::new($stream)
        if ($reader.ReadUInt16() -ne 0x5A4D) {
            throw "Not a PE image: $Path"
        }
        $stream.Position = 0x3C
        $peOffset = $reader.ReadInt32()
        $stream.Position = $peOffset
        if ($reader.ReadUInt32() -ne 0x00004550) {
            throw "Invalid PE signature: $Path"
        }
        return $reader.ReadUInt16()
    }
    finally {
        $stream.Dispose()
    }
}

function Assert-ProcessesAlive {
    param([int[]]$ProcessIds)

    foreach ($processId in $ProcessIds) {
        if (-not (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
            throw "Installer smoke terminated a pre-existing fxfile process: PID $processId"
        }
    }
}


$dist = (Resolve-Path -LiteralPath $DistDir).Path
$installer = Join-Path $dist "fxfile_v2.0.4-dev.exe"
$setupPath = Join-Path $dist "setup.nsi"

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

Assert-File $installer "NSIS installer"

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

$protectedPaths = @(
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "fxfile.lnk"),
    (Join-Path $env:PUBLIC "Desktop\fxfile.lnk"),
    (Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\fxfile.lnk"),
    (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\fxfile"),
    (Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs\fxfile")
)
$protectedPathBefore = @{}
foreach ($path in $protectedPaths) {
    $protectedPathBefore[$path] = Get-PathSnapshot $path
}

$protectedProcessIds = @(
    Get-Process -Name "fxfile" -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Id
)

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("flyExplorer-installer-smoke-" + [guid]::NewGuid().ToString("N"))
$installDir = Join-Path $tempRoot "install"
$siblingSentinel = Join-Path $tempRoot "sibling-sentinel.txt"
$runtimeSkipped = $false

try {
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    Set-Content -LiteralPath $siblingSentinel -Value "flyExplorer installer smoke sentinel" -Encoding ASCII

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

    $expectedMainMachine = if ([Environment]::Is64BitOperatingSystem) { 0x8664 } else { 0x014C }
    $mainMachine = Get-PeMachine (Join-Path $installDir "fxfile.exe")
    if ($mainMachine -ne $expectedMainMachine) {
        throw ("Installed fxfile.exe architecture mismatch: expected 0x{0:X4}, got 0x{1:X4}" -f $expectedMainMachine, $mainMachine)
    }

    $upcheckerPath = Join-Path $installDir "upchecker\fxfile-upchecker.exe"
    Assert-File $upcheckerPath "installed updater helper"
    $upcheckerMachine = Get-PeMachine $upcheckerPath
    if ($upcheckerMachine -ne 0x014C) {
        throw ("Installed upchecker architecture mismatch: expected x86 0x014C, got 0x{0:X4}" -f $upcheckerMachine)
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
    Assert-ProcessesAlive $protectedProcessIds

    foreach ($path in $protectedPaths) {
        if ((Get-PathSnapshot $path) -ne $protectedPathBefore[$path]) {
            throw "Installer smoke changed protected shortcut/start-menu state: $path"
        }
    }

    if (-not (Test-Path -LiteralPath $siblingSentinel -PathType Leaf)) {
        throw "Installer smoke removed the sibling sentinel during install."
    }

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
    Assert-ProcessesAlive $protectedProcessIds

    foreach ($path in $protectedPaths) {
        if ((Get-PathSnapshot $path) -ne $protectedPathBefore[$path]) {
            throw "Installer smoke changed protected shortcut/start-menu state: $path"
        }
    }

    if (-not (Test-Path -LiteralPath $siblingSentinel -PathType Leaf) -or
        (Get-Content -LiteralPath $siblingSentinel -Raw).Trim() -ne "flyExplorer installer smoke sentinel") {
        throw "Isolated uninstaller removed or modified the sibling sentinel."
    }

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

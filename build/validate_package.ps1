param(
    [string]$DistDir = "dist"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$dist = (Resolve-Path -LiteralPath $DistDir).Path

$configurations = @(
    @{
        Name = "x64"
        Xpr = "libxprw.dll"
        Zip = "fxfile_v2.0.4-dev_x64_portable.zip"
    },
    @{
        Name = "x86-unicode"
        Xpr = "libxprw.dll"
        Zip = "fxfile_v2.0.4-dev_x86_unicode_portable.zip"
    },
    @{
        Name = "x86-multibyte"
        Xpr = "libxpr.dll"
        Zip = "fxfile_v2.0.4-dev_x86_multibyte_portable.zip"
    }
)

$commonFiles = @(
    "fxfile.exe",
    "fxfile-crash.dll",
    "fxfile-launcher.exe",
    "fxfile-keyhook.dll",
    "libcharset-1.dll",
    "libgcc_s_sjlj-1.dll",
    "libgfl340.dll",
    "libgfle340.dll",
    "libiconv-2.dll",
    "libwinpthread-1.dll",
    "libxml2-2.dll",
    "zlib1.dll"
)

$upcheckerFiles = @(
    "upchecker/fxfile-upchecker.exe",
    "upchecker/dbghelp.dll",
    "upchecker/libcurl.dll",
    "upchecker/libgcc_s_sjlj-1.dll",
    "upchecker/libiconv-2.dll",
    "upchecker/libwinpthread-1.dll",
    "upchecker/libxml2-2.dll",
    "upchecker/libxpr.dll",
    "upchecker/zlib1.dll"
)

$forbiddenExtensions = @(".pdb", ".obj", ".lib", ".vcxproj", ".sln")

function Assert-File {
    param([string]$Path, [string]$Description)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Description is missing: $Path"
    }
    if ((Get-Item -LiteralPath $Path).Length -le 0) {
        throw "$Description is empty: $Path"
    }
}

function Normalize-ZipPath {
    param([string]$Path)
    return ($Path -replace "\\", "/").TrimStart("/")
}

function Assert-SafeZipPath {
    param([string]$Path, [string]$ConfigName)

    $normalized = $Path -replace "\\", "/"
    if ($normalized.StartsWith("/") -or
        $normalized -match "^[A-Za-z]:" -or
        @($normalized.Split("/") | Where-Object { $_ -eq ".." }).Count -gt 0) {
        throw "$ConfigName portable archive contains unsafe path: $Path"
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

foreach ($config in $configurations) {
    $stage = Join-Path $dist ("bin\" + $config.Name)
    if (-not (Test-Path -LiteralPath $stage -PathType Container)) {
        throw "Package staging directory is missing: $stage"
    }

    foreach ($relative in $commonFiles + @($config.Xpr) + $upcheckerFiles) {
        Assert-File (Join-Path $stage ($relative -replace "/", "\")) "$($config.Name) package payload"
    }

    $languages = @(Get-ChildItem -LiteralPath (Join-Path $stage "Languages") -Filter "*.xml" -File -ErrorAction SilentlyContinue)
    if ($languages.Count -eq 0) {
        throw "$($config.Name) package has no language XML files."
    }

    $unexpectedXpr = if ($config.Xpr -eq "libxprw.dll") { "libxpr.dll" } else { "libxprw.dll" }
    if (Test-Path -LiteralPath (Join-Path $stage $unexpectedXpr) -PathType Leaf) {
        throw "$($config.Name) staging contains wrong XPR runtime: $unexpectedXpr"
    }

    foreach ($archDir in @("x64", "x86-unicode", "x86-multibyte")) {
        if (Test-Path -LiteralPath (Join-Path $stage $archDir) -PathType Container) {
            throw "$($config.Name) staging unexpectedly contains architecture directory: $archDir"
        }
    }

    $staleStage = @(Get-ChildItem -LiteralPath $stage -Recurse -File | Where-Object {
        $_.Name -ieq "fxfile-updater.exe"
    })
    if ($staleStage.Count -gt 0) {
        throw "Stale updater payload found in $($config.Name) staging: $($staleStage.FullName -join ', ')"
    }

    $forbiddenStage = @(Get-ChildItem -LiteralPath $stage -Recurse -File | Where-Object {
        $forbiddenExtensions -contains $_.Extension.ToLowerInvariant()
    })
    if ($forbiddenStage.Count -gt 0) {
        throw "Development artifacts found in $($config.Name) staging: $($forbiddenStage.FullName -join ', ')"
    }

    $zipPath = Join-Path $dist $config.Zip
    Assert-File $zipPath "$($config.Name) portable archive"

    $archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        $entries = @($archive.Entries | Where-Object { -not [string]::IsNullOrEmpty($_.Name) })
        if ($entries.Count -eq 0) {
            throw "$($config.Name) portable archive is empty."
        }

        foreach ($entry in $entries) {
            Assert-SafeZipPath $entry.FullName $config.Name
        }

        $entryNames = @($entries | ForEach-Object { Normalize-ZipPath $_.FullName })
        $duplicateNames = @(
            $entryNames |
                Group-Object { $_.ToLowerInvariant() } |
                Where-Object { $_.Count -gt 1 }
        )
        if ($duplicateNames.Count -gt 0) {
            throw "$($config.Name) portable archive has duplicate/case-colliding entries: $($duplicateNames.Name -join ', ')"
        }

        $unexpectedXprName = if ($config.Xpr -eq "libxprw.dll") { "libxpr.dll" } else { "libxprw.dll" }
        if ($entryNames -icontains $unexpectedXprName) {
            throw "$($config.Name) portable archive contains wrong XPR runtime: $unexpectedXprName"
        }

        foreach ($archDir in @("x64/", "x86-unicode/", "x86-multibyte/")) {
            if (@($entryNames | Where-Object { $_.StartsWith($archDir, [StringComparison]::OrdinalIgnoreCase) }).Count -gt 0) {
                throw "$($config.Name) portable archive contains nested architecture staging: $archDir"
            }
        }

        if (@($entryNames | Where-Object { [System.IO.Path]::GetFileName($_) -ieq "fxfile-updater.exe" }).Count -gt 0) {
            throw "$($config.Name) portable archive contains stale fxfile-updater.exe."
        }

        foreach ($relative in $commonFiles + @($config.Xpr) + $upcheckerFiles) {
            $expected = Normalize-ZipPath $relative
            if ($entryNames -cnotcontains $expected) {
                $caseInsensitiveMatch = @($entryNames | Where-Object { $_ -ieq $expected })
                if ($caseInsensitiveMatch.Count -gt 0) {
                    throw "$($config.Name) portable archive casing mismatch: expected $expected, found $($caseInsensitiveMatch[0])"
                }
                throw "$($config.Name) portable archive is missing: $expected"
            }
        }

        if (-not ($entryNames | Where-Object { $_ -like "Languages/*.xml" })) {
            throw "$($config.Name) portable archive has no language XML files."
        }

        $forbiddenZip = @($entries | Where-Object {
            $forbiddenExtensions -contains [System.IO.Path]::GetExtension($_.Name).ToLowerInvariant()
        })
        if ($forbiddenZip.Count -gt 0) {
            throw "Development artifacts found in $($config.Name) portable archive: $($forbiddenZip.FullName -join ', ')"
        }
    }
    finally {
        $archive.Dispose()
    }

    Write-Host "Verified package staging and portable archive: $($config.Name)"
}

$installer = Join-Path $dist "fxfile_v2.0.4-dev.exe"
Assert-File $installer "NSIS installer"

$setup = Get-Content -LiteralPath (Join-Path $dist "setup.nsi") -Raw
foreach ($token in @(
    'File /r "bin\*.*"',
    'CopyFiles /silent "$INSTDIR\x86-unicode\*.*" "$INSTDIR"',
    'CopyFiles /silent "$INSTDIR\x86-multibyte\*.*" "$INSTDIR"',
    'CopyFiles /silent "$INSTDIR\x64\*.*" "$INSTDIR"'
)) {
    if (-not $setup.Contains($token)) {
        throw "setup.nsi is missing package contract token: $token"
    }
}

foreach ($token in @(
    'Var SMOKE_MODE',
    '/FXFILE_SMOKE=',
    'StrCmp $SMOKE_MODE "1" SkipInstallProcessKill',
    'StrCmp $SMOKE_MODE "1" CreateUninstaller',
    'StrCmp $SMOKE_MODE "1" unSmokeCleanup'
)) {
    if (-not $setup.Contains($token)) {
        throw "setup.nsi is missing installer-smoke safety contract: $token"
    }
}

foreach ($stale in @("fxfile-updater.exe", "\updater\")) {
    if ($setup.Contains($stale)) {
        throw "setup.nsi still references stale updater contract: $stale"
    }
}

Write-Host "Verified NSIS installer output: $installer"
Write-Host "Package validation PASS."

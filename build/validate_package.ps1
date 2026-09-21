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

        $entryNames = @($entries | ForEach-Object { Normalize-ZipPath $_.FullName })
        foreach ($relative in $commonFiles + @($config.Xpr) + $upcheckerFiles) {
            $expected = Normalize-ZipPath $relative
            if ($entryNames -notcontains $expected) {
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

foreach ($stale in @("fxfile-updater.exe", "\updater\")) {
    if ($setup.Contains($stale)) {
        throw "setup.nsi still references stale updater contract: $stale"
    }
}

Write-Host "Verified NSIS installer output: $installer"
Write-Host "Package validation PASS."

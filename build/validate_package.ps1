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
        Machine = 0x8664
        Zip = "fxfile_v2.0.4-dev_x64_portable.zip"
    },
    @{
        Name = "x86-unicode"
        Xpr = "libxprw.dll"
        Machine = 0x014C
        Zip = "fxfile_v2.0.4-dev_x86_unicode_portable.zip"
    },
    @{
        Name = "x86-multibyte"
        Xpr = "libxpr.dll"
        Machine = 0x014C
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

# Portable assets must be next to fxfile.exe, not merely in the installer.
$portableAncillaryFiles = @(
    "fxfile.chm",
    "custom_image_list_16.bmp",
    "custom_image_list_32.bmp",
    "license.txt",
    "readme.txt",
    "history.txt",
    "third_party_notices.txt"
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

function Assert-ChmHeader {
    param(
        [System.IO.Stream]$Stream,
        [string]$Description,
        [long]$UncompressedLength
    )
    if ($UncompressedLength -lt 4096) {
        throw "$Description is too short to be a usable CHM."
    }
    [byte[]]$signature = @(0, 0, 0, 0)
    $offset = 0
    while ($offset -lt 4) {
        $read = $Stream.Read($signature, $offset, 4 - $offset)
        if ($read -le 0) {
            throw "$Description ended before its CHM signature."
        }
        $offset += $read
    }
    if ($signature[0] -ne 0x49 -or
        $signature[1] -ne 0x54 -or
        $signature[2] -ne 0x53 -or
        $signature[3] -ne 0x46) {
        throw "$Description does not start with ITSF (compiled CHM)."
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

function Get-PeMachineFromStream {
    param(
        [System.IO.Stream]$Stream,
        [string]$Description
    )

    if (-not $Stream.CanSeek) {
        throw "$Description stream is not seekable."
    }

    $reader = New-Object System.IO.BinaryReader($Stream)
    try {
        if ($Stream.Length -lt 64 -or $reader.ReadUInt16() -ne 0x5A4D) {
            throw "$Description does not have an MZ header."
        }

        $Stream.Position = 0x3C
        $peOffset = $reader.ReadInt32()
        if ($peOffset -lt 0 -or ($peOffset + 6) -gt $Stream.Length) {
            throw "$Description has an invalid PE offset."
        }

        $Stream.Position = $peOffset
        if ($reader.ReadUInt32() -ne 0x00004550) {
            throw "$Description does not have a PE signature."
        }

        return $reader.ReadUInt16()
    }
    finally {
        $reader.Dispose()
    }
}

function Get-PeMachine {
    param([string]$Path, [string]$Description)

    $stream = [System.IO.File]::OpenRead($Path)
    return Get-PeMachineFromStream $stream $Description
}

function Get-ZipEntryPeMachine {
    param(
        [System.IO.Compression.ZipArchiveEntry]$Entry,
        [string]$Description
    )

    $entryStream = $Entry.Open()
    $memory = New-Object System.IO.MemoryStream
    try {
        $entryStream.CopyTo($memory)
        $memory.Position = 0
        return Get-PeMachineFromStream $memory $Description
    }
    finally {
        $entryStream.Dispose()
        $memory.Dispose()
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

foreach ($config in $configurations) {
    $stage = Join-Path $dist ("bin\" + $config.Name)
    if (-not (Test-Path -LiteralPath $stage -PathType Container)) {
        throw "Package staging directory is missing: $stage"
    }

    foreach ($relative in $commonFiles + @($config.Xpr) + $portableAncillaryFiles) {
        Assert-File (Join-Path $stage ($relative -replace "/", "\")) "$($config.Name) package payload"
    }

    $stageChm = [System.IO.File]::OpenRead((Join-Path $stage "fxfile.chm"))
    try {
        Assert-ChmHeader $stageChm "$($config.Name) staged help" $stageChm.Length
    }
    finally {
        $stageChm.Dispose()
    }

    $mainExe = Join-Path $stage "fxfile.exe"
    $mainMachine = Get-PeMachine $mainExe "$($config.Name) fxfile.exe"
    if ($mainMachine -ne $config.Machine) {
        throw ("$($config.Name) fxfile.exe architecture mismatch: expected 0x{0:X4}, got 0x{1:X4}" -f $config.Machine, $mainMachine)
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
        $_.Name -match '^fxfile-(?:upchecker|updater)\.exe$' -or
        $_.FullName.Substring($stage.Length).TrimStart([char[]]'\/') -match '^(?:upchecker|updater)[\\/]'
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

        $helpEntry = @($entries | Where-Object {
            (Normalize-ZipPath $_.FullName) -ceq "fxfile.chm"
        })
        if ($helpEntry.Count -ne 1) {
            throw "$($config.Name) archive must contain exactly one compiled help file."
        }
        $helpStream = $helpEntry[0].Open()
        try {
            Assert-ChmHeader $helpStream "$($config.Name) archive help" $helpEntry[0].Length
        }
        finally {
            $helpStream.Dispose()
        }

        $mainEntry = @($entries | Where-Object {
            (Normalize-ZipPath $_.FullName) -ceq "fxfile.exe"
        })
        if ($mainEntry.Count -ne 1) {
            throw "$($config.Name) portable archive must contain exactly one fxfile.exe."
        }
        $mainZipMachine = Get-ZipEntryPeMachine $mainEntry[0] "$($config.Name) archive fxfile.exe"
        if ($mainZipMachine -ne $config.Machine) {
            throw ("$($config.Name) archive fxfile.exe architecture mismatch: expected 0x{0:X4}, got 0x{1:X4}" -f $config.Machine, $mainZipMachine)
        }

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

        $retiredUpdaterEntries = @($entryNames | Where-Object {
            $_ -match '^(?:upchecker|updater)/' -or
            [System.IO.Path]::GetFileName($_) -match '^fxfile-(?:upchecker|updater)\.exe$'
        })
        if ($retiredUpdaterEntries.Count -gt 0) {
            throw "$($config.Name) portable archive contains retired updater payload: $($retiredUpdaterEntries -join ', ')"
        }

        foreach ($relative in $commonFiles + @($config.Xpr) + $portableAncillaryFiles) {
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

foreach ($stale in @("fxfile-updater.exe", "fxfile-upchecker.exe")) {
    if ($setup.Contains($stale)) {
        throw "setup.nsi still references stale updater contract: $stale"
    }
}

Write-Host "Verified NSIS installer output: $installer"
Write-Host "Package validation PASS."

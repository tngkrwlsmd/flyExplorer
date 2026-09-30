param(
    [Parameter(Mandatory = $true)]
    [string]$Configuration
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

switch -Wildcard ($Configuration) {
    "*-x64-*" {
        $relativeOutputDir = "bin\x64"
        break
    }
    "*-x86-Unicode" {
        $relativeOutputDir = "bin\x86-unicode"
        break
    }
    "*-x86-Multibyte" {
        $relativeOutputDir = "bin\x86-multibyte"
        break
    }
    default {
        Write-Host "Build output lock preflight SKIPPED: unknown configuration '$Configuration'."
        exit 0
    }
}

$outputDir = Join-Path $repoRoot $relativeOutputDir
if (-not (Test-Path -LiteralPath $outputDir)) {
    exit 0
}

# Repository-owned linker outputs that Rebuild may replace. Third-party runtime
# DLLs are staged separately by copy_lib.bat.
$outputNames = @(
    "fxfile.exe",
    "fxfile_dbg.exe",
    "libxprw.dll",
    "libxprw_dbg.dll",
    "libxpr.dll",
    "libxpr_dbg.dll",
    "fxfile-crash.dll",
    "fxfile-crash_dbg.dll",
    "fxfile-launcher.exe",
    "fxfile-launcher_dbg.exe",
    "fxfile-keyhook.dll",
    "fxfile-keyhook_dbg.dll",
    "fxfile-functional-tests.exe"
)

$blocked = New-Object System.Collections.Generic.List[string]

foreach ($name in $outputNames) {
    $path = Join-Path $outputDir $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        continue
    }

    $available = $false
    for ($attempt = 0; $attempt -lt 3; ++$attempt) {
        $stream = $null
        try {
            $stream = [System.IO.File]::Open(
                $path,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::ReadWrite,
                [System.IO.FileShare]::None
            )
            $available = $true
            break
        }
        catch [System.IO.IOException] {
            if ($attempt -lt 2) {
                Start-Sleep -Milliseconds 150
            }
        }
        catch [System.UnauthorizedAccessException] {
            break
        }
        finally {
            if ($null -ne $stream) {
                $stream.Dispose()
            }
        }
    }

    if (-not $available) {
        $blocked.Add($path)
    }
}

if ($blocked.Count -eq 0) {
    exit 0
}

Write-Host "ERROR: Local CI cannot rebuild because existing build outputs are in use or not writable:"
foreach ($path in $blocked) {
    $displayPath = $path.Substring($repoRoot.Length).TrimStart("\")
    Write-Host "  $displayPath"
}
Write-Host ""
Write-Host "Close any flyExplorer instance launched from this repository's bin directory,"
Write-Host "then run local_ci.bat again. Local CI will not terminate user processes automatically."
exit 2

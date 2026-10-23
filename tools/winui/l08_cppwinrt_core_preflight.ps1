#requires -Version 5.1
<#
.SYNOPSIS
Small L08 C++/WinRT toolchain and full-error logging preflight.
.DESCRIPTION
Compiles one isolated Windows.Foundation projection source with /Zs and
proves a deliberate C1189 diagnostic survives output capture. It does NOT
validate WinUI/Windows App SDK ProtectedCursor nor build flyExplorer.
Creates/removes only a named RUNNER_TEMP child; never accesses user files.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) { throw 'L08_RUNNER_TEMP_REQUIRED' }

$root = [IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
$owned = Join-Path $root 'fly-l08-compiler-core-preflight'
if (Test-Path -LiteralPath $owned) { throw 'L08_SCRATCH_ALREADY_EXISTS' }
New-Item -ItemType Directory -Path $owned -ErrorAction Stop | Out-Null

try {
    $vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
    $sdk = 'C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\cppwinrt'
    if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
        throw 'L08_VSWHERE_MISSING'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $sdk 'winrt\Windows.Foundation.h') -PathType Leaf)) {
        throw 'L08_WINSDK_PROJECTION_MISSING'
    }
    $install = (& $vswhere -latest -products '*' -property installationPath).Trim()
    if (-not $install) { throw 'L08_VS_INSTALL_MISSING' }
    $vcvars = Join-Path $install 'VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path -LiteralPath $vcvars -PathType Leaf)) {
        throw 'L08_VCVARS_MISSING'
    }

    $source = @'
#include <winrt/Windows.Foundation.h>
#include <string>

struct L08Probe : winrt::implements<L08Probe, winrt::Windows::Foundation::IStringable> {
    winrt::hstring ToString() { return L"OK"; }
    void Check() {
        std::wstring value=L"hello";
        winrt::hstring diagnostic(value.c_str());
        auto iface=get_strong().as<winrt::Windows::Foundation::IStringable>();
        (void)diagnostic;
        (void)iface;
    }
};
'@
    $cpp = Join-Path $owned 'l08_compile_core.cpp'
    Set-Content -LiteralPath $cpp -Value $source -Encoding UTF8 -ErrorAction Stop
    $log = Join-Path $owned 'compiler.log'
    $compile = 'call "' + $vcvars + '" >nul && cl.exe /nologo /std:c++20 /EHsc /Zs /utf-8 /I "' + $sdk + '" "' + $cpp + '"'
    & cmd.exe /d /c $compile 2>&1 | Out-File -LiteralPath $log -Encoding UTF8
    $exit = $LASTEXITCODE
    Write-Output ('L08_CORE_COMPILER_EXIT=' + $exit)
    if ($exit -ne 0) {
        # Copy the exact error to CI before scratch retirement. Never mask
        # the native compiler's error behind a synthetic Python contract.
        foreach ($line in @(Get-Content -LiteralPath $log -Encoding UTF8)) {
            Write-Output ('L08_CORE_COMPILER_ERROR ' + $line)
        }
        throw 'L08_CORE_COMPILE_FAILED'
    }
    Write-Output 'L08_CPPWINRT_CORE_COMPILE_PASS=True'

    $negative = Join-Path $owned 'l08_expected_error.cpp'
    Set-Content -LiteralPath $negative -Value '#error L08_EXPECTED_COMPILER_DIAGNOSTIC' -Encoding UTF8
    $errLog = Join-Path $owned 'expected-error.log'
    $negativeCommand = 'call "' + $vcvars + '" >nul && cl.exe /nologo /Zs "' + $negative + '"'
    & cmd.exe /d /c $negativeCommand 2>&1 | Out-File -LiteralPath $errLog -Encoding UTF8
    $negativeExit = $LASTEXITCODE
    $errorContent = Get-Content -LiteralPath $errLog -Raw -Encoding UTF8
    Write-Output ('L08_EXPECTED_ERROR_EXIT=' + $negativeExit)
    if ($negativeExit -eq 0 -or -not $errorContent.Contains('L08_EXPECTED_COMPILER_DIAGNOSTIC')) {
        throw 'L08_ORIGINAL_DIAGNOSTIC_NOT_CAPTURED'
    }
    foreach ($line in @(Get-Content -LiteralPath $errLog -Encoding UTF8)) {
        Write-Output ('L08_EXPECTED_COMPILER_ERROR ' + $line)
    }
    Write-Output 'L08_COMPILER_ERROR_CAPTURE_PASS=True'
} finally {
    if (Test-Path -LiteralPath $owned -PathType Container) {
        $candidate = [IO.Path]::GetFullPath($owned)
        $expected = [IO.Path]::GetFullPath((Join-Path $root 'fly-l08-compiler-core-preflight'))
        if ($candidate -cne $expected) { throw 'L08_UNSAFE_SCRATCH_PATH' }
        $item = Get-Item -LiteralPath $candidate -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'L08_UNSAFE_SCRATCH_REPARSE'
        }
        Remove-Item -LiteralPath $candidate -Recurse -Force -ErrorAction Stop
        Write-Output 'L08_COMPILER_SCRATCH_REMOVED=True'
    }
}

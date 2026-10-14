# F03 owned native reader acceptance. Never changes user profile or settings.
# Invocation must supply a fresh, test-owned FixtureRoot on a fixed local volume.
param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$FixtureRoot,
    [Parameter(Mandatory=$true)][string]$ExpectedSha
)
$ErrorActionPreference='Stop'
if($ExpectedSha -cnotmatch '^[a-f0-9]{40}$'){throw 'F03_NATIVE_INVALID_SHA'}
if(-not (Test-Path -LiteralPath $SourceRoot -PathType Container)){
    throw 'F03_NATIVE_SOURCE_ROOT_MISSING'
}
if(-not (Test-Path -LiteralPath $FixtureRoot -PathType Container)){
    throw 'F03_NATIVE_FIXTURE_ROOT_MISSING'
}
$actual=(& git -C $SourceRoot rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $actual -cne $ExpectedSha){
    throw ('F03_NATIVE_SOURCE_SHA_MISMATCH '+$actual)
}
if(@(Get-ChildItem -LiteralPath $FixtureRoot -Force).Count -ne 0){
    throw 'F03_NATIVE_FIXTURE_MUST_BE_EMPTY'
}
$programFiles32=[Environment]::GetFolderPath('ProgramFilesX86')
$vswhere=Join-Path $programFiles32 'Microsoft Visual Studio\Installer\vswhere.exe'
if(-not (Test-Path -LiteralPath $vswhere -PathType Leaf)){
    throw 'F03_NATIVE_VSWHERE_MISSING'
}
$install=(& $vswhere -latest -products '*' -requires 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64' -property installationPath)
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($install)){
    throw 'F03_NATIVE_MSVC_NOT_FOUND'
}
$vcvars=Join-Path $install 'VC\Auxiliary\Build\vcvars64.bat'
if(-not (Test-Path -LiteralPath $vcvars -PathType Leaf)){
    throw 'F03_NATIVE_VCVARS_MISSING'
}
$sourceCpp=Join-Path $SourceRoot 'src\base\file_preview_reader.cpp'
$testCpp=Join-Path $SourceRoot 'tests\winui\native_preview_reader.cpp'
$exe=Join-Path $FixtureRoot 'f03-reader-native.exe'
$batch=Join-Path $FixtureRoot 'compile-and-test.cmd'
$log=Join-Path $FixtureRoot 'compile.log'
$setupLog=Join-Path $FixtureRoot 'vcvars-setup.log'
$testFolder=Join-Path $FixtureRoot 'test-data'
New-Item -ItemType Directory -Path $testFolder -ErrorAction Stop | Out-Null
# All outputs / objects remain inside the supplied owned fixture.
# ASCII command paths are required in this bounded VM scratch invocation;
# the C++ sources are decoded with /utf-8 to retain Korean test names.
$body=@(
    '@echo off',
    'setlocal',
    'call "'+$vcvars+'" >"'+$setupLog+'" 2>&1',
    'if errorlevel 1 exit /b 22',
    'cd /d "'+$FixtureRoot+'"',
    'cl.exe /nologo /std:c++20 /W4 /WX /EHsc /utf-8 /MD /Fe:"'+$exe+'" "'+$sourceCpp+'" "'+$testCpp+'" >"'+$log+'" 2>&1',
    'if errorlevel 1 exit /b 23',
    '"'+$exe+'" "'+$testFolder+'"',
    'exit /b %errorlevel%'
)
[IO.File]::WriteAllLines($batch,$body,[Text.Encoding]::ASCII)
& cmd.exe /d /c $batch
$code=$LASTEXITCODE
if($code -ne 0){
    if($code -eq 22 -and (Test-Path -LiteralPath $setupLog)){
        Get-Content -LiteralPath $setupLog -Tail 35 | ForEach-Object {Write-Output ('F03_NATIVE_VCVARS '+$_)}
    }
    if(Test-Path -LiteralPath $log){
        Get-Content -LiteralPath $log -Tail 25 | ForEach-Object {Write-Output $_}
    }
    throw ('F03_NATIVE_TEST_FAILED_EXIT_'+$code)
}
if(@(Get-ChildItem -LiteralPath $testFolder -Force).Count -ne 0){
    throw 'F03_NATIVE_TEST_LEFT_OWNED_FILES'
}
Write-Output ('F03_NATIVE_VERIFIED_HANDLE_ACCEPTANCE=PASS SHA='+$ExpectedSha)

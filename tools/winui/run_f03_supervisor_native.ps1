#requires -Version 5.1
# F03 exact-SHA native parent+real child acceptance. Test-owned files only.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$SourceRoot,
    [Parameter(Mandatory)][string]$FixtureRoot,
    [Parameter(Mandatory)][ValidatePattern('^[a-f0-9]{40}$')][string]$ExpectedSha
)
$ErrorActionPreference='Stop'
if(-not (Test-Path -LiteralPath $SourceRoot -PathType Container) -or
   -not (Test-Path -LiteralPath $FixtureRoot -PathType Container)){
    throw 'F03_SUPERVISOR_SOURCE_OR_OWNED_ROOT_MISSING'
}
$head=(& git -C $SourceRoot rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $head -cne $ExpectedSha){
    throw 'F03_SUPERVISOR_SOURCE_SHA_MISMATCH'
}
if(@(Get-ChildItem -LiteralPath $FixtureRoot -Force).Count -ne 0){
    throw 'F03_SUPERVISOR_OWNED_ROOT_NOT_EMPTY'
}
$helper=Join-Path $SourceRoot 'out\helper\Release\FlyShellIsolationHelper.exe'
if(-not (Test-Path -LiteralPath $helper -PathType Leaf)){
    throw 'F03_SUPERVISOR_SHIPPING_CHILD_MUST_BE_BUILT'
}
$pf86=[Environment]::GetFolderPath('ProgramFilesX86')
$vswhere=Join-Path $pf86 'Microsoft Visual Studio\Installer\vswhere.exe'
if(-not (Test-Path -LiteralPath $vswhere -PathType Leaf)){
    throw 'F03_SUPERVISOR_VSWHERE_MISSING'
}
$install=(& $vswhere -latest -products '*' -requires 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64' -property installationPath)
$vcvars=Join-Path $install 'VC\Auxiliary\Build\vcvars64.bat'
if(-not (Test-Path -LiteralPath $vcvars -PathType Leaf)){
    throw 'F03_SUPERVISOR_VCVARS_MISSING'
}
$cpp=Join-Path $SourceRoot 'src\base\file_preview_supervisor.cpp'
$native=Join-Path $SourceRoot 'tests\winui\native_preview_supervisor.cpp'
$stub=Join-Path $SourceRoot 'tests\winui\native_preview_supervisor_stub.cpp'
$stubDir=Join-Path $FixtureRoot 'stub'
$owned=Join-Path $FixtureRoot 'data'
New-Item -ItemType Directory -Path $stubDir,$owned -ErrorAction Stop|Out-Null
$stubExe=Join-Path $stubDir 'FlyShellIsolationHelper.exe'
$exe=Join-Path $FixtureRoot 'F03PreviewSupervisorNative.exe'
$batch=Join-Path $FixtureRoot 'build-and-test.cmd'
$setup=Join-Path $FixtureRoot 'vcvars.log'
$log=Join-Path $FixtureRoot 'compile.log'
$body=@(
 '@echo off',
 'setlocal',
 ('call "'+$vcvars+'" >"'+$setup+'" 2>&1'),
 'if errorlevel 1 exit /b 22',
 ('cd /d "'+$FixtureRoot+'"'),
 ('cl.exe /nologo /std:c++20 /W4 /WX /EHsc /utf-8 /MD /Fo:"'+$FixtureRoot+'\stub.obj" /Fe:"'+$stubExe+'" "'+$stub+'" >"'+$log+'" 2>&1'),
 'if errorlevel 1 exit /b 23',
 ('cl.exe /nologo /std:c++20 /W4 /WX /EHsc /utf-8 /MD /Fe:"'+$exe+'" "'+$cpp+'" "'+$native+'" >>"'+$log+'" 2>&1'),
 'if errorlevel 1 exit /b 24',
 ('"'+$exe+'" "'+$helper+'" "'+$stubExe+'" "'+$owned+'"'),
 'exit /b %errorlevel%'
)
if($body.Count -ne 11 -or !$body[5].Contains($stub) -or
   !$body[7].Contains($cpp) -or !$body[7].Contains($native) -or
   !$body[9].Contains($helper)){throw 'F03_SUPERVISOR_BATCH_SERIALIZATION_INVALID'}
[IO.File]::WriteAllLines($batch,$body,[Text.Encoding]::ASCII)
& cmd.exe /d /c $batch
$exit=$LASTEXITCODE
if($exit -ne 0){
 if(Test-Path -LiteralPath $setup){Get-Content -LiteralPath $setup -Tail 10|ForEach-Object{Write-Output ('F03_VCVARS '+$_)}}
 if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 28|ForEach-Object{Write-Output ('F03_COMPILE '+$_)}}
 throw ('F03_SUPERVISOR_NATIVE_FAILED_EXIT_'+$exit)
}
if(@(Get-ChildItem -LiteralPath $owned -Force).Count -ne 0){
 throw 'F03_SUPERVISOR_TEST_DATA_LEFT_BEHIND'
}
Write-Output ('F03_SUPERVISOR_REAL_CHILD_NATIVE_PASS SHA='+$ExpectedSha)

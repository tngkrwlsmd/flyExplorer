#requires -Version 5.1
<#
Isolated L08 WinUI 3 projection preflight; NOT a product build or GUI test.
Tests generated WinUI InputSystemCursor and AutomationProperties APIs only.
Uses pinned NuGet components of Windows App SDK 2.5.1 and CppWinRT 2.0.250303.1.
#>
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(-not $env:RUNNER_TEMP){throw 'L08_RUNNER_TEMP_REQUIRED'}
$parent=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
$owned=Join-Path $parent 'fly-l08-winui-api-preflight'
if(Test-Path -LiteralPath $owned){throw 'L08_OWNED_FIXTURE_EXISTS'}
New-Item -ItemType Directory -Path $owned -ErrorAction Stop | Out-Null
function LogErrors([string]$file,[string]$marker){
    if(-not (Test-Path -LiteralPath $file -PathType Leaf)){return}
    # The previous bounded CI report dropped the first meaningful C++/WinRT
    # error. Keep the opening context AND error lines across the whole log.
    # Bound stdout to an explicitly reported count rather than silently
    # discarding the compiler's actual failure.
    $lines=@(Get-Content -LiteralPath $file -Encoding UTF8)
    Write-Output ($marker+'_TOTAL_LINES='+$lines.Count)
    $emitted=0
    for($index=0;$index -lt $lines.Count;$index++){
        $line=[string]$lines[$index]
        $isError=$line -match '(?i)(fatal error|error [A-Z]{1,5}[0-9]{4}|cppwinrt\s*:\s*error|mismatched C\+\+/WinRT|failed to find)'
        if($index -ge 20 -and -not $isError){continue}
        if($line.Length -gt 900){$line=$line.Substring(0,900)+' [line truncated]'}
        Write-Output ($marker+' LINE='+($index+1)+' '+$line)
        $emitted++
        if($emitted -ge 160){
            Write-Output ($marker+'_EMISSION_LIMIT=160')
            break
        }
    }
    Write-Output ($marker+'_EMITTED='+$emitted)
}
try{
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $inputs=Join-Path $owned 'winmd'
    $output=Join-Path $owned 'generated'
    $bin=Join-Path $owned 'bin'
    New-Item -ItemType Directory -Path $inputs,$output,$bin -ErrorAction Stop | Out-Null
    $packages=@(
      @{Id='microsoft.windowsappsdk.winui';Version='2.3.9';Max=80000000;Hash='D36145BD6C0F46FC04E07FB4AF365D093FB42C39B625948D0EAD07A0B26FCE96';Kind='xaml'},
      @{Id='microsoft.windowsappsdk.foundation';Version='2.3.12';Max=16000000;Hash='CE04D01D68CB16B5DC85A5C9EFB8162DBA876BC2E5B766B5968979899D4EFA9E';Kind='foundation'},
      @{Id='microsoft.windowsappsdk.interactiveexperiences';Version='2.1.9';Max=42000000;Hash='F9159D73E3E46717F159606E43B4ACF8336AAFF5BDD4D395FE3A93FDB41437AC';Kind='ui'},
      @{Id='microsoft.web.webview2';Version='1.0.3719.77';Max=15000000;Hash='2F6BE3A10A1A8D6D1FDE986AF4131DAB344F8181FFFE75590824E0F4B037ED73';Kind='webview'},
      @{Id='microsoft.windows.cppwinrt';Version='2.0.250303.1';Max=8000000;Hash='955E3051B35DB1C00177ED14AB6B7B995C3B32A53FDB6C184EA53B1DBA66E439';Kind='compiler'}
    )
    $generator=Join-Path $bin 'cppwinrt.exe'
    foreach($p in $packages){
        $name=$p.Id+'.'+$p.Version+'.nupkg'
        $zipPath=Join-Path $owned $name
        Invoke-WebRequest -Uri ('https://api.nuget.org/v3-flatcontainer/'+$p.Id+'/'+$p.Version+'/'+$name) -UseBasicParsing -OutFile $zipPath -TimeoutSec 180 -ErrorAction Stop
        $file=Get-Item -LiteralPath $zipPath -Force
        if($file.Length -lt 10000 -or $file.Length -gt $p.Max){throw ('L08_PACKAGE_SIZE_INVALID_'+$p.Id)}
        if((Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash -cne $p.Hash){throw ('L08_PACKAGE_SHA_INVALID_'+$p.Id)}
        Write-Output ('L08_PACKAGE_VERIFIED '+$p.Id+'/'+$p.Version)
        $zip=[IO.Compression.ZipFile]::OpenRead($zipPath)
        try{
            foreach($entry in $zip.Entries){
                $member=$entry.FullName
                $target=$null
                if($p.Kind -eq 'xaml' -and $member -match '^metadata/[^/]+\.winmd$'){
                    $target=Join-Path $inputs ([IO.Path]::GetFileName($member))
                }elseif($p.Kind -eq 'foundation' -and $member -match '^metadata/[^/]+\.winmd$'){
                    $target=Join-Path $inputs ([IO.Path]::GetFileName($member))
                }elseif($p.Kind -eq 'ui' -and $member -match '^metadata/10\.0\.18362\.0/(Microsoft\.Foundation|Microsoft\.Graphics|Microsoft\.UI)\.winmd$'){
                    $target=Join-Path $inputs ([IO.Path]::GetFileName($member))
                }elseif($p.Kind -eq 'webview' -and $member -match '(^|/)Microsoft\.Web\.WebView2\.Core\.winmd$'){
                    $target=Join-Path $inputs 'Microsoft.Web.WebView2.Core.winmd'
                }elseif($p.Kind -eq 'compiler' -and $member -ceq 'bin/cppwinrt.exe'){
                    $target=$generator
                }
                if($target){
                    if(Test-Path -LiteralPath $target){throw ('L08_DUPLICATE_INPUT_'+[IO.Path]::GetFileName($target))}
                    [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$target)
                }
            }
        }finally{$zip.Dispose()}
        Remove-Item -LiteralPath $zipPath -Force -ErrorAction Stop
    }
    foreach($name in @('Microsoft.UI.Xaml.winmd','Microsoft.UI.winmd','Microsoft.Foundation.winmd')){
        if(-not (Test-Path -LiteralPath (Join-Path $inputs $name) -PathType Leaf)){throw ('L08_INPUT_MISSING_'+$name)}
    }
    if(-not (Test-Path -LiteralPath $generator -PathType Leaf)){throw 'L08_CPPWINRT_MISSING'}
    if((Get-AuthenticodeSignature -FilePath $generator).Status -ne 'Valid'){throw 'L08_CPPWINRT_SIGNATURE_INVALID'}
    Write-Output 'L08_CPPWINRT_SIGNATURE_VALID=True'
    function Generate([string[]]$parameters,[string]$step){
        $stdout=Join-Path $owned ($step+'.stdout')
        $stderr=Join-Path $owned ($step+'.stderr')
        $proc=Start-Process -FilePath $generator -ArgumentList $parameters -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr -ErrorAction Stop
        Write-Output ('L08_'+$step+'_EXIT='+$proc.ExitCode)
        if($proc.ExitCode -ne 0){LogErrors $stderr 'L08_GENERATOR_ERROR';throw ('L08_'+$step+'_FAILED')}
    }
    # Generate Windows projection with this exact tool first; never mix SDK
    # winrt/base.h with newer generated Microsoft.UI.Xaml headers.
    Generate @('-input','sdk','-output',('"'+$output+'"')) 'PLATFORM'
    if(-not (Test-Path -LiteralPath (Join-Path $output 'winrt\base.h') -PathType Leaf)){
        throw 'L08_MATCHING_CPPWINRT_BASE_HEADER_MISSING'
    }
    Generate @('-input',('"'+$inputs+'"'),'-reference','sdk','-output',('"'+$output+'"')) 'WINUI'
    foreach($name in @('Microsoft.UI.h','Microsoft.UI.Xaml.h','Microsoft.UI.Xaml.Controls.h','Microsoft.UI.Xaml.Automation.h','Microsoft.UI.Input.h')){
        if(-not (Test-Path -LiteralPath (Join-Path $output ('winrt\'+$name)) -PathType Leaf)){throw ('L08_MISSING_PROJECTED_HEADER_'+$name)}
    }
    Write-Output 'L08_WINUI_REQUIRED_HEADERS_GENERATED=True'

    # Check the *final* output of both generators: a later generation
    # step must not replace/delete the version-matched platform base.h.
    $baseFile=Join-Path $output 'winrt\base.h'
    $xamlFile=Join-Path $output 'winrt\Microsoft.UI.Xaml.Controls.h'
    if(-not (Test-Path -LiteralPath $baseFile -PathType Leaf)){
        throw 'L08_FINAL_GENERATED_BASE_HEADER_MISSING'
    }
    function ProjectionVersion([string]$path){
        $versionHits=@(Get-Content -LiteralPath $path -TotalCount 64 -Encoding UTF8 |
            Select-String -Pattern '^\s*#\s*define\s+CPPWINRT_VERSION\s+(.+)$')
        if($versionHits.Count -ne 1){
            throw ('L08_CPPWINRT_VERSION_MARKER_MISSING_'+[IO.Path]::GetFileName($path))
        }
        return $versionHits[0].Matches[0].Groups[1].Value.Trim()
    }
    $baseVersion=ProjectionVersion $baseFile
    $xamlVersion=ProjectionVersion $xamlFile
    Write-Output ('L08_GENERATED_BASE_CPPWINRT_VERSION='+$baseVersion)
    Write-Output ('L08_GENERATED_XAML_CPPWINRT_VERSION='+$xamlVersion)
    if($baseVersion -cne $xamlVersion){
        throw 'L08_CPPWINRT_GENERATED_VERSION_MISMATCH'
    }
    Write-Output 'L08_CPPWINRT_GENERATED_VERSION_MATCH=True'

    $probe=Join-Path $owned 'l08_winui_api.cpp'
    $cpp=@'
#include <winrt/Microsoft.UI.Xaml.Controls.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#include <winrt/Microsoft.UI.Input.h>
void L08Probe(winrt::Microsoft::UI::Xaml::Controls::Grid const& grid) {
    auto cursor=winrt::Microsoft::UI::Input::InputSystemCursor::Create(
        winrt::Microsoft::UI::Input::InputSystemCursorShape::SizeWestEast);
    winrt::Microsoft::UI::Xaml::Automation::AutomationProperties::SetHelpText(
        grid, winrt::hstring(L"L08"));
    (void)cursor;
}
'@
    Set-Content -LiteralPath $probe -Value $cpp -Encoding UTF8 -ErrorAction Stop
    $vswhere='C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
    $vs=(& $vswhere -latest -products '*' -property installationPath).Trim()
    if(-not $vs){throw 'L08_VS_NOT_FOUND'}
    $vcvars=Join-Path $vs 'VC\Auxiliary\Build\vcvars64.bat'
    if(-not (Test-Path -LiteralPath $vcvars -PathType Leaf)){throw 'L08_VCVARS_NOT_FOUND'}
    $sdk='C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\cppwinrt'
    $log=Join-Path $owned 'compiler.log'
    $command='call "'+$vcvars+'" >nul && cl.exe /nologo /std:c++20 /EHsc /Zs /utf-8 /I "'+$output+'" /I "'+$sdk+'" "'+$probe+'"'
    & cmd.exe /d /c $command 2>&1 | Out-File -LiteralPath $log -Encoding UTF8
    $rc=$LASTEXITCODE
    Write-Output ('L08_WINUI_CPP_COMPILE_EXIT='+$rc)
    if($rc -ne 0){LogErrors $log 'L08_COMPILE_ERROR';throw 'L08_CPP_API_COMPILE_FAILED'}
    Write-Output 'L08_WINUI_API_COMPILE_PASS=True'
}finally{
    if(Test-Path -LiteralPath $owned -PathType Container){
        $item=Get-Item -LiteralPath $owned -Force
        if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'L08_UNSAFE_OWNED_DIRECTORY'}
        if([IO.Path]::GetFullPath($owned) -cne [IO.Path]::GetFullPath((Join-Path $parent 'fly-l08-winui-api-preflight'))){throw 'L08_UNEXPECTED_CLEANUP_PATH'}
        Remove-Item -LiteralPath $owned -Recurse -Force -ErrorAction Stop
        Write-Output 'L08_WINUI_SCRATCH_REMOVED=True'
    }
}

# Exact-source, disposable before/after real WinUI light-theme capture.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$Source,
      [Parameter(Mandatory)][string]$Root,
      [Parameter(Mandatory)][string]$Before,
      [Parameter(Mandatory)][string]$After,
      [switch]$ResumeBeforeBuild)
$ErrorActionPreference='Stop'
if($Before -notmatch '^[0-9a-f]{40}$' -or $After -notmatch '^[0-9a-f]{40}$'){throw 'Full exact SHA required'}
$base=[IO.Path]::GetFullPath((Join-Path $env:ProgramData 'personal-control-plane\scratch')).TrimEnd('\')
$canon=[IO.Path]::GetFullPath($Root).TrimEnd('\')
if(-not $canon.StartsWith(($base+'\v-'),[StringComparison]::OrdinalIgnoreCase) -or
 $canon.Substring(($base+'\v-').Length) -notmatch '^[0-9a-f]{12}$'){throw 'Not an owned short path'}
if((Get-Item -LiteralPath $Root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Refuse reparse root'}
if([IO.Path]::GetFullPath($Source) -cne [IO.Path]::GetFullPath((Join-Path $Root 'source'))){throw 'Invalid owned checkout'}
$rev=(& git -C $Source rev-parse HEAD).Trim()
$expected=if($ResumeBeforeBuild){$Before}else{$After}
if($LASTEXITCODE -ne 0 -or $rev -cne $expected){throw 'Exact initial source SHA mismatch'}
if($ResumeBeforeBuild){
 $priorPath=Join-Path $Root 'light-result.json'
 if(-not(Test-Path -LiteralPath $priorPath -PathType Leaf)){throw 'Prior owned failed result missing'}
 $prior=Get-Content -LiteralPath $priorPath -Raw -Encoding UTF8|ConvertFrom-Json
 if($prior.status -cne 'FAIL' -or $prior.stage -cne 'before-light-matrix'){throw 'Prior result does not prove completed baseline Release'}
 if(-not(Test-Path -LiteralPath (Join-Path $Source 'out\winui\Release\flyExplorer.exe') -PathType Leaf)){throw 'Baseline Release EXE absent'}
 Write-Output 'LIGHT_FILTER_VERIFIED_OWNED_BASELINE_RELEASE_REUSE=PASS'
}
& git -C $Source cat-file -e ($Before+'^{commit}')
if($LASTEXITCODE -ne 0){throw 'Before SHA not present in clone'}
$users=@(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" |
 Where-Object {$_.SessionId -gt 0} | ForEach-Object {
  $o=Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
  if($o.ReturnValue -eq 0 -and $o.Sid -match '^S-1-5-21-'){
   [pscustomobject]@{sid=$o.Sid;session=$_.SessionId}
  }
 } | Sort-Object session,sid -Unique)
if($users.Count -ne 1){throw 'One interactive Explorer session required'}
Write-Output ('LIGHT_FILTER_DESKTOP_SESSION='+$users[0].session)
& icacls.exe $Root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*'+$users[0].sid+':(OI)(CI)M')|Out-Null
if($LASTEXITCODE -ne 0){throw 'Owned root ACL failed'}
$images=Join-Path $Root 'images'
New-Item -ItemType Directory -Path $images -Force|Out-Null
$capture=Join-Path $Root 'light-capture.py'
if($ResumeBeforeBuild){
 if(-not(Test-Path -LiteralPath $capture -PathType Leaf)){throw 'Reviewed current test-only capture script not pre-staged'}
 $script=Get-Content -LiteralPath $capture -Raw -Encoding UTF8
 if(-not $script.Contains('Both revisions already support color/icon selectors')){throw 'Resumed capture script is not fixed baseline comparison'}
}else{
 Copy-Item -LiteralPath (Join-Path $Source 'tests\winui\test_filter_light_visual_gui.py') -Destination $capture
}
$worker=Join-Path $Root 'light-worker.ps1'
$result=Join-Path $Root 'light-result.json'
if($ResumeBeforeBuild){Remove-Item -LiteralPath $result -Force -ErrorAction Stop}
$workerText=@'
param([string]$Source,[string]$Capture,[string]$Images,[string]$Result,[string]$Before,[string]$After,[switch]$ResumeBeforeBuild)
$ErrorActionPreference='Stop';$state='FAIL';$stage='preflight';$detail=''
$log=Join-Path (Split-Path -Parent $Result) 'light-build.log'
try {
 Set-Location -LiteralPath $Source
 $env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
 $env:GIT_CONFIG_COUNT='1';$env:GIT_CONFIG_KEY_0='safe.directory';$env:GIT_CONFIG_VALUE_0=$Source
 $null=Get-Command python.exe -ErrorAction Stop
 $stage='capture-syntax'
 & python.exe -X utf8 -m py_compile $Capture
 if($LASTEXITCODE -ne 0){throw 'Python capture syntax failed'}
 foreach($label in @('before','after')){
  $sha=if($label -eq 'before'){$Before}else{$After}
  $stage=$label+'-checkout'
  if($ResumeBeforeBuild -and $label -eq 'before'){
   $actual=(& git -C $Source rev-parse HEAD).Trim()
   if($LASTEXITCODE -ne 0 -or $actual -cne $Before){throw 'Reused baseline source SHA mismatch'}
   if(-not(Test-Path -LiteralPath (Join-Path $Source 'out\winui\Release\flyExplorer.exe') -PathType Leaf)){throw 'Baseline Release binary missing'}
   Add-Content -LiteralPath $log -Value 'LIGHT_FILTER_REUSED_BASELINE_RELEASE=PASS'
  }else{
   $ErrorActionPreference='Continue'
   & git -C $Source checkout --quiet --detach $sha *>&1|Out-File -LiteralPath $log -Append -Encoding UTF8
   $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
   if($rc -ne 0){throw ('Exact checkout failed '+$label)}
   $actual=(& git -C $Source rev-parse HEAD).Trim()
   if($LASTEXITCODE -ne 0 -or $actual -cne $sha){throw ('Revision mismatch '+$label)}
  }
  if($label -eq 'after'){
   $stage='owned-clean-after-runtime'
   $ErrorActionPreference='Continue'
   & cmd.exe /d /c 'clean.bat build' *>&1|Out-File -LiteralPath $log -Append -Encoding UTF8
   $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
   if($rc -ne 0){throw ('Owned clean failed '+$rc)}
   if(Test-Path -LiteralPath (Join-Path $Source 'out')){throw 'Stale out remains'}
  }
  if(-not($ResumeBeforeBuild -and $label -eq 'before')){
   $stage=$label+'-Release-build'
   $ErrorActionPreference='Continue'
   & cmd.exe /d /c 'build.bat Release' *>&1|Out-File -LiteralPath $log -Append -Encoding UTF8
   $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
   if($rc -ne 0){throw ('Release build failed '+$label+' '+$rc)}
  }
  $stage=$label+'-light-matrix'
  $ErrorActionPreference='Continue'
  & python.exe -X utf8 $Capture --source $Source --output $Images --label $label --exact-sha $sha *>&1|Out-File -LiteralPath $log -Append -Encoding UTF8
  $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
  if($rc -ne 0){throw ('Owned real light screenshots failed '+$label+' '+$rc)}
 }
 $stage='matched-light-evidence'
 $b=Get-Content -LiteralPath (Join-Path $Images 'before-light-metadata.json') -Raw -Encoding UTF8|ConvertFrom-Json
 $a=Get-Content -LiteralPath (Join-Path $Images 'after-light-metadata.json') -Raw -Encoding UTF8|ConvertFrom-Json
 if($b.revision -cne $Before -or $a.revision -cne $After){throw 'Image source SHA mismatch'}
 if($b.binary_sha256 -ceq $a.binary_sha256){throw 'Before and after exe hashes identical'}
 foreach($key in @('theme','view','configuration','dpi')){if($b.$key -cne $a.$key){throw ('Unmatched '+$key)}}
 foreach($key in @('window','desktop','crop')){if(($b.$key -join ',') -cne ($a.$key -join ',')){throw ('Unmatched '+$key)}}
 if($b.theme -cne 'light' -or $b.images.Count -ne 8 -or $a.images.Count -ne 8 -or $b.montages.Count -ne 2 -or $a.montages.Count -ne 2){throw 'Missing light palette matrix evidence'}
 foreach($name in @('before-light-normal-montage.png','before-light-selected-focus-montage.png','after-light-normal-montage.png','after-light-selected-focus-montage.png')){
  $image=Join-Path $Images $name
  if(-not(Test-Path -LiteralPath $image -PathType Leaf)){throw ('PNG absent '+$name)}
  $size=(Get-Item -LiteralPath $image).Length
  if($size -lt 1700 -or $size -gt 900000){throw ('PNG bytes out of bounds '+$name)}
 }
 $stage='complete';$state='PASS';$detail='Matched actual light pixel matrix ready for independent review'
}catch{$detail=$_.Exception.Message}
finally{@{status=$state;stage=$stage;detail=$detail}|ConvertTo-Json|Set-Content -LiteralPath $Result -Encoding UTF8}
if($state -ne 'PASS'){exit 1}
'@
Set-Content -LiteralPath $worker -Value $workerText -Encoding UTF8
$name='PcpFlyLightVisual-'+[guid]::NewGuid().ToString('N')
$registered=$false;$accepted=$false
try {
 $pwsh=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $args='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$worker+'" -Source "'+$Source+'" -Capture "'+$capture+'" -Images "'+$images+'" -Result "'+$result+'" -Before "'+$Before+'" -After "'+$After+'"'
 if($ResumeBeforeBuild){$args+=' -ResumeBeforeBuild'}
 Register-ScheduledTask -TaskName $name -Action (New-ScheduledTaskAction -Execute $pwsh -Argument $args) -Principal (New-ScheduledTaskPrincipal -UserId $users[0].sid -LogonType Interactive -RunLevel Limited) -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 18)) -Force|Out-Null
 $registered=$true
 Start-ScheduledTask -TaskName $name
 $until=(Get-Date).AddMinutes(15)
 while(-not(Test-Path -LiteralPath $result -PathType Leaf) -and (Get-Date)-lt $until){Start-Sleep -Seconds 5}
 if(-not(Test-Path -LiteralPath $result -PathType Leaf)){throw 'Light visual matrix worker timeout'}
 $outcome=Get-Content -LiteralPath $result -Raw -Encoding UTF8|ConvertFrom-Json
 Write-Output ('LIGHT_FILTER_RUN_STATUS='+$outcome.status+' STAGE='+$outcome.stage+' DETAIL='+$outcome.detail)
 if($outcome.status -ne 'PASS'){
  $log=Join-Path $Root 'light-build.log'
  if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 55|ForEach-Object{Write-Output ('LIGHT_FILTER_LOG '+$_)}}
  throw ('Real visual matrix failed: '+$outcome.detail)
 }
 $meta=Get-Content -LiteralPath (Join-Path $images 'after-light-metadata.json') -Raw -Encoding UTF8|ConvertFrom-Json
 Write-Output ('LIGHT_FILTER_MATCHED_DPI='+$meta.dpi+' WINDOW='+($meta.window -join ','))
 foreach($entry in @('before-light-normal-montage.png','before-light-selected-focus-montage.png','after-light-normal-montage.png','after-light-selected-focus-montage.png')){
  $img=Join-Path $images $entry
  $key=($entry -replace '\.png$','').ToUpperInvariant().Replace('-','_')
  Write-Output ('LIGHT_FILTER_IMAGE_'+$key+'_B64='+[Convert]::ToBase64String([IO.File]::ReadAllBytes($img)))
 }
 Write-Output 'LIGHT_FILTER_ACTUAL_IMAGES=PASS PIXEL_REVIEW=REQUIRED'
 $accepted=$true
}finally{
 if($registered){
  $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if($task -and $task.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue}
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 }
 if($accepted){Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction Stop;Write-Output 'LIGHT_FILTER_OWNED_CLEANUP=PASS'}
 else{Write-Output ('LIGHT_FILTER_EVIDENCE_RETAINED='+$Root)}
}

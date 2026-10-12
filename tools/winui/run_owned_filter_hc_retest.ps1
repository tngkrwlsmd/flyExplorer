# Exact-revision, test-owned Windows High Contrast filter appearance retest.
# Uses the existing Settings UI setup/restore, no registry/theme shortcuts.
param([string]$Source,[string]$Root,[string]$Before,[string]$After,[switch]$ResumeExisting)
$ErrorActionPreference='Stop'
if($Before -notmatch '^[0-9a-f]{40}$' -or $After -notmatch '^[0-9a-f]{40}$'){throw 'Exact pinned SHA required'}
$base=[IO.Path]::GetFullPath((Join-Path $env:ProgramData 'personal-control-plane\scratch')).TrimEnd('\')
$canonical=[IO.Path]::GetFullPath($Root).TrimEnd('\')
if(-not $canonical.StartsWith($base+'\v-',[StringComparison]::OrdinalIgnoreCase) -or $canonical.Substring(($base+'\v-').Length) -notmatch '^[0-9a-f]{12}$'){throw 'Invalid test-owned path'}
if((Get-Item -LiteralPath $Root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked scratch root forbidden'}
$revision=(& git -C $Source rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $revision -cne $After){throw 'Exact current source revision mismatch'}
& git -C $Source cat-file -e ($Before+'^{commit}')
if($LASTEXITCODE -ne 0){throw 'Exact baseline revision unavailable'}
$users=@(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Where-Object {$_.SessionId -gt 0} | ForEach-Object {$o=Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid;if($o.ReturnValue -eq 0 -and $o.Sid -match '^S-1-5-21-'){[pscustomobject]@{sid=$o.Sid;session=$_.SessionId}}} | Sort-Object session,sid -Unique)
if($users.Count -ne 1){throw 'One dedicated interactive Windows user required'}
& icacls.exe $Root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*'+$users[0].sid+':(OI)(CI)M') | Out-Null
if($LASTEXITCODE -ne 0){throw 'Unable to grant owned scratch access'}
Write-Output ('HC_FILTER_SESSION='+$users[0].session)
if($ResumeExisting){
 $previous=Join-Path $Root 'result.json'
 if(-not(Test-Path -LiteralPath $previous -PathType Leaf)){throw 'No previously failed owned HC acceptance'}
 $old=Get-Content -LiteralPath $previous -Raw -Encoding UTF8|ConvertFrom-Json
 if($old.status -cne 'FAIL' -or $old.stage -cne 'actual-HighContrast-settings-and-GUI'){throw 'Previous stage is not verified after both Release builds'}
 $contrastResult=Get-Content -LiteralPath (Join-Path $Root 'high-contrast-result.json') -Raw -Encoding UTF8|ConvertFrom-Json
 if($contrastResult.original_high_contrast -ne $contrastResult.final_high_contrast -or $contrastResult.stages.CLEANUP -cne 'PASS'){throw 'Previous HC theme state was not restored'}
 $baseline=Join-Path $Root 'baseline'
 $original=(& git -C $baseline rev-parse HEAD).Trim()
 if($LASTEXITCODE -ne 0 -or $original -cne $Before){throw 'Existing exact baseline worktree mismatch'}
 foreach($exe in @((Join-Path $baseline 'out\winui\Release\flyExplorer.exe'),(Join-Path $Source 'out\winui\Release\flyExplorer.exe'))){
  if(-not(Test-Path -LiteralPath $exe -PathType Leaf)){throw ('Trusted prebuilt Release binary missing '+$exe)}
 }
 Remove-Item -LiteralPath $previous -Force -ErrorAction Stop
 Write-Output 'HC_FILTER_EXACT_OWNED_RELEASE_REUSE=PASS'
}
$worker=Join-Path $Root 'worker.ps1'
$result=Join-Path $Root 'result.json'
$workerText=@'
param([string]$Source,[string]$Root,[string]$Before,[string]$After,[string]$Result,[switch]$ResumeExisting)
$ErrorActionPreference='Stop'
$state='FAIL';$stage='preflight';$detail='';$ime='NOT_RUN'
$log=Join-Path $Root 'hc-build.log'
try{
 $env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
 $env:GIT_CONFIG_COUNT='1';$env:GIT_CONFIG_KEY_0='safe.directory';$env:GIT_CONFIG_VALUE_0=$Source
 $baseline=Join-Path $Root 'baseline'
 if(-not $ResumeExisting){
 $stage='baseline-detached-worktree'
 $ErrorActionPreference='Continue'
 & git -C $Source worktree add --quiet --detach $baseline $Before *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
 $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($rc -ne 0){throw ('Owned baseline checkout failed '+$rc)}
 $env:GIT_CONFIG_COUNT='2';$env:GIT_CONFIG_KEY_1='safe.directory';$env:GIT_CONFIG_VALUE_1=$baseline
 $rev=(& git -C $baseline rev-parse HEAD).Trim()
 if($rev -cne $Before){throw 'Baseline checkout SHA mismatch'}
 $stage='baseline-Release'
 Set-Location -LiteralPath $baseline
 $ErrorActionPreference='Continue'
 & cmd.exe /d /c 'build.bat Release' *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
 $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($rc -ne 0){throw ('Baseline Release failed '+$rc)}
 $stage='after-Release'
 Set-Location -LiteralPath $Source
 $rev=(& git -C $Source rev-parse HEAD).Trim()
 if($rev -cne $After){throw 'Current source SHA moved'}
 $ErrorActionPreference='Continue'
 & cmd.exe /d /c 'build.bat Release' *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
 $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($rc -ne 0){throw ('Current Release failed '+$rc)}
 }else{
  $env:GIT_CONFIG_COUNT='2';$env:GIT_CONFIG_KEY_1='safe.directory';$env:GIT_CONFIG_VALUE_1=$baseline
  $rev=(& git -C $baseline rev-parse HEAD).Trim()
  if($LASTEXITCODE -ne 0 -or $rev -cne $Before){throw 'Reused baseline provenance mismatch'}
  foreach($exe in @((Join-Path $baseline 'out\winui\Release\flyExplorer.exe'),(Join-Path $Source 'out\winui\Release\flyExplorer.exe'))){
   if(-not(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'Reused Release exe missing'}
  }
  Add-Content -LiteralPath $log -Value 'HC_FILTER_TRUSTED_PREBUILT_BASELINE_AND_CURRENT=PASS'
 }
 $stage='physical-Korean-IME'
 $ErrorActionPreference='Continue'
 & python.exe -X utf8 (Join-Path $Source 'tests\winui\test_filter_korean_ime_gui.py') *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
 $imeCode=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($imeCode -eq 0){$ime='PASS'}else{$ime='NOT_ACCEPTED'}
 Add-Content -LiteralPath $log -Value ('KOREAN_IME_PHYSICAL_TEST_RESULT='+$ime)
 $stage='actual-HighContrast-settings-and-GUI'
 $old=Join-Path $baseline 'out\winui\Release\flyExplorer.exe'
 $new=Join-Path $Source 'out\winui\Release\flyExplorer.exe'
 if(-not(Test-Path $old -PathType Leaf) -or -not(Test-Path $new -PathType Leaf)){throw 'Missing full Release binary'}
 $hc=Join-Path $Source 'tools\winui\high_contrast_acceptance.py'
 $ErrorActionPreference='Continue'
 & python.exe -X utf8 $hc --configuration Release --baseline-exe $old --candidate-exe $new --evidence-dir $Root *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
 $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($rc -ne 0){throw ('Owned Windows HC UI acceptance failed '+$rc)}
 $accept=Get-Content -LiteralPath (Join-Path $Root 'high-contrast-result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 foreach($key in @('RUNNER_SETUP','BASELINE','CANDIDATE_GUI','CLEANUP')){
  if($accept.stages.$key -cne 'PASS'){throw ('HC step missing PASS '+$key)}
 }
 if($accept.original_high_contrast -ne $accept.final_high_contrast){throw 'System contrast theme was not restored'}
 $stage='verify-real-HC-color-pixels'
 $dir=Join-Path $Source 'logs\high-contrast'
 foreach($prefix in @('baseline-high-contrast','candidate-high-contrast')){
  foreach($color in @('blue','green','amber','red')){
   $path=Join-Path $dir ($prefix+'-filter-'+$color+'.png')
   if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw ('Real HC screenshot missing '+$prefix+' '+$color)}
   if((Get-Item -LiteralPath $path).Length -lt 1500){throw ('Real HC PNG invalid '+$color)}
  }
 }
 $state='PASS';$stage='complete';$detail='Both HC WinUI revisions, four style pixels and restored contrast theme'
}catch{$detail=$_.Exception.Message}
finally{@{status=$state;stage=$stage;detail=$detail;ime=$ime}|ConvertTo-Json|Set-Content -LiteralPath $Result -Encoding UTF8}
if($state -ne 'PASS'){exit 1}
'@
Set-Content -LiteralPath $worker -Value $workerText -Encoding UTF8
$name='PcpFlyHCFilter-'+[guid]::NewGuid().ToString('N')
$registered=$false;$ok=$false
try{
 $pwsh=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $arguments='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$worker+'" -Source "'+$Source+'" -Root "'+$Root+'" -Before "'+$Before+'" -After "'+$After+'" -Result "'+$result+'"'
 if($ResumeExisting){$arguments+=' -ResumeExisting'}
 Register-ScheduledTask -TaskName $name -Action (New-ScheduledTaskAction -Execute $pwsh -Argument $arguments) -Principal (New-ScheduledTaskPrincipal -UserId $users[0].sid -LogonType Interactive -RunLevel Limited) -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 20)) -Force | Out-Null
 $registered=$true
 Start-ScheduledTask -TaskName $name
 $until=(Get-Date).AddMinutes(18)
 while(-not(Test-Path -LiteralPath $result -PathType Leaf) -and (Get-Date)-lt $until){Start-Sleep -Seconds 5}
 if(-not(Test-Path -LiteralPath $result -PathType Leaf)){throw 'Bounded HC acceptance timeout: restore state before any retry'}
 $done=Get-Content -LiteralPath $result -Raw -Encoding UTF8|ConvertFrom-Json
 Write-Output ('HC_FILTER_STATUS='+$done.status+' STAGE='+$done.stage+' DETAIL='+$done.detail+' IME='+$done.ime)
 if($done.status -ne 'PASS'){
  $log=Join-Path $Root 'hc-build.log'
  if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 44|ForEach-Object{Write-Output ('HC_FILTER_LOG '+$_)}}
  throw ('High Contrast styled rows were not accepted: '+$done.detail)
 }
 $dir=Join-Path $Source 'logs\high-contrast'
 foreach($side in @('baseline','candidate')){
  foreach($color in @('blue','green','amber','red')){
   $path=Join-Path $dir ($side+'-high-contrast-filter-'+$color+'.png')
   if($color -eq 'blue' -or $color -eq 'red'){
    if((Get-Item -LiteralPath $path).Length -gt 220000){throw 'Bounded screenshot size exceeded'}
    Write-Output ('HC_FILTER_'+$side.ToUpperInvariant()+'_'+$color.ToUpperInvariant()+'_B64='+[Convert]::ToBase64String([IO.File]::ReadAllBytes($path)))
   }
  }
 }
 Write-Output 'HC_FILTER_FOUR_STYLES_ACTUAL_PIXELS=PASS REVIEW_REQUIRED=TRUE'
 $ok=$true
}finally{
 if($registered){
  $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if($task -and $task.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue}
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 }
 if($ok){Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction Stop;Write-Output 'HC_FILTER_OWNED_CLEANUP=PASS'}
 else{Write-Output ('HC_FILTER_OWNED_EVIDENCE_RETAINED='+$Root)}
}

# Exact-source owned WinUI baseline/current filter pixels; outputs images for review, not acceptance.
[CmdletBinding()]
param(
 [Parameter(Mandatory)][string]$Source,
 [Parameter(Mandatory)][string]$Root,
 [Parameter(Mandatory)][string]$Before,
 [Parameter(Mandatory)][string]$After,
 [switch]$ResumeBeforeCapture
)
$ErrorActionPreference='Stop'
if($Before -notmatch '^[0-9a-f]{40}$' -or $After -notmatch '^[0-9a-f]{40}$'){throw 'Full exact SHA required'}
$base=[IO.Path]::GetFullPath((Join-Path $env:ProgramData 'personal-control-plane\scratch')).TrimEnd('\')
$canonical=[IO.Path]::GetFullPath($Root).TrimEnd('\')
if(-not $canonical.StartsWith($base+'\v-',[StringComparison]::OrdinalIgnoreCase) -or
 $canonical.Substring(($base+'\v-').Length) -notmatch '^[0-9a-f]{12}$'){
 throw 'Refusing a non-owned visual scratch directory'
}
if((Get-Item -LiteralPath $Root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Refusing root reparse point'}
if([IO.Path]::GetFullPath($Source) -cne [IO.Path]::GetFullPath((Join-Path $Root 'source'))){throw 'Wrong owned source'}
$revision=(& git -C $Source rev-parse HEAD).Trim()
$expected=if($ResumeBeforeCapture){$Before}else{$After}
if($LASTEXITCODE -ne 0 -or $revision -cne $expected){throw 'Exact initial revision mismatch'}
if($ResumeBeforeCapture){
 $oldResult=Join-Path $Root 'result.json'
 if(-not(Test-Path -LiteralPath $oldResult -PathType Leaf)){throw 'No prior owned failed result to resume'}
 $prior=Get-Content -LiteralPath $oldResult -Raw -Encoding UTF8 | ConvertFrom-Json
 if($prior.status -cne 'FAIL' -or $prior.stage -cne 'before-actual-capture'){throw 'Prior owned result does not prove complete baseline build'}
 $binary=Join-Path $Source 'out\winui\Release\flyExplorer.exe'
 if(-not(Test-Path -LiteralPath $binary -PathType Leaf)){throw 'Baseline Release exe absent'}
 Write-Output 'FILTER_VISUAL_PREBUILT_BASELINE_VERIFIED=PASS'
}
& git -C $Source cat-file -e ($Before+'^{commit}')
if($LASTEXITCODE -ne 0){throw 'Baseline revision not in bounded clone'}
$users=@(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Where-Object {$_.SessionId -gt 0} | ForEach-Object {
 $owner=Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
 if($owner.ReturnValue -eq 0 -and $owner.Sid -match '^S-1-5-21-'){
  [pscustomobject]@{sid=$owner.Sid;session=$_.SessionId}
 }
} | Sort-Object session,sid -Unique)
if($users.Count -ne 1){throw 'Exactly one Explorer user session required'}
Write-Output ('FILTER_VISUAL_DESKTOP_SESSION='+$users[0].session)
& icacls.exe $Root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*'+$users[0].sid+':(OI)(CI)M') | Out-Null
if($LASTEXITCODE -ne 0){throw 'Owned workspace ACL failed'}
$images=Join-Path $Root 'images'
New-Item -ItemType Directory -Path $images -Force | Out-Null
$capture=Join-Path $Root 'capture.py'
if($ResumeBeforeCapture){
 & git -C $Source checkout --quiet --detach $After
 if($LASTEXITCODE -ne 0){throw 'Resume target checkout failed'}
 Copy-Item -LiteralPath (Join-Path $Source 'tests\winui\test_filter_style_visual_capture_gui.py') -Destination $capture -Force
 & git -C $Source checkout --quiet --detach $Before
 if($LASTEXITCODE -ne 0){throw 'Resume baseline checkout failed'}
} else {
 Copy-Item -LiteralPath (Join-Path $Source 'tests\winui\test_filter_style_visual_capture_gui.py') -Destination $capture
}
$worker=Join-Path $Root 'worker.ps1'
$result=Join-Path $Root 'result.json'
if($ResumeBeforeCapture){Remove-Item -LiteralPath $result -Force -ErrorAction Stop}
$workerCode=@'
param([string]$Source,[string]$Capture,[string]$Images,[string]$Result,[string]$Before,[string]$After,[switch]$ResumeBeforeCapture)
$ErrorActionPreference='Stop';$status='FAIL';$stage='preflight';$detail=''
$log=Join-Path (Split-Path -Parent $Result) 'visual-build.log'
try{
 Set-Location -LiteralPath $Source
 $env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
 $env:GIT_CONFIG_COUNT='1';$env:GIT_CONFIG_KEY_0='safe.directory';$env:GIT_CONFIG_VALUE_0=$Source
 $null=Get-Command python.exe -ErrorAction Stop
 $stage='capture-syntax'
 & python.exe -X utf8 -m py_compile $Capture
 if($LASTEXITCODE -ne 0){throw 'Capture script syntax failed'}
 foreach($label in @('before','after')){
  $sha=if($label -eq 'before'){$Before}else{$After}
  $stage=$label+'-checkout'
  if($ResumeBeforeCapture -and $label -eq 'before'){
   $current=(& git -C $Source rev-parse HEAD).Trim()
   if($LASTEXITCODE -ne 0 -or $current -cne $Before){throw 'Resume baseline SHA mismatch'}
   if(-not(Test-Path -LiteralPath (Join-Path $Source 'out\winui\Release\flyExplorer.exe'))){throw 'Previously built baseline binary missing'}
   Add-Content -LiteralPath $log -Value 'FILTER_VISUAL_REUSED_BASELINE_RELEASE=PASS'
  }else{
   $ErrorActionPreference='Continue'
   & git -C $Source checkout --quiet --detach $sha *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
   $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
   if($rc -ne 0){throw ($label+' checkout exit '+$rc)}
   $current=(& git -C $Source rev-parse HEAD).Trim()
   if($LASTEXITCODE -ne 0 -or $current -cne $sha){throw ($label+' checkout SHA mismatch')}
   $stage=$label+'-Release-build'
   $ErrorActionPreference='Continue'
   & cmd.exe /d /c 'build.bat Release' *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
   $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
   if($rc -ne 0){throw ($label+' Release build exit '+$rc)}
  }
  $stage=$label+'-actual-capture'
  $ErrorActionPreference='Continue'
  & python.exe -X utf8 $Capture --source $Source --label $label --source-sha $sha --output $Images *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
  $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
  if($rc -ne 0){throw ($label+' actual capture exit '+$rc)}
 }
 $stage='matched-conditions'
 $b=Get-Content -LiteralPath (Join-Path $Images 'before-metadata.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $a=Get-Content -LiteralPath (Join-Path $Images 'after-metadata.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 if($b.revision -cne $Before -or $a.revision -cne $After){throw 'Revision metadata mismatch'}
 if($b.binary_sha256 -ceq $a.binary_sha256){throw 'Binary comparison hashes unexpectedly equal'}
 foreach($f in @('dpi','theme','configuration')){
  if($a.$f -cne $b.$f){throw ('Matched pixel condition differs: '+$f)}
 }
 foreach($f in @('window','desktop','preview_rect_relative_to_window')){
  if(($a.$f -join ',') -cne ($b.$f -join ',')){throw ('Matched geometry differs: '+$f)}
 }
 foreach($label in @('before','after')){
  $png=Join-Path $Images ($label+'-preview.png')
  if(-not(Test-Path -LiteralPath $png -PathType Leaf)){throw ('Missing real preview: '+$label)}
  $size=(Get-Item -LiteralPath $png).Length
  if($size -lt 1800 -or $size -gt 650000){throw ('Bounded preview size mismatch: '+$size)}
 }
 $status='PASS';$stage='complete';$detail='Matched real screenshots captured; independent pixel review required'
}catch{$detail=$_.Exception.Message}
finally{@{status=$status;stage=$stage;detail=$detail}|ConvertTo-Json|Set-Content -LiteralPath $Result -Encoding UTF8}
if($status -ne 'PASS'){exit 1}
'@
Set-Content -LiteralPath $worker -Value $workerCode -Encoding UTF8
$name='PcpFlyFilterVisual-'+[guid]::NewGuid().ToString('N')
$registered=$false;$success=$false
try{
 $exe=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $arguments='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$worker+'" -Source "'+$Source+'" -Capture "'+$capture+'" -Images "'+$images+'" -Result "'+$result+'" -Before "'+$Before+'" -After "'+$After+'"'
 if($ResumeBeforeCapture){$arguments+=' -ResumeBeforeCapture'}
 $action=New-ScheduledTaskAction -Execute $exe -Argument $arguments
 $principal=New-ScheduledTaskPrincipal -UserId $users[0].sid -LogonType Interactive -RunLevel Limited
 $settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 16)
 Register-ScheduledTask -TaskName $name -Action $action -Principal $principal -Settings $settings -Force | Out-Null
 $registered=$true
 Start-ScheduledTask -TaskName $name
 $deadline=(Get-Date).AddMinutes(13)
 while(-not(Test-Path -LiteralPath $result -PathType Leaf) -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 5}
 if(-not(Test-Path -LiteralPath $result -PathType Leaf)){throw 'Owned visual worker timed out'}
 $outcome=Get-Content -LiteralPath $result -Raw -Encoding UTF8 | ConvertFrom-Json
 Write-Output ('FILTER_VISUAL_RUN_STATUS='+$outcome.status+' STAGE='+$outcome.stage+' DETAIL='+$outcome.detail)
 if($outcome.status -cne 'PASS'){
  $log=Join-Path $Root 'visual-build.log'
  if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 40 | ForEach-Object {Write-Output ('FILTER_VISUAL_LOG '+$_)}}
  throw ('Visual worker failed: '+$outcome.detail)
 }
 $metadata=Get-Content -LiteralPath (Join-Path $images 'after-metadata.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 Write-Output ('FILTER_VISUAL_MATCHED_DPI='+$metadata.dpi+' WINDOW='+($metadata.window -join ','))
 foreach($label in @('before','after')){
  $png=Join-Path $images ($label+'-preview.png')
  Write-Output ('FILTER_VISUAL_PREVIEW_'+$label.ToUpperInvariant()+'_B64='+[Convert]::ToBase64String([IO.File]::ReadAllBytes($png)))
 }
 Write-Output 'FILTER_VISUAL_CAPTURE_PAIR=PASS PIXEL_REVIEW=REQUIRED'
 $success=$true
}finally{
 if($registered){
  $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if($task -and $task.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue}
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 }
 if($success){Remove-Item -LiteralPath $Root -Recurse -Force;Write-Output 'FILTER_VISUAL_OWNED_CLEANUP=PASS'}
 else{Write-Output ('FILTER_VISUAL_OWNED_EVIDENCE_RETAINED='+$Root)}
}

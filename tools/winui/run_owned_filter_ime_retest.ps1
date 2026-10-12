# Test-owned physical Korean IME 2-beolsik composition on WinUI Release.
# Does not change machine language lists, system DPI, Narrator, or HKCU settings.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$Source,
      [Parameter(Mandatory)][string]$Root,
      [Parameter(Mandatory)][string]$Expected)
$ErrorActionPreference='Stop'
if($Expected -notmatch '^[0-9a-f]{40}$'){throw 'Exact commit SHA required'}
$base=[IO.Path]::GetFullPath((Join-Path $env:ProgramData 'personal-control-plane\scratch')).TrimEnd('\')
$canon=[IO.Path]::GetFullPath($Root).TrimEnd('\')
if(-not $canon.StartsWith($base+'\v-',[StringComparison]::OrdinalIgnoreCase) -or
 $canon.Substring(($base+'\v-').Length) -notmatch '^[0-9a-f]{12}$'){
 throw 'Non-test-owned path'
}
if((Get-Item -LiteralPath $Root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked directory'}
if([IO.Path]::GetFullPath($Source) -cne [IO.Path]::GetFullPath((Join-Path $Root 'source'))){throw 'Wrong owned checkout'}
$sha=(& git -C $Source rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $sha -cne $Expected){throw 'Owned source SHA mismatch'}
$users=@(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'"|Where-Object{$_.SessionId -gt 0}|ForEach-Object{
 $o=Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
 if($o.ReturnValue -eq 0 -and $o.Sid -match '^S-1-5-21-'){
  [pscustomobject]@{sid=$o.Sid;session=$_.SessionId}
 }
}|Sort-Object session,sid -Unique)
if($users.Count -ne 1){throw 'Single interactive desktop user required'}
& icacls.exe $Root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*'+$users[0].sid+':(OI)(CI)M')|Out-Null
if($LASTEXITCODE -ne 0){throw 'Owned ACL failed'}
Write-Output ('IME_TEST_SESSION='+$users[0].session)
$worker=Join-Path $Root 'ime-worker.ps1'
$result=Join-Path $Root 'ime-result.json'
$code=@'
param([string]$Source,[string]$Result,[string]$Expected)
$ErrorActionPreference='Stop';$status='FAIL';$stage='preflight';$detail=''
$log=Join-Path (Split-Path -Parent $Result) 'ime-build.log'
try {
 Set-Location -LiteralPath $Source
 $env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
 $env:GIT_CONFIG_COUNT='1';$env:GIT_CONFIG_KEY_0='safe.directory';$env:GIT_CONFIG_VALUE_0=$Source
 $actual=(& git rev-parse HEAD).Trim()
 if($LASTEXITCODE -ne 0 -or $actual -cne $Expected){throw 'Worker source SHA mismatch'}
 $stage='python-syntax'
 & python.exe -X utf8 -m py_compile tests/winui/test_filter_korean_ime_gui.py
 if($LASTEXITCODE -ne 0){throw 'IME harness Python syntax failed'}
 $stage='Release-build'
 $ErrorActionPreference='Continue'
 & cmd.exe /d /c 'build.bat Release' *>&1|Out-File -LiteralPath $log -Append -Encoding UTF8
 $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($rc -ne 0){throw ('Release build failed '+$rc)}
 $stage='physical-Korean-IME'
 $ErrorActionPreference='Continue'
 & python.exe -X utf8 tests/winui/test_filter_korean_ime_gui.py *>&1|Out-File -LiteralPath $log -Append -Encoding UTF8
 $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($rc -ne 0){throw ('Physical composition not accepted exit '+$rc)}
 $body=Get-Content -LiteralPath $log -Raw -Encoding UTF8
 if(-not $body.Contains('KOREAN_IME_ACTUAL_PHYSICAL_COMPOSITION_AND_SAVE=PASS')){
  throw 'Missing actual Hangul composition + durable save acceptance marker'
 }
 $stage='complete';$status='PASS';$detail='Physical Korean 2-beolsik composition and persistence'
}catch{$detail=$_.Exception.Message}
finally{@{status=$status;stage=$stage;detail=$detail}|ConvertTo-Json|Set-Content -LiteralPath $Result -Encoding UTF8}
if($status -ne 'PASS'){exit 1}
'@
Set-Content -LiteralPath $worker -Value $code -Encoding UTF8
$name='PcpFlyKoreanIME-'+[guid]::NewGuid().ToString('N')
$registered=$false;$pass=$false
try{
 $exe=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $args='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$worker+'" -Source "'+$Source+'" -Result "'+$result+'" -Expected "'+$Expected+'"'
 Register-ScheduledTask -TaskName $name -Action (New-ScheduledTaskAction -Execute $exe -Argument $args) -Principal (New-ScheduledTaskPrincipal -UserId $users[0].sid -LogonType Interactive -RunLevel Limited) -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 12)) -Force|Out-Null
 $registered=$true
 Start-ScheduledTask -TaskName $name
 $deadline=(Get-Date).AddMinutes(10)
 while(-not(Test-Path -LiteralPath $result -PathType Leaf) -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 4}
 if(-not(Test-Path -LiteralPath $result -PathType Leaf)){throw 'Owned physical IME worker timed out'}
 $outcome=Get-Content -LiteralPath $result -Raw -Encoding UTF8|ConvertFrom-Json
 Write-Output ('KOREAN_IME_RUN_STATUS='+$outcome.status+' STAGE='+$outcome.stage+' DETAIL='+$outcome.detail)
 $log=Join-Path $Root 'ime-build.log'
 if(Test-Path -LiteralPath $log){
  Get-Content -LiteralPath $log -Tail 34|ForEach-Object{Write-Output ('KOREAN_IME_LOG '+$_)}
 }
 if($outcome.status -ne 'PASS'){throw ('Physical IME test not accepted: '+$outcome.detail)}
 Write-Output 'KOREAN_IME_PHYSICAL_ACCEPTANCE=PASS'
 $pass=$true
}finally{
 if($registered){
  $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if($task -and $task.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue}
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 }
 if($pass){Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction Stop;Write-Output 'KOREAN_IME_OWNED_CLEANUP=PASS'}
 else{Write-Output ('KOREAN_IME_DIAG_EVIDENCE_RETAINED='+$Root)}
}

# Owned native Win32 EDIT physical Korean IME capability diagnostic.
# Reuse the already built failing IME test workspace, not a product rebuild.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$Source,
      [Parameter(Mandatory)][string]$Root,
      [Parameter(Mandatory)][string]$Expected,
      [switch]$Independent)
$ErrorActionPreference='Stop'
if($Expected -notmatch '^[0-9a-f]{40}$'){throw 'Exact SHA required'}
$base=[IO.Path]::GetFullPath((Join-Path $env:ProgramData 'personal-control-plane\scratch')).TrimEnd('\')
$canon=[IO.Path]::GetFullPath($Root).TrimEnd('\')
if(-not $canon.StartsWith($base+'\v-',[StringComparison]::OrdinalIgnoreCase) -or
 $canon.Substring(($base+'\v-').Length) -notmatch '^[0-9a-f]{12}$'){throw 'Not an owned path'}
if((Get-Item -LiteralPath $Root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked owned path forbidden'}
if([IO.Path]::GetFullPath($Source) -cne [IO.Path]::GetFullPath((Join-Path $Root 'source'))){throw 'Wrong source checkout'}
$revision=(& git -C $Source rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $revision -cne $Expected){throw 'Source SHA mismatch'}
if(-not $Independent){
 $prior=Get-Content -LiteralPath (Join-Path $Root 'ime-result.json') -Raw -Encoding UTF8|ConvertFrom-Json
 if($prior.status -cne 'FAIL' -or $prior.stage -cne 'physical-Korean-IME'){throw 'Prior IME failure provenance missing'}
}
$users=@(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'"|Where-Object{$_.SessionId -gt 0}|ForEach-Object{
 $o=Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
 if($o.ReturnValue -eq 0 -and $o.Sid -match '^S-1-5-21-'){[pscustomobject]@{sid=$o.Sid;session=$_.SessionId}}
}|Sort-Object sid,session -Unique)
if($users.Count -ne 1){throw 'One logged-in owner required'}
Write-Output ('IME_BASELINE_DESKTOP_SESSION='+$users[0].session)
$log=Join-Path $Root 'ime-native-baseline.log'
$result=Join-Path $Root 'ime-native-baseline-result.json'
$worker=Join-Path $Root 'native-ime-worker.ps1'
$workerText=@'
param([string]$Source,[string]$Log,[string]$Result)
$ErrorActionPreference='Stop';$status='FAIL';$detail=''
try {
 Set-Location -LiteralPath $Source
 $env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
 $ErrorActionPreference='Continue'
 & python.exe -X utf8 -m py_compile tests/winui/test_windows_korean_ime_host_baseline.py *>&1 |
   Out-File -LiteralPath $Log -Append -Encoding UTF8
 $rc=$LASTEXITCODE
 if($rc -ne 0){throw 'Native host baseline syntax failed'}
 & python.exe -X utf8 tests/winui/test_windows_korean_ime_host_baseline.py *>&1|
  Out-File -LiteralPath $Log -Append -Encoding UTF8
 $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
 if($rc -ne 0){throw ('Native Win32 EDIT baseline failed '+$rc)}
 $content=Get-Content -LiteralPath $Log -Raw -Encoding UTF8
 if(-not $content.Contains('KOREAN_IME_BASELINE_DIAGNOSTIC=PASS')){throw 'No baseline diagnostic marker'}
 $status='PASS';$detail='Native owned Win32 EDIT comparison completed'
}catch{$detail=$_.Exception.Message}
finally{@{status=$status;detail=$detail}|ConvertTo-Json|Set-Content -LiteralPath $Result -Encoding UTF8}
if($status -ne 'PASS'){exit 1}
'@
Set-Content -LiteralPath $worker -Value $workerText -Encoding UTF8
$name='PcpFlyNativeIME-'+[guid]::NewGuid().ToString('N')
$registered=$false;$success=$false
try{
 $p=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $args='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$worker+'" -Source "'+$Source+'" -Log "'+$log+'" -Result "'+$result+'"'
 Register-ScheduledTask -TaskName $name -Action (New-ScheduledTaskAction -Execute $p -Argument $args) -Principal (New-ScheduledTaskPrincipal -UserId $users[0].sid -LogonType Interactive -RunLevel Limited) -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 3)) -Force|Out-Null
 $registered=$true;Start-ScheduledTask -TaskName $name
 $until=(Get-Date).AddSeconds(145)
 while(-not(Test-Path -LiteralPath $result -PathType Leaf) -and (Get-Date) -lt $until){Start-Sleep -Seconds 3}
 if(-not(Test-Path -LiteralPath $result -PathType Leaf)){throw 'Native owned IME diagnostic timeout'}
 $outcome=Get-Content -LiteralPath $result -Raw -Encoding UTF8|ConvertFrom-Json
 Write-Output ('IME_NATIVE_BASELINE_STATUS='+$outcome.status+' DETAIL='+$outcome.detail)
 if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 30 | ForEach-Object{Write-Output ('IME_NATIVE_BASELINE_LOG '+$_)}}
 if($outcome.status -ne 'PASS'){throw ('Native baseline probe failed: '+$outcome.detail)}
 $success=$true
}finally{
 if($registered){
  $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if($task -and $task.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue}
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 }
 if($success){Write-Output 'IME_NATIVE_BASELINE_DIAGNOSTIC_CAPTURED=PASS'}
 else{Write-Output ('IME_NATIVE_EVIDENCE_RETAINED='+$Root)}
}

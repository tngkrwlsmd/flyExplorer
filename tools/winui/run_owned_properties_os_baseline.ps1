# Interactive test for a disposable Windows Explorer Properties window.
# Only the test-owned Explorer HWND and property sheet may be controlled.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Source)
$ErrorActionPreference='Stop'
if(-not (Test-Path -LiteralPath (Join-Path $Source 'tests\winui\test_owned_explorer_properties_baseline.py') -PathType Leaf)){throw 'Missing owned test'}
$users=@(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Where-Object {$_.SessionId -gt 0} | ForEach-Object {
 $o=Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
 if($o.ReturnValue -eq 0 -and $o.Sid -match '^S-1-5-21-'){[pscustomobject]@{Sid=$o.Sid;Session=$_.SessionId}}
} | Sort-Object Sid,Session -Unique)
if($users.Count -ne 1){throw 'No unique interactive desktop'}
$root=Join-Path $env:ProgramData ('personal-control-plane\focused-tests\os-properties-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
& icacls.exe $root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*'+$users[0].Sid+':(OI)(CI)M') *> $null
if($LASTEXITCODE -ne 0){throw 'Owned workspace ACL setup failed'}
$worker=Join-Path $root 'worker.ps1';$log=Join-Path $root 'baseline.log';$result=Join-Path $root 'result.txt'
$code=@'
param([string]$Source,[string]$Root)
$ErrorActionPreference='Stop'
$log=Join-Path $Root 'baseline.log';$result=Join-Path $Root 'result.txt'
try{
 Set-Location -LiteralPath $Source
 $env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8';$env:GITHUB_ACTIONS='true'
 $before=$ErrorActionPreference;$ErrorActionPreference='Continue'
 try{
  & python.exe -X utf8 -u tests\winui\test_owned_explorer_properties_baseline.py 2>&1 | Out-File -LiteralPath $log -Append -Encoding utf8
  $code=$LASTEXITCODE
 }finally{$ErrorActionPreference=$before}
 if($code -ne 0){throw ('OS_PROPERTIES_EXIT='+$code)}
 Set-Content -LiteralPath $result -Value 'PASS' -Encoding ASCII
}catch{
 Add-Content -LiteralPath $log -Value ('TEST_FAILURE='+$_.Exception.Message)
 Set-Content -LiteralPath $result -Value 'FAIL' -Encoding ASCII
}
'@
Set-Content -LiteralPath $worker -Value $code -Encoding UTF8
$name='PcpFlyOsProperties-'+[guid]::NewGuid().ToString('N');$registered=$false
try{
 $ps=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $args='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$worker+'" -Source "'+$Source+'" -Root "'+$root+'"'
 $action=New-ScheduledTaskAction -Execute $ps -Argument $args
 $principal=New-ScheduledTaskPrincipal -UserId $users[0].Sid -LogonType Interactive -RunLevel Limited
 Register-ScheduledTask -TaskName $name -Action $action -Principal $principal -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 3)) -Force | Out-Null
 $registered=$true
 Start-ScheduledTask -TaskName $name
 Write-Output ('OS_PROPERTIES_BASELINE_WORKSPACE='+$root)
 $deadline=(Get-Date).AddSeconds(150)
 while(-not (Test-Path -LiteralPath $result) -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 3}
 if(-not (Test-Path -LiteralPath $result)){throw 'OS Properties baseline task deadline'}
 $status=(Get-Content -LiteralPath $result -Raw).Trim()
 Write-Output ('OS_PROPERTIES_BASELINE_RESULT='+$status)
 if(Test-Path -LiteralPath $log){
  Get-Content -LiteralPath $log -Tail 50 | ForEach-Object {Write-Output ('OS_PROPERTIES_BASELINE_LOG '+$_)}
 }
 if($status -cne 'PASS'){throw 'OS Properties baseline failed'}
}finally{
 if($registered){
  try{
   $t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
   if($t -and $t.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue}
   Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
  }catch{Write-Warning 'Review owned baseline task cleanup'}
 }
}

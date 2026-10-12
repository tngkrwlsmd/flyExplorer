# Verify an unsigned private setup against its exact built runtime and source ZIP.
# Never install, sign, publish, create tags, or change production registration.
param([string]$Source,[string]$Root,[string]$Expected)
$ErrorActionPreference='Stop'
if($Expected -notmatch '^[0-9a-f]{40}$'){throw 'Exact 40-char SHA required'}
$base=[IO.Path]::GetFullPath((Join-Path $env:ProgramData 'personal-control-plane\scratch')).TrimEnd('\')
$canon=[IO.Path]::GetFullPath($Root).TrimEnd('\')
if(-not $canon.StartsWith($base+'\v-',[StringComparison]::OrdinalIgnoreCase) -or $canon.Substring(($base+'\v-').Length) -notmatch '^[0-9a-f]{12}$'){throw 'Refuse non-owned scratch'}
if((Get-Item -LiteralPath $Root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Refuse linked root'}
if([IO.Path]::GetFullPath($Source) -cne [IO.Path]::GetFullPath((Join-Path $Root 'source'))){throw 'Wrong owned source'}
$rev=(& git -C $Source rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $rev -cne $Expected){throw 'Source SHA mismatch'}
$users=@(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Where-Object {$_.SessionId -gt 0} | ForEach-Object {
 $o=Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
 if($o.ReturnValue -eq 0 -and $o.Sid -match '^S-1-5-21-'){[pscustomobject]@{sid=$o.Sid;session=$_.SessionId}}
} | Sort-Object session,sid -Unique)
if($users.Count -ne 1){throw 'One owned interactive account required'}
& icacls.exe $Root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*'+$users[0].sid+':(OI)(CI)M') | Out-Null
if($LASTEXITCODE -ne 0){throw 'Owned ACL failed'}
Write-Output ('PRIVATE_IDENTITY_SESSION='+$users[0].session)
$worker=Join-Path $Root 'identity-worker.ps1'
$result=Join-Path $Root 'identity-result.json'
$code=@'
param([string]$Source,[string]$Result,[string]$Expected)
$ErrorActionPreference='Stop';$status='FAIL';$stage='preflight';$detail='';$info=@{}
$log=Join-Path (Split-Path -Parent $Result) 'identity-build.log'
try {
 Set-Location -LiteralPath $Source
 $env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
 $env:GIT_CONFIG_COUNT='1';$env:GIT_CONFIG_KEY_0='safe.directory';$env:GIT_CONFIG_VALUE_0=$Source
 $rev=(& git rev-parse HEAD).Trim()
 if($LASTEXITCODE -ne 0 -or $rev -cne $Expected){throw 'Worker source differs'}
 $old=Get-Content -LiteralPath 'packaging\RELEASE_IDENTITY.json' -Raw -Encoding UTF8 | ConvertFrom-Json
 $info.old_binary_source=[string]$old.binary_source_revision
 $tasks=@(
  @{name='clean-release-setup';exe='cmd.exe';args=@('/d','/c','fly.bat package')},
  @{name='source-write';exe='python.exe';args=@('-X','utf8','packaging/source_bundle.py','--write','--revision','HEAD')},
  @{name='source-check';exe='python.exe';args=@('-X','utf8','packaging/source_bundle.py','--check','--revision','HEAD')},
  @{name='identity-write';exe='python.exe';args=@('-X','utf8','packaging/release_identity.py','--write','--source-manifest',('out/release/flyExplorer-source-'+$Expected+'.manifest.json'),'--source-bundle',('out/release/flyExplorer-source-'+$Expected+'.zip'),'--setup','out/package/flyExplorer-Setup-x64.exe','--identity','out/release/RELEASE_IDENTITY.json')},
  @{name='identity-check';exe='python.exe';args=@('-X','utf8','packaging/release_identity.py','--check','--source-manifest',('out/release/flyExplorer-source-'+$Expected+'.manifest.json'),'--source-bundle',('out/release/flyExplorer-source-'+$Expected+'.zip'),'--setup','out/package/flyExplorer-Setup-x64.exe','--identity','out/release/RELEASE_IDENTITY.json')}
 )
 foreach($task in $tasks){
  $stage=$task.name;$argv=[string[]]$task.args
  $ErrorActionPreference='Continue'
  & $task.exe @argv *>&1 | Out-File -LiteralPath $log -Append -Encoding UTF8
  $rc=$LASTEXITCODE;$ErrorActionPreference='Stop'
  if($rc -ne 0){throw ('Stage '+$stage+' exit '+$rc)}
 }
 $stage='verify-exact-identity'
 $identity=Get-Content -LiteralPath 'out\release\RELEASE_IDENTITY.json' -Raw -Encoding UTF8 | ConvertFrom-Json
 $bundle=Get-Content -LiteralPath ('out\release\flyExplorer-source-'+$Expected+'.manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $provenance=Get-Content -LiteralPath 'packaging\licenses\PAYLOAD_PROVENANCE.json' -Raw -Encoding UTF8 | ConvertFrom-Json
 if($identity.binary_source_revision -cne $Expected -or $identity.runtime.source_revision -cne $Expected -or $bundle.source_revision -cne $Expected -or $provenance.runtime_source_revision -cne $Expected){throw 'Runtime and source identity mismatch'}
 if($identity.publication_status -cne 'private-evidence-only' -or $identity.public_distribution_clearance -cne 'not-cleared' -or $identity.setup.signing_status -cne 'unsigned'){throw 'Unauthorized distribution status'}
 $changed=@(& git diff --name-only)
 if(@($changed | Where-Object {$_ -notin @('packaging/licenses/PAYLOAD_PROVENANCE.json','packaging/licenses/PAYLOAD_PROVENANCE.md')}).Count -gt 0){throw ('Unexpected source mutation '+($changed -join ','))}
 $info.current_source=$Expected
 $info.source_tree=[string]$identity.source_tree_sha
 $info.source_zip_sha256=[string]$identity.source_bundle.sha256
 $info.source_files=[int]$identity.source_bundle.tracked_file_count
 $info.runtime_manifest_sha256=[string]$identity.runtime.manifest_sha256
 $info.runtime_files=[int]$identity.runtime.file_count
 $info.setup_sha256=[string]$identity.setup.sha256
 $info.setup_bytes=[long]$identity.setup.bytes
 $stage='complete';$status='PASS';$detail='Private setup, runtime and matching source ZIP verified'
}catch{$detail=$_.Exception.Message}
finally{@{status=$status;stage=$stage;detail=$detail;info=$info}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $Result -Encoding UTF8}
if($status -ne 'PASS'){exit 1}
'@
Set-Content -LiteralPath $worker -Value $code -Encoding UTF8
$name='PcpFlyAudit-'+[guid]::NewGuid().ToString('N')
$registered=$false;$pass=$false
try {
 $pwsh=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $arguments='-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$worker+'" -Source "'+$Source+'" -Result "'+$result+'" -Expected "'+$Expected+'"'
 Register-ScheduledTask -TaskName $name -Action (New-ScheduledTaskAction -Execute $pwsh -Argument $arguments) -Principal (New-ScheduledTaskPrincipal -UserId $users[0].sid -LogonType Interactive -RunLevel Limited) -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 24)) -Force | Out-Null
 $registered=$true;Start-ScheduledTask -TaskName $name
 $deadline=(Get-Date).AddMinutes(21)
 while(-not(Test-Path -LiteralPath $result -PathType Leaf) -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 5}
 if(-not(Test-Path -LiteralPath $result -PathType Leaf)){throw 'Private identity check timed out'}
 $outcome=Get-Content -LiteralPath $result -Raw -Encoding UTF8 | ConvertFrom-Json
 Write-Output ('PRIVATE_IDENTITY_STATUS='+$outcome.status+' STAGE='+$outcome.stage+' DETAIL='+$outcome.detail)
 if($outcome.status -ne 'PASS'){
  $log=Join-Path $Root 'identity-build.log'
  if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 45|ForEach-Object{Write-Output ('PRIVATE_IDENTITY_LOG '+$_)}}
  throw ('Exact private identity not accepted: '+$outcome.detail)
 }
 $i=$outcome.info
 Write-Output ('PRIVATE_IDENTITY_OLD_SOURCE='+$i.old_binary_source)
 Write-Output ('PRIVATE_IDENTITY_CURRENT_SOURCE='+$i.current_source)
 Write-Output ('PRIVATE_IDENTITY_SOURCE_TREE='+$i.source_tree)
 Write-Output ('PRIVATE_IDENTITY_SOURCE_SHA256='+$i.source_zip_sha256)
 Write-Output ('PRIVATE_IDENTITY_SOURCE_FILES='+$i.source_files)
 Write-Output ('PRIVATE_IDENTITY_RUNTIME_SHA256='+$i.runtime_manifest_sha256)
 Write-Output ('PRIVATE_IDENTITY_RUNTIME_FILES='+$i.runtime_files)
 Write-Output ('PRIVATE_IDENTITY_SETUP_SHA256='+$i.setup_sha256)
 Write-Output ('PRIVATE_IDENTITY_SETUP_BYTES='+$i.setup_bytes)
 Write-Output 'PRIVATE_IDENTITY_MATCH=PASS PRIVATE_ONLY=TRUE'
 $pass=$true
}finally{
 if($registered){
  $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if($task -and $task.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue}
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 }
 if($pass){Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction Stop;Write-Output 'PRIVATE_IDENTITY_OWNED_CLEANUP=PASS'}
 else{Write-Output ('PRIVATE_IDENTITY_EVIDENCE_RETAINED='+$Root)}
}

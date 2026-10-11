#requires -Version 5.1
<#
 Runs in an EXISTING interactive user session, via an owned one-shot task.
 All source/destination/test logs are strictly in -Root. The production
 helper resolves its own real user's LocalAppData Known Folder and writes
 only its normal per-operation immutable receipt files. No cleanup.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Root,
    [Parameter(Mandatory)][string]$Result
)
$ErrorActionPreference = 'Stop'
$stage = 'session'
$passed = $false
$log = Join-Path $Root 'interactive-receipt.log'
try {
    $session = (Get-Process -Id $PID).SessionId
    if ($session -le 0 -or -not @(Get-Process explorer -ErrorAction SilentlyContinue |
            Where-Object { $_.SessionId -eq $session }).Count) {
        throw 'No unlocked interactive Explorer session'
    }
    $python = Get-Command python.exe -ErrorAction Stop
    & $python.Source -X utf8 -c "import pywinauto"
    if ($LASTEXITCODE -ne 0) { throw 'Interactive GUI Python dependencies missing' }
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $env:FLY_ALLOW_INTERACTIVE_RECEIPT_GUI = '1'
    $env:FLY_INTERACTIVE_RECEIPT_LOG_ROOT = Join-Path $Root 'logs'
    $env:GITHUB_ACTIONS = 'true'

    $stage = 'actual-winui-copy'
    $gui = Join-Path $Root 'tests\winui\test_owned_user_receipt_gui.py'
    # Native stderr must not be promoted to a terminating PowerShell error.
    # Keep only this test-owned GUI process stdout/stderr in owned evidence.
    $stdout = Join-Path $Root 'owned-gui-stdout.log'
    $stderr = Join-Path $Root 'owned-gui-stderr.log'
    $arguments = '-X utf8 "' + $gui + '"'
    $guiProcess = Start-Process -FilePath $python.Source -ArgumentList $arguments -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    ('GUI_PYTHON_EXIT=' + $guiProcess.ExitCode) | Out-File -FilePath $log -Append -Encoding utf8
    foreach ($file in @($stdout,$stderr)) {
        if (Test-Path -LiteralPath $file) {
            Get-Content -LiteralPath $file -Tail 35 | Out-File -FilePath $log -Append -Encoding utf8
        }
    }
    if ($guiProcess.ExitCode -ne 0) { throw 'Owned interactive GUI transfer gate failed' }

    $stage = 'shipping-helper-direct-ipc'
    $fixture = Join-Path $Root 'tests\winui\m22\bin\x64\Release\FlyM22ShellTransferContracts.exe'
    $sourceDir = Join-Path $Root 'owned-ipc-source'
    $targetDir = Join-Path $Root 'owned-ipc-target'
    New-Item -ItemType Directory -Path $sourceDir,$targetDir -Force | Out-Null
    $source = Join-Path $sourceDir 'direct-user-knownfolder-한글.txt'
    [IO.File]::WriteAllText($source,'Owned-user shipping helper IPC, no cleanup')
    & $fixture '--real-user-shipping-helper-ipc' $source $targetDir *>&1 |
        Out-File -FilePath $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Shipping-helper Known Folder IPC gate failed' }

    $passed = $true
    Write-Output 'INTERACTIVE_SHIPPING_KNOWNFOLDER_GUI_AND_IPC=PASS'
} catch {
    # Avoid emitting user paths or account identifiers in persisted evidence.
    Write-Output ('INTERACTIVE_RECEIPT_FAILED_STAGE=' + $stage)
    Write-Output ('INTERACTIVE_RECEIPT_FAILED_TYPE=' + $_.Exception.GetType().Name)
    try {
        ('FAILED_STAGE=' + $stage) | Out-File -FilePath $log -Append -Encoding utf8
        ('FAILED_TYPE=' + $_.Exception.GetType().Name) | Out-File -FilePath $log -Append -Encoding utf8
    } catch {}
} finally {
    @{
        status = if ($passed) { 'PASS' } else { 'FAIL' }
        stage = if ($passed) { 'complete' } else { $stage }
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath $Result -Encoding utf8
}
if (-not $passed) { exit 1 }

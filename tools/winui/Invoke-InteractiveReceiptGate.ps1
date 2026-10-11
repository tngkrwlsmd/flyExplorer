#requires -Version 5.1
<#
 One-shot interactive-user test bridge for an exact reviewed Draft PR SHA.
 Mirrors central GUI's InteractiveToken design, but MUST NOT post central
 main-only CI status or touch other user's windows/processes/files.
 All staged runtime, temporary task, and result are uniquely test owned.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^[a-f0-9]{40}$')][string]$ExpectedSha,
    [Parameter(Mandatory)][string]$Worktree
)
$ErrorActionPreference = 'Stop'
$canonical = 'C:\ProgramData\personal-control-plane\scratch\flyexp-receipt-full-e2cf2d18'
if ($Worktree -cne $canonical -or
    [Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne 'S-1-5-18') {
    throw 'Refusing non-owned checkout or non-SYSTEM orchestrator'
}
$actual = (& git -C $Worktree rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $ExpectedSha -or
    @(git -C $Worktree status --porcelain).Count -ne 0) {
    throw 'Refusing unexpected source SHA or dirty tracked checkout'
}
$relative = 'logs\interactive-user-receipt-' + $ExpectedSha.Substring(0,8)
$owned = Join-Path $Worktree $relative
if (Test-Path -LiteralPath $owned) { throw 'One-shot fixture already exists' }
$interactive = @(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" |
    Where-Object { $_.SessionId -gt 0 } | ForEach-Object {
        $owner = Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
        if ($owner.ReturnValue -eq 0 -and $owner.Sid -match '^S-1-5-21-') {
            [pscustomobject]@{ Session=$_.SessionId; Sid=$owner.Sid }
        }
    } | Sort-Object Session,Sid -Unique)
if ($interactive.Count -ne 1) {
    throw ('Require exactly one interactive Explorer user: count=' +
           $interactive.Count)
}
$sourceRuntime = Join-Path $Worktree 'out\winui\Release'
$sourceFixture = Join-Path $Worktree 'tests\winui\m22\bin\x64\Release\FlyM22ShellTransferContracts.exe'
$sourceWorker = Join-Path $Worktree 'tools\winui\OwnedInteractiveReceiptWorker.ps1'
foreach ($path in @($sourceRuntime,$sourceFixture,$sourceWorker)) {
    if (-not (Test-Path -LiteralPath $path)) { throw 'Required acceptance output unavailable' }
}
if (-not (Test-Path -LiteralPath (Join-Path $sourceRuntime 'FlyShellIsolationHelper.exe')) -or
    -not (Test-Path -LiteralPath (Join-Path $sourceRuntime 'flyExplorer.exe'))) {
    throw 'Shipping app or helper missing'
}
# No unreviewed symlinks are copied into an interactive user's runnable tree.
$reparse = @(Get-ChildItem -LiteralPath $sourceRuntime -Recurse -Force |
    Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
if ($reparse.Count) { throw 'Refusing to copy reparse-point Release runtime' }

$run = Join-Path $owned 'runtime'
$taskName = 'FlyOwnedReceipt-' + [guid]::NewGuid().ToString('N')
$result = Join-Path $run 'interactive-result.json'
$taskRegistered = $false
try {
    New-Item -ItemType Directory -Path $owned,$run -Force | Out-Null
    & icacls.exe $owned '/inheritance:r' '/grant:r' '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*'+$interactive[0].Sid+':(OI)(CI)M') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Owned fixture ACL grant failed' }

    $releaseParent = Join-Path $run 'out\winui'
    New-Item -ItemType Directory -Path $releaseParent -Force | Out-Null
    Copy-Item -LiteralPath $sourceRuntime -Destination $releaseParent -Recurse -Force
    $testDir = Join-Path $run 'tests\winui'
    $nativeDir = Join-Path $testDir 'm22\bin\x64\Release'
    New-Item -ItemType Directory -Path $nativeDir -Force | Out-Null
    foreach ($name in @('paths.py','uia_polling.py','receipt_wire_owned.py','test_owned_user_receipt_gui.py')) {
        Copy-Item -LiteralPath (Join-Path $Worktree ('tests\winui\'+$name)) -Destination $testDir
    }
    Copy-Item -LiteralPath $sourceFixture -Destination $nativeDir
    Copy-Item -LiteralPath (Join-Path $sourceRuntime 'FlyShellIsolationHelper.exe') -Destination $nativeDir
    $worker = Join-Path $owned 'OwnedInteractiveReceiptWorker.ps1'
    Copy-Item -LiteralPath $sourceWorker -Destination $worker
    if (-not (Test-Path -LiteralPath (Join-Path $run 'out\winui\Release\flyExplorer.exe'))) {
        throw 'Exact private app runtime staging failed'
    }
    Write-Output 'INTERACTIVE_RECEIPT_OWNED_RUNTIME_STAGED=PASS'

    $command = '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
        $worker + '" -Root "' + $run + '" -Result "' + $result + '"'
    $action = New-ScheduledTaskAction -Execute (
        Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    ) -Argument $command
    $principal = New-ScheduledTaskPrincipal -UserId $interactive[0].Sid -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 6) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $settings -Force | Out-Null
    $taskRegistered = $true
    Start-ScheduledTask -TaskName $taskName
    Write-Output 'INTERACTIVE_RECEIPT_OWNED_TASK_STARTED=PASS'
    $deadline = (Get-Date).AddMinutes(6)
    while (-not (Test-Path -LiteralPath $result) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
    }
    if (-not (Test-Path -LiteralPath $result)) {
        throw 'Interactive worker did not deliver bounded result'
    }
    $state = Get-Content -Raw -LiteralPath $result | ConvertFrom-Json
    $log = Join-Path $run 'interactive-receipt.log'
    if (Test-Path -LiteralPath $log) {
        Get-Content -LiteralPath $log -Tail 18 |
            ForEach-Object { Write-Output ('OWNED_USER_LOG ' + $_) }
    }
    if ($state.status -ne 'PASS') {
        throw ('Interactive user acceptance failed at stage: ' + $state.stage)
    }
    Write-Output 'INTERACTIVE_REAL_USER_KNOWNFOLDER_GUI_AND_IPC=PASS'
    Write-Output ('INTERACTIVE_RECEIPT_EXACT_SHA=' + $ExpectedSha)
} finally {
    if ($taskRegistered) {
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task -and $task.State -eq 'Running') {
                Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            }
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        } catch { Write-Warning 'One-shot task cleanup failed; review task by owned prefix' }
    }
    # Retain owned runtime and logs as evidence; no cleanup or enumeration
    # of the real user's persistent app Known Folder is performed by SYSTEM.
    Write-Output 'INTERACTIVE_RECEIPT_ONE_SHOT_TASK_RELEASED=TRUE'
}

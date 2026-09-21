param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDir,

    [Parameter(Mandatory = $true)]
    [string]$Configuration,

    [int]$StartupTimeoutSeconds = 12,

    [int]$StabilitySeconds = 3
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Path {
    param([string]$Path, [string]$Description)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Description is missing: $Path"
    }
}

function Write-Utf16Config {
    param([string]$Path, [string[]]$Lines)

    $content = ($Lines -join "`r`n") + "`r`n"
    [System.IO.File]::WriteAllText(
        $Path,
        $content,
        [System.Text.UnicodeEncoding]::new($false, $true)
    )
}

$resolvedSource = (Resolve-Path -LiteralPath $SourceDir).Path
Require-Path (Join-Path $resolvedSource "fxfile.exe") "flyExplorer executable"
Require-Path (Join-Path $resolvedSource "fxfile-crash.dll") "crash module"
Require-Path (Join-Path $resolvedSource "fxfile-launcher.exe") "launcher helper"
Require-Path (Join-Path $resolvedSource "fxfile-keyhook.dll") "keyhook helper"
Require-Path (Join-Path $resolvedSource "Languages") "language directory"

$languageFiles = Get-ChildItem -LiteralPath (Join-Path $resolvedSource "Languages") -File
if (-not $languageFiles) {
    throw "No language files were staged under $resolvedSource\Languages."
}

$xprCandidates = @(
    (Join-Path $resolvedSource "libxprw.dll"),
    (Join-Path $resolvedSource "libxpr.dll")
) | Where-Object { Test-Path -LiteralPath $_ }

if ($xprCandidates.Count -ne 1) {
    throw "Expected exactly one xpr runtime in $resolvedSource; found $($xprCandidates.Count)."
}

$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
foreach ($valueName in @("fxfile-launcher", "fxfile-upchecker")) {
    $existing = Get-ItemProperty -Path $runKey -Name $valueName -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        throw "Refusing runtime smoke because HKCU Run value '$valueName' already exists."
    }
}

$appRegistryRoot = "HKCU:\Software\fxfile"
if (Test-Path -LiteralPath $appRegistryRoot) {
    throw "Refusing runtime smoke because existing flyExplorer HKCU profile data was found."
}

$smokeRoot = Join-Path $env:RUNNER_TEMP ("flyExplorer-runtime-smoke-" + [guid]::NewGuid().ToString("N"))
$runtimeDir = Join-Path $smokeRoot "runtime"
$confDir = Join-Path $smokeRoot "conf"
$testDir = Join-Path $smokeRoot "test-root"
$process = $null

try {
    New-Item -ItemType Directory -Path $runtimeDir, $confDir, $testDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $testDir "FolderA"), (Join-Path $testDir "FolderB") -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $testDir "root.txt") -Value "flyExplorer runtime smoke" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $testDir "FolderA\child.txt") -Value "child" -Encoding UTF8

    Copy-Item -LiteralPath (Join-Path $resolvedSource "*") -Destination $runtimeDir -Recurse -Force

    Write-Utf16Config -Path (Join-Path $confDir "fxfile-main.conf") -Lines @(
        "[main]",
        "main.tip_of_today.show = 0"
    )

    Write-Utf16Config -Path (Join-Path $confDir "fxfile.conf") -Lines @(
        "[config]",
        "config.update_check.enable = 0",
        "config.global_hotkey.enable = 0",
        "config.global_hotkey.show_tray = 0",
        "config.global_hotkey.windows_startup = 0",
        "config.register_shell_context_menu = 0",
        "config.single_process = 0",
        "config.language = English"
    )

    $exe = Join-Path $runtimeDir "fxfile.exe"
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $exe
    $startInfo.WorkingDirectory = $runtimeDir
    $startInfo.UseShellExecute = $false
    $startInfo.ArgumentList.Add("--conf_dir=$confDir")
    $startInfo.ArgumentList.Add($testDir)

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo

    Write-Host "Configuration: $Configuration"
    Write-Host "Executable: $exe"
    Write-Host "Runtime directory: $runtimeDir"
    Write-Host "xpr runtime: $([System.IO.Path]::GetFileName($xprCandidates[0]))"

    if (-not $process.Start()) {
        throw "Process.Start returned false."
    }

    Write-Host "Process id: $($process.Id)"

    try {
        $null = $process.WaitForInputIdle(5000)
    }
    catch {
        Write-Host "WaitForInputIdle was unavailable; continuing with bounded window polling."
    }

    $deadline = [DateTime]::UtcNow.AddSeconds($StartupTimeoutSeconds)
    $mainWindow = [IntPtr]::Zero

    while ([DateTime]::UtcNow -lt $deadline) {
        $process.Refresh()

        if ($process.HasExited) {
            throw "fxfile.exe exited during startup with code $($process.ExitCode)."
        }

        $mainWindow = $process.MainWindowHandle
        if ($mainWindow -ne [IntPtr]::Zero) {
            break
        }

        Start-Sleep -Milliseconds 250
    }

    if ($mainWindow -eq [IntPtr]::Zero) {
        throw "fxfile.exe did not create a top-level main window within $StartupTimeoutSeconds seconds."
    }

    Write-Host ("Main window handle: 0x{0:X}" -f $mainWindow.ToInt64())
    Start-Sleep -Seconds $StabilitySeconds
    $process.Refresh()

    if ($process.HasExited) {
        throw "fxfile.exe exited during the stability window with code $($process.ExitCode)."
    }

    Write-Host "Hosted-runner launch smoke PASS: process stayed alive and created a main window."
}
finally {
    if ($null -ne $process) {
        try {
            $process.Refresh()
            if (-not $process.HasExited) {
                $null = $process.CloseMainWindow()
                if (-not $process.WaitForExit(5000)) {
                    $process.Kill($true)
                    $process.WaitForExit(5000) | Out-Null
                }
            }
        }
        catch {
            Write-Warning "Failed to stop smoke-test process cleanly: $($_.Exception.Message)"
            try {
                if (-not $process.HasExited) {
                    $process.Kill($true)
                }
            }
            catch {
            }
        }
        finally {
            $process.Dispose()
        }
    }

    if (Test-Path -LiteralPath $appRegistryRoot) {
        Remove-Item -LiteralPath $appRegistryRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path -LiteralPath $smokeRoot) {
        Remove-Item -LiteralPath $smokeRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

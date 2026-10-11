#requires -Version 5.1
<#
.SYNOPSIS
  Read-only audit of a separate Hyper-V HOST for a disposable durability lab.
.DESCRIPTION
  Must run on the Hyper-V host, NOT in the existing shared Windows guest.
  This never creates, deletes, starts, stops or modifies a VM, disk or switch.
  It prints capability flags and resource counts only; no VM names, host
  identities, account SIDs or private storage paths leave the host.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'

$cmd = Get-Command -Name Get-VMHost -ErrorAction SilentlyContinue
if (-not $cmd) {
    Write-Output 'FLY_HYPERV_HOST_AUDIT=UNAVAILABLE'
    Write-Output 'FLY_HYPERV_REASON=VM_MANAGEMENT_CMDLETS_MISSING'
    exit 2
}
$vmms = Get-Service -Name vmms -ErrorAction SilentlyContinue
if (-not $vmms -or $vmms.Status -ne 'Running') {
    Write-Output 'FLY_HYPERV_HOST_AUDIT=UNAVAILABLE'
    Write-Output 'FLY_HYPERV_REASON=VMMS_NOT_RUNNING'
    exit 3
}

$hypervisor = Get-VMHost -ErrorAction Stop
$vms = @(Get-VM -ErrorAction Stop)
$switches = @(Get-VMSwitch -ErrorAction Stop)
$guest = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
$os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
$diskLocation = [string]$hypervisor.VirtualHardDiskPath
$configLocation = [string]$hypervisor.VirtualMachinePath
$diskRoot = [System.IO.Path]::GetPathRoot($diskLocation)
$diskFreeGiB = 'UNKNOWN'
if ($diskRoot -and $diskRoot -match '^[A-Za-z]:\\$') {
    $drive = Get-PSDrive -Name $diskRoot.Substring(0,1) -PSProvider FileSystem -ErrorAction SilentlyContinue
    if ($drive -and $null -ne $drive.Free) {
        $diskFreeGiB = [string][math]::Floor($drive.Free / 1GB)
    }
}
$running = @($vms | Where-Object { $_.State -eq 'Running' })
$labName = 'flyExplorer-DurabilityLab'
$reserved = @($vms | Where-Object { $_.Name -eq $labName })
$memoryTotal = [math]::Floor([double]$guest.TotalPhysicalMemory / 1GB)
$memoryFree = [math]::Floor(([double]$os.FreePhysicalMemory * 1KB) / 1GB)

Write-Output 'FLY_HYPERV_HOST_AUDIT=PASS'
Write-Output 'FLY_HYPERV_VMMS_RUNNING=TRUE'
Write-Output ('FLY_HYPERV_VM_COUNT=' + $vms.Count)
Write-Output ('FLY_HYPERV_RUNNING_VM_COUNT=' + $running.Count)
Write-Output ('FLY_HYPERV_SWITCH_COUNT=' + $switches.Count)
Write-Output ('FLY_HYPERV_VHD_FOLDER_EXISTS=' + [bool](Test-Path -LiteralPath $diskLocation -PathType Container))
Write-Output ('FLY_HYPERV_CONFIG_FOLDER_EXISTS=' + [bool](Test-Path -LiteralPath $configLocation -PathType Container))
Write-Output ('FLY_HYPERV_DEFAULT_VHD_FREE_GIB=' + $diskFreeGiB)
Write-Output ('FLY_HYPERV_HOST_TOTAL_RAM_GIB=' + $memoryTotal)
Write-Output ('FLY_HYPERV_HOST_FREE_RAM_GIB=' + $memoryFree)
Write-Output ('FLY_HYPERV_LAB_NAME_RESERVED=' + [bool]($reserved.Count -ne 0))
Write-Output ('FLY_HYPERV_CHECKPOINT_QUERY_AVAILABLE=' + [bool](Get-Command Get-VMSnapshot -ErrorAction SilentlyContinue))
Write-Output ('FLY_HYPERV_EXPORT_AVAILABLE=' + [bool](Get-Command Export-VM -ErrorAction SilentlyContinue))
Write-Output 'FLY_HYPERV_DISPOSABLE_VM_PROVISIONED=UNVERIFIED'
Write-Output 'FLY_HYPERV_HOST_SIDE_ROLLBACK=UNVERIFIED'
Write-Output 'FLY_HYPERV_AUDIT_READONLY=TRUE'

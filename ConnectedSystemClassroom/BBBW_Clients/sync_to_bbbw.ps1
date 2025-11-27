# PowerShell script to sync BBBW client files to BeagleBone Black Wireless board
# Handles differences gracefully by checking file existence and prompting for conflicts

param(
    [Parameter(Mandatory=$true)]
    [string]$BBBW_IP = "192.168.7.2",  # Default USB IP, change if using WiFi
    
    [Parameter(Mandatory=$false)]
    [string]$RemotePath = "/var/lib/cloud9/BBBW_Clients",
    
    [Parameter(Mandatory=$false)]
    [string]$SSHKey = "$env:USERPROFILE\.ssh\beaglebone_key",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false  # Force overwrite without prompting
)

$ErrorActionPreference = "Continue"
$LocalPath = $PSScriptRoot

Write-Host "=== BBBW Client File Sync ===" -ForegroundColor Cyan
Write-Host "Source: $LocalPath" -ForegroundColor Gray
Write-Host "Destination: debian@${BBBW_IP}:${RemotePath}" -ForegroundColor Gray
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $SSHKey)) {
    Write-Host "ERROR: SSH key not found at: $SSHKey" -ForegroundColor Red
    Write-Host "Please generate SSH key first using:" -ForegroundColor Yellow
    Write-Host "  ssh-keygen -t rsa -b 4096 -f `$env:USERPROFILE\.ssh\beaglebone_key -N '""'" -ForegroundColor Yellow
    exit 1
}

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
$sshTest = ssh -i $SSHKey -o ConnectTimeout=5 -o BatchMode=yes debian@${BBBW_IP} "echo 'connected'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cannot connect to BBBW at ${BBBW_IP}" -ForegroundColor Red
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "  1. BBBW is connected (USB or WiFi)" -ForegroundColor Yellow
    Write-Host "  2. IP address is correct (current: ${BBBW_IP})" -ForegroundColor Yellow
    Write-Host "  3. SSH key is authorized on BBBW" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To connect manually: ssh -i $SSHKey debian@${BBBW_IP}" -ForegroundColor Gray
    exit 1
}

Write-Host "Connection successful!" -ForegroundColor Green
Write-Host ""

# Create remote directory if it doesn't exist
Write-Host "Creating remote directory if needed..." -ForegroundColor Yellow
ssh -i $SSHKey debian@${BBBW_IP} "mkdir -p ${RemotePath}" | Out-Null

# Get list of Python files to sync
$filesToSync = Get-ChildItem -Path $LocalPath -Filter "*.py" -File

if ($filesToSync.Count -eq 0) {
    Write-Host "No Python files found to sync." -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($filesToSync.Count) file(s) to sync:" -ForegroundColor Cyan
$filesToSync | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
Write-Host ""

# Sync each file
$syncedCount = 0
$skippedCount = 0
$errorCount = 0

foreach ($file in $filesToSync) {
    $localFile = $file.FullName
    $remoteFile = "${RemotePath}/$($file.Name)"
    
    Write-Host "Syncing: $($file.Name)..." -ForegroundColor Yellow -NoNewline
    
    # Check if file exists on remote
    $remoteExists = ssh -i $SSHKey debian@${BBBW_IP} "test -f ${remoteFile} && echo 'exists' || echo 'notfound'" 2>&1
    
    if ($remoteExists -eq "exists" -and -not $Force) {
        # Get file sizes for comparison
        $localSize = (Get-Item $localFile).Length
        $remoteSize = ssh -i $SSHKey debian@${BBBW_IP} "stat -c%s ${remoteFile}" 2>&1
        
        if ($localSize -eq $remoteSize) {
            Write-Host " [SKIP - identical]" -ForegroundColor Gray
            $skippedCount++
            continue
        }
        
        # Files differ - prompt user (unless Force is set)
        Write-Host ""
        Write-Host "  WARNING: Remote file exists and differs!" -ForegroundColor Yellow
        Write-Host "  Local size:  $localSize bytes" -ForegroundColor Gray
        Write-Host "  Remote size: $remoteSize bytes" -ForegroundColor Gray
        Write-Host "  Remote file will be overwritten." -ForegroundColor Yellow
    }
    
    # Copy file using SCP
    $scpOutput = scp -i $SSHKey "$localFile" "debian@${BBBW_IP}:${remoteFile}" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK]" -ForegroundColor Green
        $syncedCount++
    } else {
        Write-Host " [ERROR]" -ForegroundColor Red
        Write-Host "  $scpOutput" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "=== Sync Complete ===" -ForegroundColor Cyan
Write-Host "Synced:   $syncedCount" -ForegroundColor Green
Write-Host "Skipped:  $skippedCount" -ForegroundColor Gray
Write-Host "Errors:   $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Gray" })
Write-Host ""

if ($errorCount -eq 0) {
    Write-Host "To run on BBBW:" -ForegroundColor Cyan
    Write-Host "  ssh -i $SSHKey debian@${BBBW_IP}" -ForegroundColor Gray
    Write-Host "  cd ${RemotePath}" -ForegroundColor Gray
    Write-Host "  sudo python3 BBBW2_Potentiometer.py" -ForegroundColor Gray
}


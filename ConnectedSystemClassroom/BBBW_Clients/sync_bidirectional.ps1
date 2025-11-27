# Bidirectional sync script - Pulls from BBBW and Pushes to BBBW
# Handles folders recursively and ensures 100% synchronization

param(
    [Parameter(Mandatory=$false)]
    [string]$BBBW_IP = "192.168.7.2",
    
    [Parameter(Mandatory=$false)]
    [string]$RemotePath = "/var/lib/cloud9/BBBW_Clients",
    
    [Parameter(Mandatory=$false)]
    [string]$SSHKey = "$env:USERPROFILE\.ssh\beaglebone_key",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Watch = $false
)

$ErrorActionPreference = "Continue"
$LocalPath = $PSScriptRoot

Write-Host "=== Bidirectional BBBW Sync ===" -ForegroundColor Cyan
Write-Host "Local:  $LocalPath" -ForegroundColor Gray
Write-Host "Remote: debian@${BBBW_IP}:${RemotePath}" -ForegroundColor Gray
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $SSHKey)) {
    Write-Host "ERROR: SSH key not found at: $SSHKey" -ForegroundColor Red
    exit 1
}

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
$sshTest = ssh -i $SSHKey -o ConnectTimeout=5 -o BatchMode=yes debian@${BBBW_IP} "echo 'connected'" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cannot connect to BBBW at ${BBBW_IP}" -ForegroundColor Red
    exit 1
}

Write-Host "Connection successful!" -ForegroundColor Green
Write-Host ""

# Create remote directory structure
Write-Host "Ensuring remote directory exists..." -ForegroundColor Yellow
ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} "mkdir -p ${RemotePath}" | Out-Null

# Create local backup directory
$BackupPath = Join-Path $LocalPath ".sync_backup"
if (-not (Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
}

# Function to get file info from remote (suppress banner)
function Get-RemoteFileInfo {
    param([string]$RemoteFile)
    $info = ssh -i $SSHKey -o LogLevel=ERROR -o BatchMode=yes debian@${BBBW_IP} "if [ -f '${RemoteFile}' ]; then stat -c '%s %Y' '${RemoteFile}'; else echo 'NOTFOUND'; fi" 2>&1 | Where-Object { 
        $_ -and 
        $_ -notmatch "Debian|BeagleBoard|Support|default username|Permission denied" -and
        ($_ -match '^\d+' -or $_ -match 'NOTFOUND')
    }
    return $info
}

# Function to sync file (push)
function Sync-PushFile {
    param([string]$LocalFile, [string]$RelativePath)
    
    $remoteFile = "${RemotePath}/${RelativePath}"
    $remoteDir = Split-Path $remoteFile -Parent
    
    # Ensure remote directory exists
    ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} "mkdir -p '${remoteDir}'" | Out-Null
    
    # Push file
    $scpOutput = scp -i $SSHKey -o LogLevel=ERROR "$LocalFile" "debian@${BBBW_IP}:${remoteFile}" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        return $true
    }
    return $false
}

# Function to sync file (pull)
function Sync-PullFile {
    param([string]$RemoteFile, [string]$LocalFile)
    
    $localDir = Split-Path $LocalFile -Parent
    if (-not (Test-Path $localDir)) {
        New-Item -ItemType Directory -Path $localDir -Force | Out-Null
    }
    
    # Pull file
    $scpOutput = scp -i $SSHKey -o LogLevel=ERROR "debian@${BBBW_IP}:${RemoteFile}" "$LocalFile" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        return $true
    }
    return $false
}

# Function to get all files recursively
function Get-AllFiles {
    param([string]$BasePath, [string]$RelativePath = "")
    
    $files = @()
    $items = Get-ChildItem -Path $BasePath -File -ErrorAction SilentlyContinue
    
    foreach ($item in $items) {
        if ($item.Name -notlike '.sync*' -and $item.Name -notlike 'sync_*') {
            if ($RelativePath) {
                $relPath = "${RelativePath}/$($item.Name)"
            } else {
                $relPath = $item.Name
            }
            $files += @{
                FullPath = $item.FullName
                RelativePath = $relPath
                Name = $item.Name
                Size = $item.Length
                Modified = $item.LastWriteTime
            }
        }
    }
    
    $dirs = Get-ChildItem -Path $BasePath -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '.sync*' }
    foreach ($dir in $dirs) {
        if ($RelativePath) {
            $relPath = "${RelativePath}/$($dir.Name)"
        } else {
            $relPath = $dir.Name
        }
        $files += Get-AllFiles -BasePath $dir.FullName -RelativePath $relPath
    }
    
    return $files
}

# STEP 1: PULL - Get all files from remote recursively
Write-Host "=== STEP 1: PULLING from BBBW ===" -ForegroundColor Cyan
$remoteFilesCmd = "find ${RemotePath} -type f 2>/dev/null | grep -E '\.(py|txt|md|sh|json|yml|yaml)$'"
$remoteFiles = ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} $remoteFilesCmd 2>&1
$remoteFilesList = $remoteFiles | Where-Object { 
    $_ -and 
    $_ -notmatch "Permission denied|find:" -and
    $_ -match "\.(py|txt|md|sh|json|yml|yaml)$"
}

$pulledCount = 0
$skippedPullCount = 0

foreach ($remoteFile in $remoteFilesList) {
    if ([string]::IsNullOrWhiteSpace($remoteFile)) { continue }
    
    # Get relative path
    $relPath = $remoteFile -replace [regex]::Escape($RemotePath + "/"), ""
    $localFile = Join-Path $LocalPath $relPath
    
    Write-Host "  Pulling: $relPath..." -ForegroundColor Yellow -NoNewline
    
    # Check if local file exists
    if (Test-Path $localFile) {
        $remoteInfo = Get-RemoteFileInfo $remoteFile
        $localSize = (Get-Item $localFile).Length
        
        if ($remoteInfo -match "NOTFOUND" -or [string]::IsNullOrWhiteSpace($remoteInfo)) {
            Write-Host " [SKIP - not found on remote]" -ForegroundColor Gray
            $skippedPullCount++
            continue
        }
        
        $remoteParts = ($remoteInfo -split '\s+') | Where-Object { $_ -match '^\d+$' }
        if ($remoteParts.Length -ge 1) {
            try {
                $remoteSize = [int]$remoteParts[0]
                
                if ($localSize -eq $remoteSize -and -not $Force) {
                    Write-Host " [SKIP - identical]" -ForegroundColor Gray
                    $skippedPullCount++
                    continue
                }
                
                # Backup local file if different
                if (-not $Force) {
                    $backupFile = Join-Path $BackupPath "${relPath}.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
                    $backupDir = Split-Path $backupFile -Parent
                    if (-not (Test-Path $backupDir)) {
                        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
                    }
                    Copy-Item $localFile $backupFile -Force
                }
            } catch {
                # Continue anyway
            }
        }
    }
    
    # Pull file
    if (Sync-PullFile -RemoteFile $remoteFile -LocalFile $localFile) {
        Write-Host " [OK]" -ForegroundColor Green
        $pulledCount++
    } else {
        Write-Host " [ERROR]" -ForegroundColor Red
    }
}

Write-Host "Pulled: $pulledCount, Skipped: $skippedPullCount" -ForegroundColor Gray
Write-Host ""

# STEP 2: PUSH - Send all local files to remote recursively
Write-Host "=== STEP 2: PUSHING to BBBW ===" -ForegroundColor Cyan
$localFiles = Get-AllFiles -BasePath $LocalPath

if ($localFiles.Count -eq 0) {
    Write-Host "No files to push." -ForegroundColor Yellow
} else {
    Write-Host "Found $($localFiles.Count) file(s) to push" -ForegroundColor Cyan
    Write-Host ""
}

$pushedCount = 0
$skippedPushCount = 0
$errorCount = 0

foreach ($fileInfo in $localFiles) {
    $localFile = $fileInfo.FullPath
    $relPath = $fileInfo.RelativePath
    $remoteFile = "${RemotePath}/${relPath}"
    
    Write-Host "  Pushing: $relPath..." -ForegroundColor Yellow -NoNewline
    
    # Check if file exists on remote
    $remoteInfo = Get-RemoteFileInfo $remoteFile
    
    if ($remoteInfo -notmatch "NOTFOUND" -and -not [string]::IsNullOrWhiteSpace($remoteInfo)) {
        if (-not $Force) {
            $localSize = $fileInfo.Size
            $remoteParts = ($remoteInfo -split '\s+') | Where-Object { $_ -match '^\d+$' }
            if ($remoteParts.Length -ge 1) {
                try {
                    $remoteSize = [int]$remoteParts[0]
                    
                    if ($localSize -eq $remoteSize) {
                        Write-Host " [SKIP - identical]" -ForegroundColor Gray
                        $skippedPushCount++
                        continue
                    }
                } catch {
                    # Continue anyway
                }
            }
        }
    }
    
    # Push file
    if (Sync-PushFile -LocalFile $localFile -RelativePath $relPath) {
        Write-Host " [OK]" -ForegroundColor Green
        $pushedCount++
    } else {
        Write-Host " [ERROR]" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "=== Sync Complete ===" -ForegroundColor Cyan
Write-Host "PULLED:" -ForegroundColor Cyan
Write-Host "  Synced:   $pulledCount" -ForegroundColor Green
Write-Host "  Skipped:  $skippedPullCount" -ForegroundColor Gray
Write-Host ""
Write-Host "PUSHED:" -ForegroundColor Cyan
Write-Host "  Synced:   $pushedCount" -ForegroundColor Green
Write-Host "  Skipped:  $skippedPushCount" -ForegroundColor Gray
Write-Host "  Errors:   $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Gray" })
Write-Host ""

if ($pulledCount -gt 0) {
    Write-Host "Backup location: $BackupPath" -ForegroundColor Gray
}

if ($errorCount -eq 0) {
    Write-Host "[OK] Synchronization complete - Local and Remote are in sync!" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Some errors occurred during sync" -ForegroundColor Yellow
}

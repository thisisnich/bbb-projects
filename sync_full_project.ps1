# Full project bidirectional sync
# Syncs ConnectedSystemClassroom to BBBW and pulls wk6 from BBBW

param(
    [Parameter(Mandatory=$false)]
    [string]$BBBW_IP = "192.168.7.2",
    
    [Parameter(Mandatory=$false)]
    [string]$SSHKey = "$env:USERPROFILE\.ssh\beaglebone_key",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

$ErrorActionPreference = "Continue"
# Get the project root (where this script is located)
$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
$LocalConnectedSystem = Join-Path $ProjectRoot "ConnectedSystemClassroom"
$RemoteBase = "/var/lib/cloud9"
$RemoteConnectedSystem = "${RemoteBase}/ConnectedSystemClassroom"
$RemoteWk6 = "${RemoteBase}/wk6"
$LocalWk6 = Join-Path $ProjectRoot "wk6"

Write-Host "=== Full Project Bidirectional Sync ===" -ForegroundColor Cyan
Write-Host "Local ConnectedSystemClassroom: $LocalConnectedSystem" -ForegroundColor Gray
Write-Host "Remote ConnectedSystemClassroom: debian@${BBBW_IP}:${RemoteConnectedSystem}" -ForegroundColor Gray
Write-Host "Local wk6: $LocalWk6" -ForegroundColor Gray
Write-Host "Remote wk6: debian@${BBBW_IP}:${RemoteWk6}" -ForegroundColor Gray
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

# Function to sync directory recursively
function Sync-Directory {
    param(
        [string]$LocalDir,
        [string]$RemoteDir,
        [string]$Direction = "Bidirectional"
    )
    
    Write-Host "=== Syncing: $LocalDir -> $RemoteDir ===" -ForegroundColor Cyan
    
    # Ensure remote directory exists
    ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} "mkdir -p '${RemoteDir}'" | Out-Null
    
    # Get all files recursively (excluding venv, __pycache__, .git, etc.)
    $files = Get-ChildItem -Path $LocalDir -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $_.FullName -notmatch '\\venv\\' -and
        $_.FullName -notmatch '\\__pycache__\\' -and
        $_.FullName -notmatch '\\.git\\' -and
        $_.FullName -notmatch '\\.sync' -and
        $_.Name -notlike '.*'
    }
    
    $syncedCount = 0
    $skippedCount = 0
    $errorCount = 0
    
    # Create all directories first
    Write-Host "Creating remote directories..." -ForegroundColor Gray
    $allDirs = $files | ForEach-Object {
        $relPath = $_.FullName -replace [regex]::Escape($LocalDir + "\"), "" -replace "\\", "/"
        $fullRemotePath = "${RemoteDir}/${relPath}"
        Split-Path $fullRemotePath -Parent
    } | Where-Object { $_ -and $_ -ne $RemoteDir } | Select-Object -Unique
    
    # Create directories in one command for efficiency
    if ($allDirs.Count -gt 0) {
        $dirsList = $allDirs -join " "
        ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} "mkdir -p $dirsList" 2>&1 | Out-Null
    }
    
    foreach ($file in $files) {
        $relPath = $file.FullName -replace [regex]::Escape($LocalDir + "\"), "" -replace "\\", "/"
        $remoteFile = "${RemoteDir}/${relPath}"
        
        Write-Host "  Syncing: $relPath..." -ForegroundColor Yellow -NoNewline
        
        # Check if file exists and compare sizes
        if (-not $Force) {
            $remoteInfo = ssh -i $SSHKey -o LogLevel=ERROR -o BatchMode=yes debian@${BBBW_IP} "if [ -f '${remoteFile}' ]; then stat -c '%s' '${remoteFile}'; else echo 'NOTFOUND'; fi" 2>&1 | Where-Object { 
                $_ -and $_ -match '^\d+$|NOTFOUND'
            }
            
            if ($remoteInfo -match '^\d+$') {
                $remoteSize = [int]$remoteInfo
                $localSize = $file.Length
                
                if ($localSize -eq $remoteSize) {
                    Write-Host " [SKIP - identical]" -ForegroundColor Gray
                    $skippedCount++
                    continue
                }
            }
        }
        
        # Sync file - ensure directory exists first, then copy
        $remoteFileEscaped = $remoteFile -replace "'", "'\''"
        $localFilePath = $file.FullName
        
        # Use rsync-style approach: create dir, then copy
        $scpOutput = scp -i $SSHKey -o LogLevel=ERROR "$localFilePath" "debian@${BBBW_IP}:${remoteFileEscaped}" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
            $syncedCount++
        } else {
            Write-Host " [ERROR]" -ForegroundColor Red
            if ($scpOutput) {
                Write-Host "    $scpOutput" -ForegroundColor DarkRed
            }
            $errorCount++
        }
    }
    
    Write-Host "Synced: $syncedCount, Skipped: $skippedCount, Errors: $errorCount" -ForegroundColor Gray
    Write-Host ""
    
    return @{
        Synced = $syncedCount
        Skipped = $skippedCount
        Errors = $errorCount
    }
}

# Function to pull directory from remote
function Pull-Directory {
    param(
        [string]$RemoteDir,
        [string]$LocalDir
    )
    
    Write-Host "=== Pulling: $RemoteDir -> $LocalDir ===" -ForegroundColor Cyan
    
    # Ensure local directory exists
    if (-not (Test-Path $LocalDir)) {
        New-Item -ItemType Directory -Path $LocalDir -Force | Out-Null
    }
    
    # Get list of files from remote
    $remoteFilesCmd = "find '${RemoteDir}' -type f 2>/dev/null"
    $remoteFiles = ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} $remoteFilesCmd 2>&1 | Where-Object {
        $_ -and $_ -notmatch "Permission denied|find:"
    }
    
    $pulledCount = 0
    $skippedCount = 0
    $errorCount = 0
    
    foreach ($remoteFile in $remoteFiles) {
        if ([string]::IsNullOrWhiteSpace($remoteFile)) { continue }
        
        # Get relative path
        $relPath = $remoteFile -replace [regex]::Escape($RemoteDir + "/"), ""
        $localFile = Join-Path $LocalDir $relPath
        $localFileDir = Split-Path $localFile -Parent
        
        # Ensure local directory exists
        if (-not (Test-Path $localFileDir)) {
            New-Item -ItemType Directory -Path $localFileDir -Force | Out-Null
        }
        
        Write-Host "  Pulling: $relPath..." -ForegroundColor Yellow -NoNewline
        
        # Check if local file exists and compare
        if ((Test-Path $localFile) -and (-not $Force)) {
            $remoteInfo = ssh -i $SSHKey -o LogLevel=ERROR -o BatchMode=yes debian@${BBBW_IP} "stat -c '%s' '${remoteFile}'" 2>&1 | Where-Object { $_ -match '^\d+$' }
            $localSize = (Get-Item $localFile).Length
            
            if ($remoteInfo -and [int]$remoteInfo -eq $localSize) {
                Write-Host " [SKIP - identical]" -ForegroundColor Gray
                $skippedCount++
                continue
            }
        }
        
        # Pull file
        $scpOutput = scp -i $SSHKey -o LogLevel=ERROR -r "debian@${BBBW_IP}:${remoteFile}" "$localFile" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
            $pulledCount++
        } else {
            Write-Host " [ERROR]" -ForegroundColor Red
            $errorCount++
        }
    }
    
    Write-Host "Pulled: $pulledCount, Skipped: $skippedCount, Errors: $errorCount" -ForegroundColor Gray
    Write-Host ""
    
    return @{
        Synced = $pulledCount
        Skipped = $skippedCount
        Errors = $errorCount
    }
}

# STEP 1: Push ConnectedSystemClassroom to BBBW
if (Test-Path $LocalConnectedSystem) {
    $result1 = Sync-Directory -LocalDir $LocalConnectedSystem -RemoteDir $RemoteConnectedSystem
} else {
    Write-Host "WARNING: Local ConnectedSystemClassroom not found at: $LocalConnectedSystem" -ForegroundColor Yellow
    Write-Host ""
}

# STEP 2: Pull wk6 from BBBW
Write-Host "Checking for wk6 on BBBW..." -ForegroundColor Yellow
$wk6Exists = ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} "test -d '${RemoteWk6}' && echo 'EXISTS' || echo 'NOTFOUND'" 2>&1 | Where-Object { $_ -match 'EXISTS|NOTFOUND' }

if ($wk6Exists -match 'EXISTS') {
    $result2 = Pull-Directory -RemoteDir $RemoteWk6 -LocalDir $LocalWk6
} else {
    Write-Host "WARNING: wk6 folder not found on BBBW at: ${RemoteWk6}" -ForegroundColor Yellow
    Write-Host ""
}

# STEP 3: Check for additional BBBW client files in MyFirstPythonProject
Write-Host "Checking for additional BBBW client files..." -ForegroundColor Yellow
$remoteMyFirstPython = "${RemoteBase}/MyFirstPythonProject"
$clientFiles = ssh -i $SSHKey -o LogLevel=ERROR debian@${BBBW_IP} "find '${remoteMyFirstPython}' -maxdepth 1 -type f \( -iname '*reed*' -o -iname '*door*' -o -iname '*bbbw*' -o -iname '*client*' \) 2>/dev/null" 2>&1 | Where-Object {
    $_ -and $_ -notmatch "Permission denied|find:"
}

if ($clientFiles) {
    Write-Host "Found additional client files in MyFirstPythonProject:" -ForegroundColor Cyan
    foreach ($remoteFile in $clientFiles) {
        if ([string]::IsNullOrWhiteSpace($remoteFile)) { continue }
        $fileName = Split-Path $remoteFile -Leaf
        $localFile = Join-Path $LocalConnectedSystem "BBBW_Clients/$fileName"
        
        # Skip if already exists locally with same name
        if (-not (Test-Path $localFile)) {
            Write-Host "  Pulling: $fileName..." -ForegroundColor Yellow -NoNewline
            $scpOutput = scp -i $SSHKey -o LogLevel=ERROR "debian@${BBBW_IP}:${remoteFile}" "$localFile" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host " [OK]" -ForegroundColor Green
            } else {
                Write-Host " [ERROR]" -ForegroundColor Red
            }
        } else {
            Write-Host "  Skipping: $fileName (already exists locally)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

Write-Host "=== Sync Complete ===" -ForegroundColor Cyan
Write-Host "[OK] Full project synchronization complete!" -ForegroundColor Green


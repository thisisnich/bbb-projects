# File watcher that automatically syncs on file save
# Watches local files and syncs to BBBW on save

param(
    [Parameter(Mandatory=$false)]
    [string]$BBBW_IP = "192.168.7.2",
    
    [Parameter(Mandatory=$false)]
    [string]$RemotePath = "/var/lib/cloud9/BBBW_Clients",
    
    [Parameter(Mandatory=$false)]
    [string]$SSHKey = "$env:USERPROFILE\.ssh\beaglebone_key"
)

$LocalPath = $PSScriptRoot
$SyncScript = Join-Path $LocalPath "sync_bidirectional.ps1"

Write-Host "=== File Watcher - Auto Sync on Save ===" -ForegroundColor Cyan
Write-Host "Watching: $LocalPath" -ForegroundColor Gray
Write-Host "Remote: debian@${BBBW_IP}:${RemotePath}" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Load FileSystemWatcher
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $LocalPath
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

# Filter for relevant file types
$watcher.Filter = "*.*"
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::FileName

# Debounce timer to avoid multiple syncs
$syncTimer = $null
$syncQueue = New-Object System.Collections.ArrayList

# Function to perform sync
function Invoke-Sync {
    param([string[]]$Files)
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Syncing changes..." -ForegroundColor Cyan
    foreach ($file in $Files) {
        $relPath = $file -replace [regex]::Escape($LocalPath + "\"), "" -replace "\\", "/"
        Write-Host "  - $relPath" -ForegroundColor Gray
    }
    
    # Run sync script
    & $SyncScript -BBBW_IP $BBBW_IP -RemotePath $RemotePath -SSHKey $SSHKey -Force | Out-Null
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Sync complete" -ForegroundColor Green
    Write-Host ""
}

# Event handler for file changes
$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    $name = $Event.SourceEventArgs.Name
    
    # Skip sync files and backup directory
    if ($path -like "*\.sync*" -or $path -like "*\sync_*" -or $name -like ".*") {
        return
    }
    
    # Only watch relevant file types
    if ($path -match "\.(py|txt|md|sh|json|yml|yaml|html|css|js)$") {
        if (-not $syncQueue.Contains($path)) {
            [void]$syncQueue.Add($path)
        }
        
        # Debounce: wait 2 seconds after last change before syncing
        if ($syncTimer) {
            $syncTimer.Stop()
        }
        
        $syncTimer = New-Object System.Timers.Timer(2000)
        $syncTimer.AutoReset = $false
        $syncTimer.add_Elapsed({
            $filesToSync = $syncQueue.ToArray()
            $syncQueue.Clear()
            Invoke-Sync -Files $filesToSync
        })
        $syncTimer.Start()
    }
}

# Register event handlers
Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $action | Out-Null

Write-Host "File watcher started. Monitoring for changes..." -ForegroundColor Green
Write-Host ""

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "File watcher stopped." -ForegroundColor Yellow
}


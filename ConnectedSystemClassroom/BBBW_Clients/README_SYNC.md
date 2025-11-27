# Complete Sync Guide

## Quick Sync (One-time)

### Bidirectional Sync (Recommended)
Syncs both ways - pulls from BBBW and pushes to BBBW:
```powershell
.\sync_bidirectional.ps1 -BBBW_IP "192.168.7.2"
```

**Features:**
- ✅ Syncs folders recursively
- ✅ Handles all file types (py, txt, md, sh, json, yml, yaml, html, css, js)
- ✅ Compares file sizes to skip identical files
- ✅ Backs up local files before overwriting
- ✅ 100% synchronization

## Auto-Sync on Save

### Start File Watcher
Automatically syncs when you save any file:
```powershell
.\watch_and_sync.ps1 -BBBW_IP "192.168.7.2"
```

**How it works:**
- Watches all files in the BBBW_Clients folder (and subfolders)
- Detects when you save a file
- Waits 2 seconds (debounce) to catch multiple rapid saves
- Automatically runs bidirectional sync
- Press Ctrl+C to stop

**What gets synced:**
- `.py` - Python files
- `.txt` - Text files
- `.md` - Markdown files
- `.sh` - Shell scripts
- `.json` - JSON files
- `.yml`, `.yaml` - YAML files
- `.html` - HTML files
- `.css` - CSS files
- `.js` - JavaScript files

## Sync Options

### Force Sync (Overwrite Everything)
```powershell
.\sync_bidirectional.ps1 -BBBW_IP "192.168.7.2" -Force
```

### Custom Remote Path
```powershell
.\sync_bidirectional.ps1 -BBBW_IP "192.168.7.2" -RemotePath "/home/debian/myproject"
```

### Custom SSH Key
```powershell
.\sync_bidirectional.ps1 -BBBW_IP "192.168.7.2" -SSHKey "C:\path\to\key"
```

## Folder Structure

The sync script handles nested folders:
```
BBBW_Clients/
├── BBBW2_Potentiometer.py
├── subfolder/
│   └── file.py
└── another_folder/
    └── config.json
```

All folders and files are synced recursively.

## Troubleshooting

### Files not syncing?
- Check SSH connection: `ssh -i $env:USERPROFILE\.ssh\beaglebone_key debian@192.168.7.2`
- Verify file types are included (see list above)
- Check file permissions on BBBW

### Watcher not detecting changes?
- Make sure you're saving files (not just editing)
- Check that file extension is supported
- Verify watcher is running (should show "File watcher started")

### Sync errors?
- Check disk space on BBBW: `ssh debian@192.168.7.2 "df -h"`
- Verify remote directory exists: `ssh debian@192.168.7.2 "ls -la /var/lib/cloud9/BBBW_Clients"`

## Best Practices

1. **Start watcher in background** for continuous sync:
   ```powershell
   Start-Process powershell -ArgumentList "-File", "watch_and_sync.ps1" -WindowStyle Minimized
   ```

2. **Manual sync before important changes**:
   ```powershell
   .\sync_bidirectional.ps1
   ```

3. **Check sync status** - The script shows what was synced/skipped

4. **Backups** - Local files are backed up to `.sync_backup/` before being overwritten


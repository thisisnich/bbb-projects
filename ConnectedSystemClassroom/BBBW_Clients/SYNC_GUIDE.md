# File Sync Guide for BBBW Clients

This guide explains how to sync your BBBW client files to the BeagleBone Black Wireless board, handling differences gracefully.

## Methods

### Method 1: PowerShell Sync Script (Recommended for Windows)

The `sync_to_bbbw.ps1` script automatically handles file differences:

```powershell
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\BBBW_Clients"
.\sync_to_bbbw.ps1 -BBBW_IP "192.168.7.2"
```

**Options:**
- `-BBBW_IP "192.168.X.X"` - BBBW IP address (default: 192.168.7.2 for USB)
- `-RemotePath "/path/on/bbbw"` - Remote directory (default: /var/lib/cloud9/BBBW_Clients)
- `-SSHKey "path/to/key"` - SSH key path (default: $env:USERPROFILE\.ssh\beaglebone_key)
- `-Force` - Force overwrite without checking differences

**Features:**
- ✅ Tests SSH connection before syncing
- ✅ Compares file sizes to skip identical files
- ✅ Warns when files differ (unless -Force is used)
- ✅ Shows sync progress and summary

### Method 2: Bash Sync Script (Linux/Mac/WSL)

```bash
cd ConnectedSystemClassroom/BBBW_Clients
chmod +x sync_to_bbbw.sh
./sync_to_bbbw.sh [BBBW_IP] [REMOTE_PATH] [SSH_KEY_PATH] [FORCE]
```

**Example:**
```bash
./sync_to_bbbw.sh "192.168.7.2" "/var/lib/cloud9/BBBW_Clients" "$HOME/.ssh/beaglebone_key" "false"
```

### Method 3: Manual SCP (One-time sync)

**Windows PowerShell:**
```powershell
$SSH_KEY = "$env:USERPROFILE\.ssh\beaglebone_key"
$BBBW_IP = "192.168.7.2"
scp -i $SSH_KEY BBBW2_Potentiometer.py debian@${BBBW_IP}:/var/lib/cloud9/BBBW_Clients/
```

**Linux/Mac:**
```bash
scp -i ~/.ssh/beaglebone_key BBBW2_Potentiometer.py debian@192.168.7.2:/var/lib/cloud9/BBBW_Clients/
```

### Method 4: SFTP Extension in Cursor/VS Code

1. Install SFTP extension (Natizyskunk)
2. The `.vscode/sftp.json` is already configured
3. Files auto-upload on save (if configured)

**Note:** Update the `privateKeyPath` in `.vscode/sftp.json` if needed.

## Handling Differences

The sync scripts handle differences gracefully:

1. **File doesn't exist on remote:** Uploads automatically
2. **Files are identical (same size):** Skips upload
3. **Files differ:** 
   - Shows warning with file sizes
   - Prompts to continue (unless `-Force` is used)
   - Overwrites remote file

## Troubleshooting

### Connection Issues

**Error: Cannot connect to BBBW**
- Check BBBW is powered on and connected (USB or WiFi)
- Verify IP address: `ping 192.168.7.2` (or your WiFi IP)
- Test SSH manually: `ssh -i $env:USERPROFILE\.ssh\beaglebone_key debian@192.168.7.2`

**Error: Permission denied**
- Ensure SSH key is authorized on BBBW
- Check key permissions: `icacls $env:USERPROFILE\.ssh\beaglebone_key`
- Re-add key to BBBW if needed (see beaglebone-setup.md)

### File Sync Issues

**Files not syncing:**
- Check remote directory exists: `ssh debian@192.168.7.2 "ls -la /var/lib/cloud9/BBBW_Clients"`
- Verify file permissions on BBBW
- Check disk space: `ssh debian@192.168.7.2 "df -h"`

**Files differ but should be same:**
- Check line endings (Windows vs Linux)
- Verify file encoding (UTF-8)
- Use `-Force` flag to overwrite

## WiFi vs USB Connection

**USB Connection (default):**
- IP: `192.168.7.2`
- No network setup needed
- Use when BBBW is connected via USB cable

**WiFi Connection:**
- IP: Check with `ssh debian@192.168.7.2 "hostname -I"` or check your router
- Both PC and BBBW must be on same WiFi network
- Update `-BBBW_IP` parameter accordingly

## Quick Reference

```powershell
# Sync with default settings (USB)
.\sync_to_bbbw.ps1

# Sync to WiFi-connected BBBW
.\sync_to_bbbw.ps1 -BBBW_IP "192.168.1.100"

# Force overwrite all files
.\sync_to_bbbw.ps1 -Force

# Custom remote path
.\sync_to_bbbw.ps1 -RemotePath "/home/debian/myproject"
```


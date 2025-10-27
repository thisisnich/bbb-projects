# BeagleBone Black + Cursor IDE Setup Guide

## Problem
Cursor's Remote SSH extension doesn't support ARMv7l architecture (32-bit ARM) used by the BeagleBone Black. The error you'll see is:
```
Architecture not supported: armv7l
```

**Solution:** Use SFTP extension to sync files locally while editing in Cursor, with automatic upload to the BeagleBone.

## Prerequisites
- BeagleBone Black connected via USB (192.168.7.2)
- Default credentials: `debian:temppwd`
- Cursor IDE installed
- SSH access working

## Step 1: Generate SSH Key
In PowerShell:
```powershell
ssh-keygen -t rsa -b 4096 -f $env:USERPROFILE\.ssh\beaglebone_key -N '""'
```

## Step 2: Add Key to BeagleBone
1. Get your public key:
   ```powershell
   type $env:USERPROFILE\.ssh\beaglebone_key.pub
   ```

2. Connect to BeagleBone:
   ```powershell
   ssh debian@192.168.7.2
   # Enter password: temppwd
   ```

3. On the BeagleBone:
   ```bash
   mkdir -p ~/.ssh
   nano ~/.ssh/authorized_keys
   # Paste the public key, Ctrl+O, Enter, Ctrl+X
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   exit
   ```

## Step 3: Configure SSH
Create/Edit: `C:\Users\user\.ssh\config`
```
Host beaglebone
    HostName 192.168.7.2
    User debian
    IdentityFile C:\Users\user\.ssh\beaglebone_key
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

## Step 4: Install SFTP Extension
In Cursor, press Ctrl+Shift+X, search "SFTP" (Natizyskunk), Install

## Step 5: Create SFTP Config
Create `.vscode/sftp.json` in your project:
```json
{
    "name": "BeagleBone Black",
    "host": "192.168.7.2",
    "protocol": "sftp",
    "port": 22,
    "username": "debian",
    "remotePath": "/var/lib/cloud9",
    "uploadOnSave": true,
    "useTempFile": false,
    "privateKeyPath": "C:/Users/user/.ssh/beaglebone_key",
    "ignore": [".vscode", ".git", "node_modules", "*.pyc"],
    "watcher": {
        "files": "**/*",
        "autoUpload": true,
        "autoDelete": false
    }
}
```

## Usage
1. Edit files in Cursor
2. Press Ctrl+S to save (auto-uploads)
3. SSH into BeagleBone to run: `ssh beaglebone`

## Quick Commands
```powershell
# Connect
ssh beaglebone

# Copy file to BeagleBone
scp -i C:\Users\user\.ssh\beaglebone_key myfile.py debian@192.168.7.2:/var/lib/cloud9/

# Copy from BeagleBone
scp -i C:\Users\user\.ssh\beaglebone_key debian@192.168.7.2:/var/lib/cloud9/myfile.py ./
```

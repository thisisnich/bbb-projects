#!/bin/bash
# Bash script to sync BBBW client files to BeagleBone Black Wireless board
# Handles differences gracefully by checking file existence and comparing sizes

BBBW_IP="${1:-192.168.7.2}"  # Default USB IP, change if using WiFi
REMOTE_PATH="${2:-/var/lib/cloud9/BBBW_Clients}"
SSH_KEY="${3:-$HOME/.ssh/beaglebone_key}"
FORCE="${4:-false}"

LOCAL_PATH="$(cd "$(dirname "$0")" && pwd)"

echo "=== BBBW Client File Sync ==="
echo "Source: $LOCAL_PATH"
echo "Destination: debian@${BBBW_IP}:${REMOTE_PATH}"
echo ""

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "ERROR: SSH key not found at: $SSH_KEY"
    echo "Please generate SSH key first using:"
    echo "  ssh-keygen -t rsa -b 4096 -f $SSH_KEY -N ''"
    exit 1
fi

# Test SSH connection
echo "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o BatchMode=yes debian@"${BBBW_IP}" "echo 'connected'" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to BBBW at ${BBBW_IP}"
    echo "Make sure:"
    echo "  1. BBBW is connected (USB or WiFi)"
    echo "  2. IP address is correct (current: ${BBBW_IP})"
    echo "  3. SSH key is authorized on BBBW"
    echo ""
    echo "To connect manually: ssh -i $SSH_KEY debian@${BBBW_IP}"
    exit 1
fi

echo "Connection successful!"
echo ""

# Create remote directory if it doesn't exist
echo "Creating remote directory if needed..."
ssh -i "$SSH_KEY" debian@"${BBBW_IP}" "mkdir -p ${REMOTE_PATH}" > /dev/null 2>&1

# Get list of Python files to sync
FILES_TO_SYNC=($(find "$LOCAL_PATH" -maxdepth 1 -name "*.py" -type f))

if [ ${#FILES_TO_SYNC[@]} -eq 0 ]; then
    echo "No Python files found to sync."
    exit 0
fi

echo "Found ${#FILES_TO_SYNC[@]} file(s) to sync:"
for file in "${FILES_TO_SYNC[@]}"; do
    echo "  - $(basename "$file")"
done
echo ""

# Sync each file
SYNCED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0

for local_file in "${FILES_TO_SYNC[@]}"; do
    filename=$(basename "$local_file")
    remote_file="${REMOTE_PATH}/${filename}"
    
    echo -n "Syncing: ${filename}... "
    
    # Check if file exists on remote
    if ssh -i "$SSH_KEY" debian@"${BBBW_IP}" "test -f ${remote_file}" 2>/dev/null; then
        if [ "$FORCE" != "true" ]; then
            # Get file sizes for comparison
            local_size=$(stat -f%z "$local_file" 2>/dev/null || stat -c%s "$local_file" 2>/dev/null)
            remote_size=$(ssh -i "$SSH_KEY" debian@"${BBBW_IP}" "stat -c%s ${remote_file}" 2>/dev/null)
            
            if [ "$local_size" = "$remote_size" ]; then
                echo "[SKIP - identical]"
                ((SKIPPED_COUNT++))
                continue
            fi
            
            # Files differ
            echo ""
            echo "  WARNING: Remote file exists and differs!"
            echo "  Local size:  $local_size bytes"
            echo "  Remote size: $remote_size bytes"
            echo "  Remote file will be overwritten."
        fi
    fi
    
    # Copy file using SCP
    if scp -i "$SSH_KEY" "$local_file" "debian@${BBBW_IP}:${remote_file}" > /dev/null 2>&1; then
        echo "[OK]"
        ((SYNCED_COUNT++))
    else
        echo "[ERROR]"
        ((ERROR_COUNT++))
    fi
done

echo ""
echo "=== Sync Complete ==="
echo "Synced:   $SYNCED_COUNT"
echo "Skipped:  $SKIPPED_COUNT"
echo "Errors:   $ERROR_COUNT"
echo ""

if [ $ERROR_COUNT -eq 0 ]; then
    echo "To run on BBBW:"
    echo "  ssh -i $SSH_KEY debian@${BBBW_IP}"
    echo "  cd ${REMOTE_PATH}"
    echo "  sudo python3 BBBW2_Potentiometer.py"
fi


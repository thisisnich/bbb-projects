# Script to automatically add SSH key to BBBW board
# This will use password authentication to add the key

param(
    [Parameter(Mandatory=$false)]
    [string]$BBBW_IP = "192.168.7.2",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "temppwd"
)

$SSH_KEY = "$env:USERPROFILE\.ssh\beaglebone_key.pub"

if (-not (Test-Path $SSH_KEY)) {
    Write-Host "ERROR: Public key not found at: $SSH_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "=== Setting up SSH key on BBBW ===" -ForegroundColor Cyan
Write-Host "BBBW IP: $BBBW_IP" -ForegroundColor Gray
Write-Host ""

# Read the public key
$publicKey = Get-Content $SSH_KEY -Raw
$publicKey = $publicKey.Trim()

Write-Host "Public key to add:" -ForegroundColor Yellow
Write-Host $publicKey -ForegroundColor Gray
Write-Host ""

# Create a temporary script to run on BBBW
$remoteScript = @"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
if ! grep -Fxq "$publicKey" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$publicKey" >> ~/.ssh/authorized_keys
    echo "Key added successfully"
else
    echo "Key already exists"
fi
chmod 600 ~/.ssh/authorized_keys
echo "Setup complete"
"@

# Save script to temp file
$tempScript = [System.IO.Path]::GetTempFileName()
$remoteScript | Out-File -FilePath $tempScript -Encoding ASCII

Write-Host "Adding SSH key to BBBW..." -ForegroundColor Yellow
Write-Host "You will be prompted for password: $Password" -ForegroundColor Gray
Write-Host ""

# Use plink or ssh with expect-like behavior
# Try using ssh with password via here-string
$sshCommand = @"
bash -c '
mkdir -p ~/.ssh
chmod 700 ~/.ssh
if ! grep -Fxq "$publicKey" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$publicKey" >> ~/.ssh/authorized_keys
    echo "Key added successfully"
else
    echo "Key already exists"
fi
chmod 600 ~/.ssh/authorized_keys
echo "Setup complete"
'
"@

# Try using sshpass if available, otherwise manual
Write-Host "Attempting to add key automatically..." -ForegroundColor Yellow
Write-Host "If this fails, you'll need to do it manually:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Connect: ssh debian@$BBBW_IP" -ForegroundColor Cyan
Write-Host "2. Run these commands:" -ForegroundColor Cyan
Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Gray
Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Gray
Write-Host "   nano ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host "   # Paste the key above, then Ctrl+O, Enter, Ctrl+X" -ForegroundColor Gray
Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host ""

# Try to use ssh with password (requires sshpass or manual entry)
Write-Host "Trying manual SSH connection..." -ForegroundColor Yellow
Write-Host "Please run this command and enter password '$Password':" -ForegroundColor Yellow
Write-Host ""
Write-Host "ssh debian@$BBBW_IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then paste this command:" -ForegroundColor Yellow
Write-Host "echo '$publicKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh" -ForegroundColor Cyan
Write-Host ""

# Clean up
Remove-Item $tempScript -ErrorAction SilentlyContinue

Write-Host "After adding the key, test connection with:" -ForegroundColor Yellow
Write-Host "ssh -i $env:USERPROFILE\.ssh\beaglebone_key debian@$BBBW_IP" -ForegroundColor Cyan


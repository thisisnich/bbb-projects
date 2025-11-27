# BBBW Client Code for Connected System Classroom

This folder contains the client code for each BeagleBone Black Wireless (BBBW) board.

## Files

- `BBBW2_Potentiometer.py` - Pot Click board for lighting control

## Setup Instructions

### 1. Sync Files to BBBW

**Quick Sync (PowerShell - Windows):**
```powershell
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\BBBW_Clients"
.\sync_to_bbbw.ps1 -BBBW_IP "192.168.7.2"
```

**For WiFi-connected BBBW:**
```powershell
.\sync_to_bbbw.ps1 -BBBW_IP "192.168.1.XXX"  # Replace with your BBBW WiFi IP
```

See `SYNC_GUIDE.md` for detailed sync instructions and troubleshooting.

### 2. Install Required Packages on BBBW

On your BBBW board (via Cloud9 or SSH), install:
```bash
sudo python3 -m pip install python-socketio Adafruit_BBIO
```

### 3. Update IP Address

Before running any client code, you must update the IP address in the Python file:

1. Find your PC's IP address (run `ipconfig` on Windows)
2. Update the `SERVER_IP` variable in the client code

For example, if your PC IP is `192.168.1.80`, change:
```python
SERVER_IP = '192.168.7.1'  # Change this to your PC's IP address
```
to:
```python
SERVER_IP = '192.168.1.80'  # Change this to your PC's IP address
```

**Note:** After updating, re-sync the file to BBBW using the sync script.

### 4. Running the Client

**Via SSH:**
```bash
ssh debian@192.168.7.2  # or your BBBW IP
cd /var/lib/cloud9/BBBW_Clients
sudo python3 BBBW2_Potentiometer.py
```

**In Cloud9 IDE:**
1. Files should already be synced
2. Open the file in Cloud9
3. Click the "Run" button

## BBBW2 - Potentiometer Board

- **Hardware:** Pot Click connected to mikroBUS Cape
- **Pin:** P9_37 (ADC)
- **Function:** Reads potentiometer value and sends to web server for lighting control
- **Data:** Sends brightness level (0.0 to 1.0) when value changes by more than 0.1

### How it works:
1. Continuously reads ADC value from P9_37
2. Compares with previous value
3. If change > 0.1, sends new value to web server via `BBBW2Event`
4. Web server updates the lighting brightness visualization

## Troubleshooting

- **Connection Error:** Make sure the web server is running on your PC
- **No Data:** Check that BBBW and PC are on the same Wi-Fi network
- **ADC Error:** Ensure Pot Click is properly connected to mikroBUS Cape


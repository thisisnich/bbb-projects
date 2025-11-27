# Connected System Classroom Web Server Setup

## Folder Structure
```
ConnectedSystemClassroom/
└── MyWebServer/
    ├── WebServer.py
    ├── templates/
    │   └── index.html
    └── static/
        ├── css/
        │   └── style.css
        └── images/
            └── (7 images from lab6b_images.zip)
```

## Setup Instructions

### 1. Virtual Environment Setup (Recommended)

A virtual environment has already been created. To activate it:

**PowerShell (if execution policy allows):**
```powershell
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
.\venv\Scripts\Activate.ps1
```

**PowerShell (if you get execution policy error - use batch file instead):**
```powershell
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
.\venv\Scripts\activate.bat
```

**Command Prompt:**
```cmd
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
venv\Scripts\activate
```

**Alternative: Use venv Python directly (no activation needed):**
```powershell
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
.\venv\Scripts\python.exe WebServer.py
```

**Note:** If you get an execution policy error in PowerShell, you can either:
1. Use the batch file method above, or
2. Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` (may require admin)
3. Use the direct Python method (no activation needed)

All required packages are already installed in the virtual environment. If you need to reinstall them:
```bash
pip install -r requirements.txt
```

### 2. Get Your PC's IP Address

In Command Prompt, run:
```bash
ipconfig
```

Look for your wireless adapter's IPv4 address (e.g., 192.168.1.80)

### 3. Update IP Address in Files

You need to replace `192.168.X.X` with your actual IP address in:
- `WebServer.py` (line 30: `wsgi.server(eventlet.listen(("192.168.X.X", 5000)), app)`)
- `templates/index.html` (line 30: `var socket = io.connect('http://192.168.X.X:5000');`)

### 4. Download and Add Images

1. Download `lab6b_images.zip` from Blackboard
2. Unzip the file
3. Copy all 7 images to `static/images/` folder:
   - Floorplan.png
   - MotionSensorIconBlue.png
   - MotionSensorIconRed.png
   - LightBulb.png
   - Keypad.png
   - DoorOpen.png
   - DoorClose.png

### 5. Run the Web Server

**With Virtual Environment (Recommended):**

PowerShell (Method 1 - Direct Python):
```powershell
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
.\venv\Scripts\python.exe WebServer.py
```

PowerShell (Method 2 - Activate then run):
```powershell
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
.\venv\Scripts\activate.bat
python WebServer.py
```

Command Prompt:
```cmd
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
venv\Scripts\activate
python WebServer.py
```

**Without Virtual Environment:**
```bash
cd "C:\Users\Nicholas Dubs\Documents\GitHub\bbb-projects\ConnectedSystemClassroom\MyWebServer"
python WebServer.py
```

Or in Python IDLE:
- Open `WebServer.py` in IDLE
- Click Run > Run Module

### 6. Access the Web Server

Open a web browser and navigate to:
```
http://YOUR_IP_ADDRESS:5000
```

Replace `YOUR_IP_ADDRESS` with the IP address you found in step 2.

## Notes

- The web server will run on port 5000
- Make sure your PC and BBBW boards are on the same Wi-Fi network
- The server must be running before the BBBW clients can connect


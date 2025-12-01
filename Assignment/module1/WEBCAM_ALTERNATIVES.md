# Webcam Capture Alternatives for BBBW

## Current: fswebcam
- **Install:** `sudo apt-get install fswebcam`
- **Pros:** Lightweight, simple, usually pre-installed
- **Cons:** None really

## Alternative Options

### Option 1: v4l2-utils (v4l2grab)
**Install:**
```bash
sudo apt-get install v4l-utils
```

**Code change:**
```python
def capture_and_encode_frame():
    """Capture frame using v4l2grab"""
    try:
        result = subprocess.run([
            'v4l2grab',
            '-d', WEBCAM_DEVICE,
            '-W', '640',
            '-H', '480',
            '-q', '85',
            '-o', '-'  # Output to stdout
        ], capture_output=True, timeout=3)
        
        if result.returncode == 0 and len(result.stdout) > 0:
            frame_base64 = base64.b64encode(result.stdout).decode('utf-8')
            return frame_base64
    except Exception as e:
        print(f'[WEBCAM] Error: {e}')
    return None
```

### Option 2: ffmpeg
**Install:**
```bash
sudo apt-get install ffmpeg
```

**Code change:**
```python
def capture_and_encode_frame():
    """Capture frame using ffmpeg"""
    try:
        result = subprocess.run([
            'ffmpeg',
            '-f', 'v4l2',
            '-i', WEBCAM_DEVICE,
            '-vf', 'scale=640:480',
            '-vframes', '1',
            '-q:v', '2',  # Quality (2 = high quality)
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-'  # Output to stdout
        ], capture_output=True, timeout=3, stderr=subprocess.DEVNULL)
        
        if result.returncode == 0 and len(result.stdout) > 0:
            frame_base64 = base64.b64encode(result.stdout).decode('utf-8')
            return frame_base64
    except Exception as e:
        print(f'[WEBCAM] Error: {e}')
    return None
```

### Option 3: streamer
**Install:**
```bash
sudo apt-get install streamer
```

**Code change:**
```python
def capture_and_encode_frame():
    """Capture frame using streamer"""
    try:
        result = subprocess.run([
            'streamer',
            '-c', WEBCAM_DEVICE,
            '-s', '640x480',
            '-o', '-'  # Output to stdout
        ], capture_output=True, timeout=3)
        
        if result.returncode == 0 and len(result.stdout) > 0:
            frame_base64 = base64.b64encode(result.stdout).decode('utf-8')
            return frame_base64
    except Exception as e:
        print(f'[WEBCAM] Error: {e}')
    return None
```

## Recommendation

**Stick with fswebcam** - It's:
- ✅ Lightweight
- ✅ Usually pre-installed on Debian/BeagleBone
- ✅ Simple and reliable
- ✅ No complex dependencies

**Only switch if:**
- fswebcam doesn't work with your specific webcam
- You need specific features fswebcam doesn't provide
- You already have another tool installed

## To Switch Tools

1. Install your chosen tool
2. Update the `capture_and_encode_frame()` function in `Module1_CrowdDetection_Client.py`
3. Update `check_fswebcam()` function to check for your tool instead
4. Test!


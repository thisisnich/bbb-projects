# Theoretical Frame Rate Analysis

## Current Setup (fswebcam subprocess)
- **Current Rate:** 5 FPS
- **Bottleneck:** Subprocess overhead (~100-300ms per call)

## Theoretical Maximums

### 1. **fswebcam Subprocess Method** (Current)
- **Max Theoretical:** ~8-12 FPS
- **Limiting Factors:**
  - Subprocess creation overhead: ~50-100ms
  - Camera initialization per call: ~50-100ms
  - JPEG encoding: ~50-100ms
  - Total per frame: ~150-300ms = 3-6 FPS practical, 8-12 FPS theoretical max

### 2. **OpenCV Direct Capture** (Better option)
- **Max Theoretical:** 15-30 FPS
- **Limiting Factors:**
  - Direct camera access (no subprocess overhead)
  - Camera buffer management
  - JPEG encoding: ~20-50ms
  - Total per frame: ~33-66ms = 15-30 FPS possible

### 3. **USB 2.0 Bandwidth**
- **Theoretical:** 480 Mbps = 60 MB/s
- **Frame size:** ~30-50 KB (640x480 JPEG 85%)
- **At 30 FPS:** ~900 KB/s - 1.5 MB/s = 7-12 Mbps
- **Verdict:** USB bandwidth is NOT a limiting factor

### 4. **Network Bandwidth**
- **WiFi (802.11n):** 54-300 Mbps
- **USB Network:** ~100 Mbps
- **Base64 overhead:** +33% = ~1.2-2 MB/s at 30 FPS
- **Verdict:** Network bandwidth is NOT a limiting factor (even at 30 FPS)

### 5. **Base64 Encoding**
- **Overhead:** ~33% size increase
- **CPU time:** Minimal (~5-10ms per frame)
- **Verdict:** Not a significant bottleneck

### 6. **SocketIO Transmission**
- **Overhead:** Event emission is fast
- **Can handle:** 30+ FPS easily
- **Verdict:** Not a limiting factor

## Practical Maximums by Method

| Method | Resolution | FPS | Notes |
|--------|-----------|-----|-------|
| **fswebcam (current)** | 640x480 | 5-8 FPS | Subprocess overhead |
| **fswebcam optimized** | 320x240 | 10-15 FPS | Lower resolution helps |
| **OpenCV direct** | 640x480 | 15-25 FPS | Much faster |
| **OpenCV direct** | 320x240 | 25-30 FPS | Near camera max |
| **MJPEG stream** | 640x480 | 30 FPS | Hardware accelerated |

## Recommendations

### To reach 15-20 FPS:
1. Switch to OpenCV direct capture (cv2.VideoCapture)
2. Keep 640x480 resolution
3. Use lower JPEG quality (70-75%)

### To reach 25-30 FPS:
1. Use OpenCV direct capture
2. Reduce to 320x240 resolution
3. Lower JPEG quality to 60-70%
4. Consider MJPEG streaming instead of individual frames

## Code Changes Needed

Switch from fswebcam subprocess to OpenCV:
```python
import cv2
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
ret, frame = cap.read()
```

This would allow 15-30 FPS instead of 5 FPS.


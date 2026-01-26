# Live Video Display Documentation

This document describes how live video frames are displayed on the HTML dashboard in the group project system.

## Overview

The system displays live video frames from Module 1 (Crowd Detection) on the HTML dashboard in real-time using WebSocket communication (SocketIO). Video frames are transmitted as base64-encoded JPEG images and displayed directly in the browser.

## Architecture

### Components

1. **Module 1 (Crowd Detection Client)**: Captures video frames and sends them to the server
2. **Flask Server (`server.py`)**: Receives video frames and broadcasts them to connected clients
3. **HTML Dashboard (`index.html`)**: Receives and displays video frames in real-time

## Data Flow

```
Module 1 Client → SocketIO Event → Flask Server → SocketIO Broadcast → HTML Dashboard
```

### Step-by-Step Process

1. **Module 1 sends video frame**:
   - Module 1 client captures a video frame from the camera
   - Encodes the frame as a base64 JPEG string
   - Sends it via SocketIO event: `CrowdVideoFrameEvent`

2. **Server receives and processes**:
   - Server handler `handle_crowd_video()` receives the event
   - Extracts video frame from nested data structure if needed
   - Auto-registers the module if not already registered
   - Broadcasts to all connected clients via `crowd_video_update` event

3. **Dashboard displays frame**:
   - JavaScript listens for `crowd_video_update` SocketIO event
   - Extracts `video_frame` from the data payload
   - Sets the image source using a data URI
   - Updates the DOM to show the video frame

## Server-Side Implementation

### Event Handler: `handle_crowd_video()`

**Location**: `server.py` (lines 834-932)

**Functionality**:
- Receives video frames via `CrowdVideoFrameEvent` SocketIO event
- Handles nested data structure (extracts `video_frame` from `data.video_frame` if present)
- Auto-registers module if not already registered
- Updates current crowd data state
- Broadcasts video frame to all clients

**Key Code**:
```python
@socketio.on('CrowdVideoFrameEvent')
def handle_crowd_video(data):
    """Receive video frames from Module 1"""
    module_id = data.get('module_id', 'unknown')
    
    # Extract video_frame from nested data structure
    video_frame_data = data.copy()
    if 'data' in data and isinstance(data['data'], dict):
        if 'video_frame' in data['data']:
            video_frame_data['video_frame'] = data['data']['video_frame']
    
    # Emit with video_frame at top level for frontend
    socketio.emit('crowd_video_update', video_frame_data)
```

**Data Structure**:
The server expects data in one of these formats:
- **Format 1** (preferred): `{'module_id': '...', 'video_frame': 'base64_string', 'data': {...}}`
- **Format 2** (nested): `{'module_id': '...', 'data': {'video_frame': 'base64_string', ...}}`

The server normalizes both formats to ensure `video_frame` is at the top level.

## Client-Side Implementation

### HTML Structure

**Location**: `templates/index.html` (line 754-756)

The video display container:
```html
<div id="m1-image-container" style="margin-bottom: 15px; display: none;">
  <img id="m1-image" src="" alt="Video Feed" 
       style="width: 100%; max-width: 640px; border-radius: 8px; 
              border: 1px solid var(--borderSubtle);">
</div>
```

**Initial State**:
- Container is hidden (`display: none`)
- Image element has empty `src` attribute
- Container becomes visible when first video frame is received

### JavaScript Event Handler

**Location**: `templates/index.html` (lines 1777-1825)

**SocketIO Listener**:
```javascript
socket.on("crowd_video_update", (data) => {
  console.log("Crowd video update event received:", data);
  
  // Update module status
  if(data.module_id) {
    state.health.m1.lastSeen = Date.now();
    setModuleStatus("m1-status", "active");
  }
  
  // Display video frame image if available
  if(data.video_frame) {
    const imageContainer = document.getElementById("m1-image-container");
    const imageElement = document.getElementById("m1-image");
    
    if(imageContainer && imageElement) {
      // Store video frame for AI analysis
      currentVideoFrameBase64 = data.video_frame;
      
      // Set image source from base64 data
      imageElement.src = "data:image/jpeg;base64," + data.video_frame;
      imageContainer.style.display = "block";
      
      // Enable analyze button
      const analyzeBtn = document.getElementById("ai-analyze-btn");
      if(analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.style.opacity = "1";
        analyzeBtn.style.cursor = "pointer";
      }
    }
  }
  
  // If video frame includes crowd data, render it
  if(data.data) {
    renderCrowd(data);
  }
});
```

### Key Features

1. **Base64 Data URI**: Video frames are displayed using data URIs:
   ```javascript
   imageElement.src = "data:image/jpeg;base64," + data.video_frame;
   ```

2. **Frame Storage**: Current video frame is stored in `currentVideoFrameBase64` for AI analysis:
   ```javascript
   currentVideoFrameBase64 = data.video_frame;
   ```

3. **Module Status Update**: Receiving video frames updates Module 1 status to "active"

4. **Crowd Data Integration**: If the video frame includes crowd detection data, it's automatically rendered

5. **AI Analysis Integration**: Video frames can be analyzed using the AI image analysis feature

## Data Format

### Video Frame Payload

**Event Name**: `crowd_video_update`

**Payload Structure**:
```javascript
{
  "module_id": "module_1_001",           // Module identifier
  "video_frame": "base64_encoded_jpeg",  // Base64-encoded JPEG image
  "data": {                              // Optional: Crowd detection data
    "people_count": 5,
    "crowd_level": "normal",
    "confidence": 0.92,
    // ... other crowd data fields
  },
  "timestamp": "2026-01-26T10:30:00"     // ISO timestamp
}
```

### Base64 Encoding

- **Format**: JPEG images encoded as base64 strings
- **No prefix**: The base64 string does NOT include the `data:image/jpeg;base64,` prefix
- **Client adds prefix**: The HTML dashboard adds the prefix when setting the image source

## Integration with Other Features

### 1. AI Image Analysis

Video frames displayed on the dashboard can be analyzed using the AI image analysis feature:

- The current video frame is stored in `currentVideoFrameBase64`
- Users can click the "Analyze Frame" button to send the frame to the AI service
- The AI analysis endpoint (`/api/analyze_image`) processes the frame and returns people count

### 2. Crowd Data Rendering

If the video frame payload includes crowd detection data in the `data` field, it's automatically rendered:

```javascript
if(data.data) {
  renderCrowd(data);
}
```

This allows Module 1 to send both video frames and crowd detection results in a single event.

### 3. Module Health Monitoring

Receiving video frames updates the Module 1 health status:

- Sets `state.health.m1.lastSeen` to current timestamp
- Updates module status badge to "active"
- Logs activity in the dashboard log

## Error Handling

### Server-Side

- **Missing video_frame**: Server logs warning but continues processing
- **Invalid data structure**: Server attempts to extract video_frame from nested structure
- **Module registration**: Auto-registers module if not already registered

### Client-Side

- **Missing elements**: Checks for `imageContainer` and `imageElement` before updating
- **Image load errors**: Browser handles image loading errors automatically
- **Console logging**: Errors are logged to browser console for debugging

## Performance Considerations

1. **Frame Rate**: Video frames are sent as individual JPEG images, not a continuous stream
2. **Image Size**: Large images may cause delays; consider resizing on Module 1 before sending
3. **Network Bandwidth**: Base64 encoding increases payload size by ~33% compared to binary
4. **Browser Rendering**: Browser efficiently handles data URI images

## Troubleshooting

### Video Not Displaying

1. **Check SocketIO connection**: Ensure dashboard is connected to server
2. **Check console logs**: Look for `crowd_video_update` events in browser console
3. **Verify data format**: Ensure `video_frame` field exists in payload
4. **Check base64 encoding**: Verify the base64 string is valid JPEG data

### Module Not Registering

- Server auto-registers modules when receiving video frames
- Check server logs for registration messages
- Verify `module_id` is present in the payload

### Image Not Loading

- Verify base64 string is complete (not truncated)
- Check browser console for image loading errors
- Ensure JPEG data is valid (can test by saving base64 to file)

## Example: Sending Video Frame from Module 1

```python
import socketio
import base64
import cv2

# Connect to server
sio = socketio.Client()
sio.connect('http://server-ip:5000')

# Capture frame from camera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

# Encode as JPEG
_, buffer = cv2.imencode('.jpg', frame)
frame_base64 = base64.b64encode(buffer).decode('utf-8')

# Send to server
sio.emit('CrowdVideoFrameEvent', {
    'module_id': 'module_1_001',
    'video_frame': frame_base64,
    'data': {
        'people_count': 5,
        'crowd_level': 'normal'
    },
    'timestamp': datetime.now().isoformat()
})
```

## Related Files

- **Server**: `Assignment/group_project/server.py` (lines 834-932)
- **Dashboard**: `Assignment/group_project/templates/index.html` (lines 754-756, 1777-1825)
- **AI Analysis**: `Assignment/group_project/server.py` (lines 505-728)
- **Crowd Rendering**: `Assignment/group_project/templates/index.html` (renderCrowd function)

## Future Enhancements

Potential improvements to the video display system:

1. **MJPEG Stream**: Replace individual frames with MJPEG stream for smoother playback
2. **WebRTC**: Implement WebRTC for lower latency video streaming
3. **Frame Rate Control**: Add client-side frame rate limiting
4. **Compression**: Implement better compression before base64 encoding
5. **Multiple Cameras**: Support multiple video feeds from different modules
6. **Recording**: Add ability to record video segments
7. **Overlays**: Add overlays showing detection boxes, people count, etc.

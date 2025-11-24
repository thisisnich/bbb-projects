## Webcam Streaming Specification (Draft)

### Purpose
- Enable USB webcam capture on BeagleBone Black Wireless (BBBW)
- Stream video feed online for remote viewing and testing
- Prepare foundation for future Google AI Studio Pro integration for image recognition/analysis

### Hardware Assumptions (Confirmed)
- Platform: BeagleBone Black Wireless (BBBW)
- USB webcam: **Logitech C615 HD webcam** (UVC compatible)
- Network: BBBW connected via WiFi or USB network (192.168.7.1 or WiFi IP)
- Existing Flask server running on port 5000

### Requirements (Confirmed)

1. **Webcam Type & Compatibility**
   - ✅ **Logitech C615 HD webcam** - UVC compatible, should work out of the box

2. **Streaming Method**
   - ✅ **MJPEG Stream** - Confirmed, works well for this use case

3. **Viewing Interface**
   - ✅ **Separate standalone page** - New page for webcam viewing (not integrated into existing Flask routes)

4. **Frame Rate & Resolution**
   - ✅ Frame rate: **15 fps (default), adjustable** - User will test to find reasonable settings
   - ✅ Resolution: **640x480 (default), adjustable** - User will test to find reasonable settings

5. **Network Access**
   - ✅ **Public internet access** - Stream should be accessible from outside local network (requires port forwarding/tunneling setup)

6. **Google AI Studio Pro Integration (Future - Phase 2)**
   - ✅ Analysis types needed:
     - Object detection
     - Scene analysis
     - Face recognition

### Success Criteria (Phase 1: Viewing & Testing)
- [ ] Logitech C615 HD webcam detected and accessible on BBBW
- [ ] Video stream accessible via web browser at `http://<bbbw-ip>:5000/webcam` (separate page)
- [ ] Stream displays in browser with reasonable latency (< 2 seconds)
- [ ] Stream runs stably without crashing (handles webcam disconnection gracefully)
- [ ] Frame rate is configurable via web interface (default: 15 fps)
- [ ] Resolution is configurable via web interface (default: 640x480)
- [ ] Works with existing Flask server (no conflicts)
- [ ] Public internet access possible (with port forwarding/tunneling)

### Success Criteria (Phase 2: Google AI Integration - Future)
- [ ] Capture frames from stream
- [ ] Send frames to Google AI Studio Pro API
- [ ] Display analysis results (object detection, scene analysis, face recognition)
- [ ] Configurable analysis interval
- [ ] Real-time or on-demand analysis modes

### Technical Considerations

**Libraries Needed:**
- `opencv-python` or `opencv-python-headless` (for webcam capture)
- `flask` (already in use)
- Possibly `Pillow` (for image processing)

**BBBW Constraints:**
- Limited CPU (ARM Cortex-A8, ~1GHz)
- Limited RAM (512MB)
- USB 2.0 bandwidth
- May need to optimize frame rate/resolution for performance

**Streaming Architecture:**
- Flask route serving MJPEG stream (`/webcam` or `/video_feed`)
- OpenCV captures frames in background thread
- Generator function yields JPEG frames
- Browser displays via `<img src="/video_feed">` or similar

### Out of Scope (Initial Implementation)
- Google AI Studio Pro integration (Phase 2)
- Recording/saving video to disk
- Multiple webcam support
- Advanced video processing (filters, effects)
- Audio streaming
- WebRTC or H.264 encoding (can add later if needed)
- Authentication/security (can add later)

### API Design (Proposed)

**Flask Routes:**
- `GET /webcam` - Standalone web page displaying webcam stream with controls
- `GET /video_feed` - MJPEG stream endpoint (used by `<img>` tag)
- `POST /webcam/config` - Update frame rate/resolution settings (optional, for Phase 1)

**Configuration:**
- Frame rate: 15 fps (default, adjustable via web interface)
- Resolution: 640x480 (default, adjustable via web interface)
- Webcam device index: 0 (default, for Logitech C615)

**Error Handling:**
- Handle webcam not found/disconnected
- Graceful degradation if OpenCV unavailable
- Clear error messages in browser

### Implementation Plan (Post-Approval)

**Phase 1: Basic Streaming**
1. Install OpenCV on BBBW
2. Create webcam capture module/class
3. Add Flask routes for webcam page and MJPEG stream
4. Create HTML template for viewing stream
5. Test with USB webcam
6. Add error handling and graceful shutdown

**Phase 2: Optimization & Polish**
1. Add configuration for frame rate/resolution
2. Optimize for BBBW CPU constraints
3. Add status indicators (fps, connection status)
4. Handle webcam reconnection

**Phase 3: Google AI Integration (Future)**
1. Research Google AI Studio Pro API
2. Add frame capture endpoint
3. Implement API integration
4. Display analysis results

### Implementation Status

✅ **Spec Approved** - All requirements confirmed:
- Logitech C615 HD webcam
- MJPEG streaming
- Separate standalone page
- Adjustable frame rate (15 fps default) and resolution (640x480 default)
- Public internet access
- Future: Google AI Studio Pro integration (object detection, scene analysis, face recognition)

**Ready for implementation!** Type 'GO!' when ready to proceed.


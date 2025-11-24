"""
Webcam Module for BBBW
Handles USB webcam capture using OpenCV
Supports Logitech C615 HD and other UVC-compatible webcams
"""
import cv2
import threading
import time
from typing import Optional, Tuple
import sys

class WebcamCapture:
    """
    Webcam capture class with configurable frame rate and resolution.
    Thread-safe for use with Flask streaming.
    """
    
    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480, fps: int = 15, lazy_hw: bool = False):
        """
        Initialize webcam capture.
        
        Args:
            device_index: Camera device index (usually 0 for first USB webcam)
            width: Frame width in pixels (default: 640)
            height: Frame height in pixels (default: 480)
            fps: Target frames per second (default: 15)
            lazy_hw: If True, don't open camera until first use
        """
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.lazy_hw = lazy_hw
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.lock = threading.Lock()
        self.is_open = False
        self.last_frame = None
        self.last_frame_time = 0
        self.frame_interval = 1.0 / fps if fps > 0 else 0.1
        
        if not lazy_hw:
            self.open()
    
    def open(self) -> bool:
        """Open the webcam device."""
        if self.is_open:
            return True
        
        try:
            with self.lock:
                self.cap = cv2.VideoCapture(self.device_index)
                
                if not self.cap.isOpened():
                    print(f"[WEBCAM] Failed to open camera device {self.device_index}")
                    return False
                
                # Set resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                
                # Set FPS (may not be supported by all cameras)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                
                # Try to set buffer size to reduce latency
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Verify actual resolution
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
                
                print(f"[WEBCAM] Opened camera {self.device_index}")
                print(f"[WEBCAM] Resolution: {actual_width}x{actual_height} (requested: {self.width}x{self.height})")
                print(f"[WEBCAM] FPS: {actual_fps:.1f} (requested: {self.fps})")
                
                self.is_open = True
                return True
                
        except Exception as e:
            print(f"[WEBCAM] Error opening camera: {e}")
            self.is_open = False
            return False
    
    def close(self):
        """Close the webcam device."""
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.is_open = False
            print("[WEBCAM] Camera closed")
    
    def read_frame(self) -> Optional[bytes]:
        """
        Read a frame from the webcam and return as JPEG bytes.
        Returns None if frame cannot be read.
        """
        if not self.is_open:
            if not self.open():
                return None
        
        try:
            with self.lock:
                if self.cap is None or not self.cap.isOpened():
                    return None
                
                # Throttle frame rate
                current_time = time.time()
                if current_time - self.last_frame_time < self.frame_interval:
                    # Return cached frame if too soon
                    if self.last_frame is not None:
                        return self.last_frame
                
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    # Try to reopen camera
                    print("[WEBCAM] Failed to read frame, attempting to reopen...")
                    self.cap.release()
                    time.sleep(0.1)
                    self.cap = cv2.VideoCapture(self.device_index)
                    if self.cap.isOpened():
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        ret, frame = self.cap.read()
                    
                    if not ret or frame is None:
                        return None
                
                # Encode frame as JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]  # 85% quality
                ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
                
                if ret:
                    self.last_frame = jpeg.tobytes()
                    self.last_frame_time = current_time
                    return self.last_frame
                else:
                    return None
                    
        except Exception as e:
            print(f"[WEBCAM] Error reading frame: {e}")
            return None
    
    def update_config(self, width: Optional[int] = None, height: Optional[int] = None, fps: Optional[int] = None) -> bool:
        """
        Update webcam configuration.
        Camera will be reopened with new settings.
        
        Args:
            width: New width (None to keep current)
            height: New height (None to keep current)
            fps: New FPS (None to keep current)
        
        Returns:
            True if successful, False otherwise
        """
        was_open = self.is_open
        
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if fps is not None:
            self.fps = fps
            self.frame_interval = 1.0 / fps if fps > 0 else 0.1
        
        if was_open:
            self.close()
            time.sleep(0.2)  # Brief pause before reopening
            return self.open()
        
        return True
    
    def get_status(self) -> dict:
        """Get current webcam status."""
        return {
            'is_open': self.is_open,
            'device_index': self.device_index,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'has_frame': self.last_frame is not None
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global webcam instance (will be initialized in WebServer)
webcam: Optional[WebcamCapture] = None



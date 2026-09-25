"""
AI-Vision Screen Capture Engine
Provides ultra-low-overhead, hardware-efficient screen capture on Windows
with pre-allocated memory buffers and real-time RAM/latency profiling.
"""

import os
import time
import threading

# Thread-local storage for mss instances
_THREAD_LOCAL = threading.local()
import psutil
import ctypes
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from PIL import Image

# Global persistent handles to prevent GC from closing desktop handles
_GLOBAL_HWINSTA = None
_GLOBAL_HDESK = None


def ensure_interactive_desktop():
    """Ensures process and thread are attached to the interactive Windows station (winsta0\\default) and DPI aware."""
    global _GLOBAL_HWINSTA, _GLOBAL_HDESK
    # 1. Enable per-monitor DPI awareness
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # 2. Attach thread to interactive window station
    try:
        import win32service
        import win32con
        if _GLOBAL_HWINSTA is None:
            _GLOBAL_HWINSTA = win32service.OpenWindowStation("winsta0", False, win32con.MAXIMUM_ALLOWED)
        _GLOBAL_HWINSTA.SetProcessWindowStation()
        
        if _GLOBAL_HDESK is None:
            _GLOBAL_HDESK = win32service.OpenDesktop("default", 0, False, win32con.MAXIMUM_ALLOWED)
        _GLOBAL_HDESK.SetThreadDesktop()
    except Exception:
        pass


# MUST ATTACH BEFORE IMPORTING MSS / GDI LIBRARIES
ensure_interactive_desktop()

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import win32gui
    import win32ui
    import win32con
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class ScreenCaptureEngine:
    def __init__(self, monitor_index: int = 1):
        """
        Initializes the screen capture engine with zero-overhead memory buffers.
        
        Args:
            monitor_index: Monitor number to capture (1-indexed for mss/win32).
        """
        ensure_interactive_desktop()
        self.monitor_index = monitor_index
        self.process = psutil.Process(os.getpid())
        self.mss_instance = None
        
        # Determine screen resolution
        self.width, self.height = self._get_screen_dimensions()
        
        # Pre-allocate contiguous NumPy buffer to eliminate RAM reallocation thrash
        # Shape: (height, width, 3) in uint8 RGB format
        self._buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Telemetry metrics
        self.last_capture_time_ms: float = 0.0
        self.frame_count: int = 0
        self.backend_name: str = "unknown"

        self._init_backend()

    def _get_screen_dimensions(self) -> Tuple[int, int]:
        """Detects the primary display dimensions."""
        if HAS_WIN32:
            w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            return w, h
        else:
            # Fallback to PIL
            from PIL import ImageGrab
            img = ImageGrab.grab()
            return img.size

    def _init_backend(self):
        """Initializes the fastest available capture backend."""
        if HAS_MSS:
            self.backend_name = "mss (DirectX/Win32 Ctypes Hook)"
        elif HAS_WIN32:
            self.backend_name = "pywin32 (Native GDI Device Context)"
        else:
            self.backend_name = "PIL.ImageGrab (Standard Fallback)"

    def get_memory_usage_mb(self) -> float:
        """Returns the current process RSS memory usage in Megabytes."""
        return self.process.memory_info().rss / (1024.0 * 1024.0)

    def capture_frame(self) -> np.ndarray:
        """
        Captures a single full desktop frame into the pre-allocated buffer.
        
        Returns:
            np.ndarray: Read-only view of the RGB frame array of shape (height, width, 3).
        """
        ensure_interactive_desktop()
        start = time.perf_counter()
        
        if HAS_MSS:
            # High-speed thread-local mss capture
            if not hasattr(_THREAD_LOCAL, "sct") or _THREAD_LOCAL.sct is None:
                _THREAD_LOCAL.sct = mss.MSS()
            sct = _THREAD_LOCAL.sct
            monitors = sct.monitors
            mon = monitors[self.monitor_index] if self.monitor_index < len(monitors) else monitors[0]
            sct_img = sct.grab(mon)
            # Fast in-place copy from BGRA to RGB into pre-allocated buffer
            raw = np.frombuffer(sct_img.raw, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 4))
            np.copyto(self._buffer, raw[:, :, :3][:, :, ::-1])  # BGRA -> RGB
            
        elif HAS_WIN32:
            # Native win32 capture
            hwnd = win32gui.GetDesktopWindow()
            w_dc = win32gui.GetWindowDC(hwnd)
            dc_obj = win32ui.CreateDCFromHandle(w_dc)
            c_dc = dc_obj.CreateCompatibleDC()
            
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(dc_obj, self.width, self.height)
            c_dc.SelectObject(bmp)
            
            # BitBlt copy
            c_dc.BitBlt((0, 0), (self.width, self.height), dc_obj, (0, 0), win32con.SRCCOPY)
            
            # Extract raw bytes
            bmpinfo = bmp.GetInfo()
            bmpstr = bmp.GetBitmapBits(True)
            raw = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))
            np.copyto(self._buffer, raw[:, :, :3][:, :, ::-1])
            
            # Cleanup Win32 GDI handles to prevent memory leaks
            dc_obj.DeleteDC()
            c_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, w_dc)
            win32gui.DeleteObject(bmp.GetHandle())
            
        else:
            # Standard PIL fallback
            from PIL import ImageGrab
            shot = ImageGrab.grab()
            np.copyto(self._buffer, np.array(shot))

        self.last_capture_time_ms = (time.perf_counter() - start) * 1000.0
        self.frame_count += 1
        return self._buffer

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns performance metrics."""
        return {
            "backend": self.backend_name,
            "resolution": f"{self.width}x{self.height}",
            "last_capture_time_ms": round(self.last_capture_time_ms, 2),
            "estimated_max_fps": round(1000.0 / max(self.last_capture_time_ms, 0.001), 1),
            "process_rss_mb": round(self.get_memory_usage_mb(), 2),
            "frame_count": self.frame_count
        }

    def close(self):
        """Releases underlying resources."""
        if self.mss_instance is not None:
            self.mss_instance.close()
            self.mss_instance = None

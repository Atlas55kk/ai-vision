"""
AI-Vision Window Filter & Application Whitelister
Allows the vision engine to track and isolate specific application windows
(e.g., Godot, Blender, ANSYS, CAD) so background private windows are never captured.
"""

import time
from typing import Optional, Tuple, Dict, Any, List
import numpy as np

try:
    import win32gui
    import win32process
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class WindowFilterEngine:
    def __init__(self, target_title_keyword: Optional[str] = None):
        """
        Initializes the Window Filter Engine.
        
        Args:
            target_title_keyword: Keyword to filter windows (e.g., "Godot", "Blender").
                                 If None, tracks the currently focused active window.
        """
        self.target_keyword = target_title_keyword

    def get_active_window_info(self) -> Dict[str, Any]:
        """Returns details about the currently focused foreground window."""
        if not HAS_WIN32:
            return {"hwnd": 0, "title": "Unknown", "rect": (0, 0, 1920, 1080)}

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return {"hwnd": 0, "title": "Desktop", "rect": (0, 0, 1920, 1080)}

        title = win32gui.GetWindowText(hwnd)
        rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)
        
        return {
            "hwnd": hwnd,
            "title": title,
            "rect": rect,  # (x1, y1, x2, y2)
            "width": max(0, rect[2] - rect[0]),
            "height": max(0, rect[3] - rect[1])
        }

    def find_window_by_keyword(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Finds the first visible window matching the keyword in its title."""
        if not HAS_WIN32:
            return None

        results = []

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if keyword.lower() in title.lower():
                    rect = win32gui.GetWindowRect(hwnd)
                    w = rect[2] - rect[0]
                    h = rect[3] - rect[1]
                    if w > 100 and h > 100:  # Must have meaningful size
                        results.append({
                            "hwnd": hwnd,
                            "title": title,
                            "rect": rect,
                            "width": w,
                            "height": h
                        })

        win32gui.EnumWindows(enum_windows_callback, None)
        return results[0] if results else None

    def isolate_window_on_frame(
        self,
        frame_rgb: np.ndarray,
        target_rect: Optional[Tuple[int, int, int, int]] = None
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Blacks out everything on the screen EXCEPT the target window bounding box.
        
        Args:
            frame_rgb: Full resolution RGB desktop frame.
            target_rect: Optional (left, top, right, bottom). If None, uses active window.
            
        Returns:
            Tuple[np.ndarray, Tuple[int, int, int, int]]:
                (isolated_frame_rgb, actual_rect_used)
        """
        frame_h, frame_w, _ = frame_rgb.shape

        if target_rect is None:
            if self.target_keyword:
                win = self.find_window_by_keyword(self.target_keyword)
                if win:
                    target_rect = win["rect"]
            if target_rect is None:
                target_rect = self.get_active_window_info()["rect"]

        x1, y1, x2, y2 = target_rect

        # Clamp to frame dimensions
        x1 = max(0, min(frame_w, x1))
        y1 = max(0, min(frame_h, y1))
        x2 = max(0, min(frame_w, x2))
        y2 = max(0, min(frame_h, y2))

        # Create isolated mask: black out outside regions
        # Top band
        if y1 > 0:
            frame_rgb[0:y1, :, :] = 0
        # Bottom band
        if y2 < frame_h:
            frame_rgb[y2:frame_h, :, :] = 0
        # Left band
        if x1 > 0:
            frame_rgb[y1:y2, 0:x1, :] = 0
        # Right band
        if x2 < frame_w:
            frame_rgb[y1:y2, x2:frame_w, :] = 0

        return frame_rgb, (x1, y1, x2, y2)

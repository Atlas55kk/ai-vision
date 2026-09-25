"""
AI-Vision OS Input Actuator
Provides safe, normalized coordinate mouse and keyboard control with
boundary clamping and safety deadman checks.
"""

import time
import win32api
import win32con
from typing import Tuple, Optional
from src.capture.engine import ensure_interactive_desktop


class OSActuator:
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        safe_mode: bool = True,
        action_delay_s: float = 0.05,
        bottom_safety_margin_px: int = 50,
        dry_run: bool = False
    ):
        """
        Initializes the OS Actuator.
        
        Args:
            screen_width: Screen width in pixels.
            screen_height: Screen height in pixels.
            safe_mode: Prevents clicking inside dangerous zones (like taskbars).
            action_delay_s: Delay in seconds after an action to ensure stability.
            bottom_safety_margin_px: Height of bottom screen zone forbidden for AI clicks.
            dry_run: If True, simulates actions without modifying physical OS cursor.
        """
        self.width = screen_width
        self.height = screen_height
        self.safe_mode = safe_mode
        self.action_delay_s = action_delay_s
        self.bottom_safety_margin = bottom_safety_margin_px
        self.dry_run = dry_run

    def normalized_to_screen_coords(self, norm_x: int, norm_y: int) -> Tuple[int, int]:
        """Maps normalized [0, 1000] coordinates to screen pixels."""
        px = int((norm_x / 1000.0) * self.width)
        py = int((norm_y / 1000.0) * self.height)
        
        # Clamp to screen bounds
        px = max(0, min(self.width - 1, px))
        py = max(0, min(self.height - 1, py))
        
        # Apply safety zone check
        if self.safe_mode:
            max_safe_y = self.height - self.bottom_safety_margin
            if py >= max_safe_y:
                py = max_safe_y - 1
                
        return px, py

    def move_mouse(self, norm_x: int, norm_y: int):
        """Moves mouse cursor to normalized coordinate."""
        if self.dry_run:
            return
        ensure_interactive_desktop()
        px, py = self.normalized_to_screen_coords(norm_x, norm_y)
        try:
            win32api.SetCursorPos((px, py))
        except Exception:
            pass
        time.sleep(self.action_delay_s)

    def click(self, norm_x: int, norm_y: int, button: str = "left"):
        """Performs a click at the normalized coordinate."""
        if self.dry_run:
            return
        ensure_interactive_desktop()
        px, py = self.normalized_to_screen_coords(norm_x, norm_y)
        try:
            win32api.SetCursorPos((px, py))
            time.sleep(0.02)
            if button == "left":
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, px, py, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, px, py, 0, 0)
            elif button == "right":
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, px, py, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, px, py, 0, 0)
        except Exception:
            pass
        time.sleep(self.action_delay_s)

    def double_click(self, norm_x: int, norm_y: int):
        """Performs a double click."""
        self.click(norm_x, norm_y, button="left")
        time.sleep(0.05)
        self.click(norm_x, norm_y, button="left")

    def type_text(self, text: str):
        """Types string characters safely."""
        if self.dry_run:
            return
        ensure_interactive_desktop()
        try:
            for char in text:
                vk = win32api.VkKeyScan(char)
                win32api.keybd_event(vk, 0, 0, 0)
                time.sleep(0.01)
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.01)
        except Exception:
            pass
        time.sleep(self.action_delay_s)

    def press_key_combination(self, *vk_codes: int):
        """Presses a combination of keys (e.g. Ctrl+S) and releases them."""
        if self.dry_run:
            return
        ensure_interactive_desktop()
        try:
            for vk in vk_codes:
                win32api.keybd_event(vk, 0, 0, 0)
            time.sleep(0.05)
            for vk in reversed(vk_codes):
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception:
            pass
        time.sleep(self.action_delay_s)

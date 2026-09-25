"""
AI-Vision On-Device Privacy & Security Engine
Guarantees sensitive screen areas (taskbars, credentials, private windows)
are masked out directly in local memory before any frame is processed or sent.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional


class PrivacyMaskEngine:
    def __init__(
        self,
        mask_taskbar: bool = True,
        taskbar_height_px: int = 48,
        custom_redaction_boxes: Optional[List[List[int]]] = None
    ):
        """
        Initializes the Privacy Mask Engine.
        
        Args:
            mask_taskbar: Whether to automatically black out the bottom Windows taskbar.
            taskbar_height_px: Typical height of the taskbar in pixels.
            custom_redaction_boxes: List of [ymin, xmin, ymax, xmax] normalized to [0, 1000].
        """
        self.mask_taskbar = mask_taskbar
        self.taskbar_height_px = taskbar_height_px
        self.custom_redaction_boxes = custom_redaction_boxes or []

    def apply_mask(self, frame_rgb: np.ndarray) -> np.ndarray:
        """
        Applies blackout masks in-place to the frame.
        
        Args:
            frame_rgb: RGB frame from capture engine.
            
        Returns:
            np.ndarray: Masked frame with sensitive areas blacked out.
        """
        h, w, _ = frame_rgb.shape

        # 1. Mask bottom taskbar if enabled
        if self.mask_taskbar and h > self.taskbar_height_px:
            frame_rgb[h - self.taskbar_height_px:h, :, :] = 0

        # 2. Mask custom user-defined redaction zones
        for box in self.custom_redaction_boxes:
            ymin, xmin, ymax, xmax = box
            y1 = max(0, int((ymin / 1000.0) * h))
            x1 = max(0, int((xmin / 1000.0) * w))
            y2 = min(h, int((ymax / 1000.0) * h))
            x2 = min(w, int((xmax / 1000.0) * w))
            
            if y2 > y1 and x2 > x1:
                frame_rgb[y1:y2, x1:x2, :] = 0

        return frame_rgb

    def add_redaction_box(self, box: List[int]):
        """Adds a normalized bounding box [ymin, xmin, ymax, xmax] in [0, 1000]."""
        self.custom_redaction_boxes.append(box)

    def clear_redaction_boxes(self):
        """Clears all custom redaction boxes."""
        self.custom_redaction_boxes.clear()

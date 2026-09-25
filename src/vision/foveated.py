"""
AI-Vision Foveated Vision & Delta Engine
Implements bio-inspired foveated attention, macro-thumbnail downsampling,
on-demand high-resolution micro cropping, and perceptual delta filtering.
"""

import io
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from PIL import Image


class FoveatedVisionEngine:
    def __init__(
        self,
        macro_size: Tuple[int, int] = (640, 360),
        delta_threshold: float = 0.015,
        delta_grid_size: Tuple[int, int] = (64, 64)
    ):
        """
        Initializes the Foveated Vision Engine.
        
        Args:
            macro_size: (width, height) for the low-resolution global macro view.
            delta_threshold: Sensitivity threshold for triggering on screen changes (0.0 to 1.0).
            delta_grid_size: Downsampled dimension (w, h) for zero-latency perceptual delta calculation.
        """
        self.macro_width, self.macro_height = macro_size
        self.delta_threshold = delta_threshold
        self.delta_grid_w, self.delta_grid_h = delta_grid_size
        
        # Previous downsampled luminance state for delta check
        self._prev_luminance: Optional[np.ndarray] = None
        
        # Pre-allocated macro buffer to avoid memory allocations
        self._macro_buffer = np.zeros((self.macro_height, self.macro_width, 3), dtype=np.uint8)

    def compute_delta(self, frame_rgb: np.ndarray) -> Tuple[bool, float]:
        """
        Computes the perceptual difference between current frame and previous keyframe
        using Algorithm 1 (Luminance downsampled perceptual delta check).
        
        Args:
            frame_rgb: RGB frame from the capture engine.
            
        Returns:
            Tuple[bool, float]: (has_changed, delta_score)
        """
        # Fast downsample and grayscale conversion
        # cv2.resize with INTER_AREA is optimal for decimation
        small = cv2.resize(frame_rgb, (self.delta_grid_w, self.delta_grid_h), interpolation=cv2.INTER_AREA)
        # Compute luminance using ITU-R BT.601 weights: 0.299 R + 0.587 G + 0.114 B
        luminance = (0.299 * small[:, :, 0] + 0.587 * small[:, :, 1] + 0.114 * small[:, :, 2]) / 255.0

        if self._prev_luminance is None:
            self._prev_luminance = luminance
            return True, 1.0  # First frame is always considered changed

        # Mean absolute difference over the 64x64 grid
        diff = np.mean(np.abs(luminance - self._prev_luminance))
        has_changed = bool(diff >= self.delta_threshold)

        if has_changed:
            self._prev_luminance = luminance

        return has_changed, float(diff)

    def get_macro_view(self, frame_rgb: np.ndarray) -> np.ndarray:
        """
        Generates the low-resolution global context thumbnail (Macro View).
        
        Args:
            frame_rgb: Full resolution RGB frame.
            
        Returns:
            np.ndarray: Resized RGB image of shape (macro_height, macro_width, 3).
        """
        cv2.resize(
            frame_rgb,
            (self.macro_width, self.macro_height),
            dst=self._macro_buffer,
            interpolation=cv2.INTER_AREA
        )
        return self._macro_buffer

    def get_foveated_crop(
        self,
        frame_rgb: np.ndarray,
        box: List[int],
        padding_pct: float = 0.05
    ) -> np.ndarray:
        """
        Extracts a crystal-clear, 1:1 pixel native resolution micro-crop based on
        normalized coordinates [ymin, xmin, ymax, xmax] in range [0, 1000].
        
        Args:
            frame_rgb: Full resolution native RGB frame.
            box: [ymin, xmin, ymax, xmax] normalized to [0, 1000].
            padding_pct: Extra padding margin around the bounding box (default 5%).
            
        Returns:
            np.ndarray: Uncompressed native-resolution crop of the region of interest.
        """
        h, w, _ = frame_rgb.shape
        ymin, xmin, ymax, xmax = box

        # Denormalize to pixel coordinates
        y1 = int((ymin / 1000.0) * h)
        x1 = int((xmin / 1000.0) * w)
        y2 = int((ymax / 1000.0) * h)
        x2 = int((xmax / 1000.0) * w)

        # Apply padding if requested
        if padding_pct > 0:
            pad_h = int((y2 - y1) * padding_pct)
            pad_w = int((x2 - x1) * padding_pct)
            y1 = max(0, y1 - pad_h)
            x1 = max(0, x1 - pad_w)
            y2 = min(h, y2 + pad_h)
            x2 = min(w, x2 + pad_w)

        # Ensure valid non-empty slice
        y1 = min(max(0, y1), h - 1)
        y2 = max(y1 + 1, min(h, y2))
        x1 = min(max(0, x1), w - 1)
        x2 = max(x1 + 1, min(w, x2))

        # Return 1:1 pixel crop directly (zero downsampling)
        return frame_rgb[y1:y2, x1:x2, :]

    @staticmethod
    def encode_to_jpeg_bytes(image_rgb: np.ndarray, quality: int = 85) -> bytes:
        """Encodes an RGB NumPy frame into JPEG bytes for API transmission."""
        img_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode('.jpg', img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not success:
            raise ValueError("Failed to encode image to JPEG")
        return buffer.tobytes()

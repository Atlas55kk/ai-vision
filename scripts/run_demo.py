"""
AI-Vision Interactive Demonstration Script
Captures the live desktop screen, applies the privacy mask, generates a macro thumbnail,
extracts a foveated micro-crop, and saves the artifacts for visual inspection.
"""

import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.capture.engine import ScreenCaptureEngine
from src.vision.foveated import FoveatedVisionEngine
from src.security.mask import PrivacyMaskEngine
from PIL import Image


def main():
    print("=" * 60)
    print("           AI-VISION LIVE DEMONSTRATION")
    print("=" * 60)
    
    # 1. Output folder
    dump_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "debug_dumps"))
    os.makedirs(dump_dir, exist_ok=True)
    
    # 2. Initialize engines
    print("[*] Initializing capture, foveated vision, and privacy engines...")
    capture = ScreenCaptureEngine()
    vision = FoveatedVisionEngine(macro_size=(640, 360), delta_threshold=0.015)
    security = PrivacyMaskEngine(mask_taskbar=True)
    
    print(f"[*] Display Resolution: {capture.width}x{capture.height}")
    print(f"[*] Backend: {capture.backend_name}")
    print(f"[*] Baseline RAM: {capture.get_memory_usage_mb():.2f} MB")
    print("-" * 60)
    
    # 3. Capture Live Frame
    print("[*] Capturing live desktop screen...")
    t0 = time.perf_counter()
    frame = capture.capture_frame()
    t_cap = (time.perf_counter() - t0) * 1000.0
    print(f"[+] Frame captured in {t_cap:.2f} ms")
    
    # 4. Apply Privacy Mask
    security.apply_mask(frame)
    print("[+] Applied on-device privacy blackout to Windows taskbar.")
    
    # 5. Generate Macro View (Global Context)
    macro = vision.get_macro_view(frame)
    macro_path = os.path.join(dump_dir, "macro_view_640x360.jpg")
    Image.fromarray(macro).save(macro_path, quality=85)
    macro_kb = os.path.getsize(macro_path) / 1024.0
    print(f"[+] Macro View saved to: {macro_path}")
    print(f"    Dimensions: 640x360 | Size: {macro_kb:.1f} KB (~64 visual tokens)")
    
    # 6. Extract Foveated Micro-Crop (Focus on Center Screen [300, 300, 700, 700])
    crop = vision.get_foveated_crop(frame, box=[300, 300, 700, 700])
    crop_path = os.path.join(dump_dir, "foveated_micro_crop.jpg")
    Image.fromarray(crop).save(crop_path, quality=95)
    crop_kb = os.path.getsize(crop_path) / 1024.0
    print(f"[+] Foveated Micro-Crop saved to: {crop_path}")
    print(f"    Dimensions: {crop.shape[1]}x{crop.shape[0]} (Native 1:1 Pixels) | Size: {crop_kb:.1f} KB (~80 tokens)")
    
    # 7. Final Telemetry
    print("-" * 60)
    telemetry = capture.get_telemetry()
    print("[*] Final Engine Telemetry:")
    for k, v in telemetry.items():
        print(f"    - {k}: {v}")
    print("=" * 60)
    print("Demonstration completed successfully!")
    capture.close()


if __name__ == "__main__":
    main()

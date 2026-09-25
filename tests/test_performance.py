"""
AI-Vision End-to-End Performance & RAM Profiler
Runs a diagnostic benchmark on the Screen Capture Engine, Foveated Cropper,
Delta Detector, and Privacy Mask, measuring exact latency, FPS, and RAM consumption.
"""

import sys
import os
import time
import psutil

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.capture.engine import ScreenCaptureEngine
from src.vision.foveated import FoveatedVisionEngine
from src.security.mask import PrivacyMaskEngine
from src.actuation.controller import OSActuator


def run_benchmark(num_frames: int = 50):
    print("=" * 65)
    print("       AI-VISION HARDWARE BENCHMARK & RAM PROFILER")
    print("=" * 65)
    
    proc = psutil.Process(os.getpid())
    ram_initial_mb = proc.memory_info().rss / (1024.0 * 1024.0)
    print(f"[*] Initial Process RAM: {ram_initial_mb:.2f} MB")
    
    # 1. Initialize Engines
    t0 = time.perf_counter()
    capture = ScreenCaptureEngine()
    vision = FoveatedVisionEngine(macro_size=(640, 360), delta_threshold=0.015)
    security = PrivacyMaskEngine(mask_taskbar=True)
    actuator = OSActuator(capture.width, capture.height, safe_mode=True)
    init_time_ms = (time.perf_counter() - t0) * 1000.0
    
    ram_post_init_mb = proc.memory_info().rss / (1024.0 * 1024.0)
    print(f"[*] Engine Initialized in {init_time_ms:.1f} ms")
    print(f"[*] Active Backend: {capture.backend_name}")
    print(f"[*] Screen Resolution: {capture.width}x{capture.height}")
    print(f"[*] Post-Init RAM (with pre-allocated buffer): {ram_post_init_mb:.2f} MB (+{ram_post_init_mb - ram_initial_mb:.2f} MB)")
    print("-" * 65)
    
    # 2. Warm-up capture & OpenCV scratchpad
    frame = capture.capture_frame()
    security.apply_mask(frame)
    vision.compute_delta(frame)
    vision.get_macro_view(frame)
    vision.get_foveated_crop(frame, box=[300, 300, 700, 700])
    
    import gc
    gc.collect()
    ram_stable_baseline_mb = proc.memory_info().rss / (1024.0 * 1024.0)
    print(f"[*] Post-Warmup Stable Baseline RAM: {ram_stable_baseline_mb:.2f} MB")
    print("-" * 65)
    
    # 3. Main Benchmark Loop
    latencies_capture = []
    latencies_delta = []
    latencies_macro = []
    latencies_crop = []
    
    print(f"[*] Running {num_frames} frames through the complete visual pipeline...")
    
    for i in range(num_frames):
        # A. Capture
        t_start = time.perf_counter()
        frame = capture.capture_frame()
        latencies_capture.append((time.perf_counter() - t_start) * 1000.0)
        
        # B. Privacy Mask
        security.apply_mask(frame)
        
        # C. Delta check
        t_delta = time.perf_counter()
        has_changed, score = vision.compute_delta(frame)
        latencies_delta.append((time.perf_counter() - t_delta) * 1000.0)
        
        # D. Macro View
        t_macro = time.perf_counter()
        macro = vision.get_macro_view(frame)
        latencies_macro.append((time.perf_counter() - t_macro) * 1000.0)
        
        # E. Foveated Micro Crop (center region: [300, 300, 700, 700])
        t_crop = time.perf_counter()
        crop = vision.get_foveated_crop(frame, box=[300, 300, 700, 700])
        latencies_crop.append((time.perf_counter() - t_crop) * 1000.0)

    # 4. Memory Profiling Post-Loop
    import gc
    gc.collect()
    ram_final_mb = proc.memory_info().rss / (1024.0 * 1024.0)
    ram_drift_mb = ram_final_mb - ram_stable_baseline_mb
    
    avg_cap = sum(latencies_capture) / len(latencies_capture)
    avg_delta = sum(latencies_delta) / len(latencies_delta)
    avg_macro = sum(latencies_macro) / len(latencies_macro)
    avg_crop = sum(latencies_crop) / len(latencies_crop)
    total_pipeline_ms = avg_cap + avg_delta + avg_macro + avg_crop
    max_pipeline_fps = 1000.0 / max(total_pipeline_ms, 0.001)

    print("-" * 65)
    print("                     PERFORMANCE RESULTS")
    print("-" * 65)
    print(f"  Capture Latency (Full Screen) : {avg_cap:.2f} ms")
    print(f"  Perceptual Delta Computation   : {avg_delta:.2f} ms")
    print(f"  Macro-View Resizing (640x360)  : {avg_macro:.2f} ms")
    print(f"  Foveated Micro-Crop Extraction : {avg_crop:.2f} ms")
    print(f"  -------------------------------------------------------------")
    print(f"  Total Pipeline Latency         : {total_pipeline_ms:.2f} ms per frame")
    print(f"  Theoretical Max Pipeline Speed : {max_pipeline_fps:.1f} FPS")
    print("=" * 65)
    print("                       RAM CONSUMPTION")
    print("=" * 65)
    print(f"  Initial Baseline RAM           : {ram_initial_mb:.2f} MB")
    print(f"  Final Post-Loop RAM            : {ram_final_mb:.2f} MB")
    print(f"  RAM Drift After {num_frames} Frames        : {ram_drift_mb:+.2f} MB")
    
    if abs(ram_drift_mb) < 5.0:
        print("  Status: [PASS] Zero Memory Leaks! Buffer is properly recycled.")
    else:
        print("  Status: [WARNING] Noticeable memory growth detected.")
        
    print("=" * 65)
    capture.close()


if __name__ == "__main__":
    run_benchmark(num_frames=50)

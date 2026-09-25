# Deep Research: Low-Overhead Screen Capture & Hardware Benchmarks on Windows

**Document ID:** RES-02  
**Focus:** Zero-Copy GPU Desktop Duplication, Latency Optimization, and Dirty Rectangle Tracking

---

## 1. Problem Statement

To run AI screen perception on resource-constrained hardware (e.g., 8 GB – 16 GB RAM, integrated GPU, multi-tasking alongside Godot, CAD, or ANSYS), the screen capture mechanism **must not** compete for system RAM or CPU clock cycles.

Standard screen-grab tools (e.g. `PIL.ImageGrab`, GDI `BitBlt`, or software video recorders):
1. Allocate large system-RAM pixel buffers on every frame.
2. Involve synchronous CPU-side pixel format conversions (BGRA $\to$ RGB).
3. Spike CPU usage to 15%–40% and cause stutters in 3D game engines.

---

## 2. Comparative Analysis of Windows Capture Technologies

| Capture Technology | API Layer | Capture Latency (1080p) | CPU Utilization | RAM Allocation | Native Dirty Rects? | Supports Window Crop? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GDI (`BitBlt`)** | Legacy Win32 User32/GDI | 25 – 45 ms | 15% – 25% | High (RAM buffer copies) | No | Yes |
| **MSS (Python)** | GDI / Direct3D Wrapper | 15 – 25 ms | 8% – 15% | Medium (~60 MB) | No | Yes |
| **DXGI Desktop Duplication** | DirectX 11 / DXGI 1.2 | **1 – 3 ms** | **< 1%** | **Near-zero (VRAM surface)**| **Yes (`DirtyRects`)** | Display output only |
| **Windows.Graphics.Capture (WGC)** | WinRT / Direct3D 11 | **2 – 4 ms** | **< 2%** | **Low (GPU Shared Texture)** | Event-driven frame arrival | **Yes (Direct `HWND` target)** |

---

## 3. The Power of DXGI Metadata: Dirty Rectangles (`DXGI_OUTDUPL_FRAME_INFO`)

When calling `IDXGIOutputDuplication::AcquireNextFrame`, the Windows graphics driver returns a populated struct:

```cpp
typedef struct DXGI_OUTDUPL_FRAME_INFO {
    LARGE_INTEGER LastPresentTime;
    LARGE_INTEGER LastMouseUpdateTime;
    UINT AccumulatedFrames;
    BOOL RectsCoalesced;
    BOOL ProtectedContentMaskedOut;
    DXGI_OUTDUPL_POINTER_POSITION PointerPosition;
    UINT TotalMetadataBufferSize;
    // Followed by:
    // 1. RECT[] DirtyRects (coordinates of pixels that actually changed)
    // 2. DXGI_OUTDUPL_MOVE_RECT[] MoveRects (coordinates of pixels that shifted)
} DXGI_OUTDUPL_FRAME_INFO;
```

### Why This is a Game-Changer:
1. **Zero CPU Pixel Diffing:** The graphics card driver already knows exactly which bounding boxes changed during the frame buffer swap.
2. **Instant Delta Detection:** If `TotalMetadataBufferSize == 0` and `AccumulatedFrames == 0`, **nothing moved on screen**. The capture engine can sleep immediately without touching a single byte in RAM.
3. **Sub-region Extraction:** Instead of copying the entire $1920 \times 1080$ frame, we can read only the sub-rectangle described by `DirtyRects`, reducing memory bus transfer by up to 98%.

---

## 4. Hardware Failure Modes & Mitigation Strategies

1. **Dual-GPU Laptops (Integrated Intel/AMD + Discrete NVIDIA):**
   * *Problem:* If DXGI duplicates the display connected to the iGPU, but the Python process runs on the discrete GPU, DXGI returns `DXGI_ERROR_UNSUPPORTED`.
   * *Mitigation:* Explicitly bind Direct3D device creation to Adapter 0 (the primary display adapter), or use `Windows.Graphics.Capture` as a seamless fallback.
2. **Frame Release Starvation:**
   * *Problem:* Holding the acquired DXGI surface lock causes Windows DWM to drop frames or replicate stale surfaces.
   * *Mitigation:* Always call `ReleaseFrame()` immediately after copying the required sub-region to an offscreen staging texture.
3. **Fast Fallback Pipeline:**
   * Primary: Hardware Direct3D 11 DXGI / WGC.
   * Secondary (Universal fallback): High-performance C-optimized `mss` with downsampled perceptual difference checks.

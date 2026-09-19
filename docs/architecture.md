# Architecture Specification: AI-Vision

## 1. System Overview

AI-Vision acts as a lightweight daemon sitting between the host operating system and any AI reasoning backend.

```
┌────────────────────────────────────────────────────────┐
│                      Host OS                           │
│       (Godot, CAD, ANSYS, Blender, IDEs, etc.)         │
└───────────────▲────────────────────────┬───────────────┘
                │                        │
       Actuation (OS Inputs)    Screen Frames / Events
                │                        │
┌───────────────┴────────────────────────▼───────────────┐
│                   AI-Vision Engine                     │
│                                                        │
│  [src/capture]   Low-overhead Screen Capture           │
│  [src/security]  Privacy Masking & Coordinate Filter   │
│  [src/vision]    Delta Detection & Foveated Cropper    │
│  [src/actuation] Native OS Input Actuator              │
│  [src/protocol]  MCP / WebSocket Server                │
└──────────────────────────┬─────────────────────────────┘
                           │
             Standard JSON / Image Payloads
                           │
┌──────────────────────────▼─────────────────────────────┐
│                       AI Brain                         │
│       (Gemini, GPT-6, Claude, Local Qwen/LLaVA)        │
└────────────────────────────────────────────────────────┘
```

## 2. Component Responsibilities

1. **`src/capture/`**:
   - Primary interface with the OS display.
   - Low-latency, low-RAM capture using DirectX/DXGI or lightweight multi-platform hooks.

2. **`src/security/`**:
   - Ensures zero leakage of private data.
   - Applies black-box filters over sensitive coordinates (e.g. taskbars, credential windows).

3. **`src/vision/`**:
   - Computes perceptual differences between frames to detect changes.
   - Implements **Foveated Cropping**: provides high-detail patches for specific bounding boxes when requested by the AI.

4. **`src/actuation/`**:
   - Simulates human input (clicks, drags, keyboard shortcuts) safely with boundary checks and emergency kill-switches.

5. **`src/protocol/`**:
   - Exposes a unified API (e.g. Model Context Protocol or WebSocket) so any local or remote agent can observe and act.

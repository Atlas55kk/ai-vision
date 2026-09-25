"""
AI-Vision Standard Protocol Server
Provides a high-performance REST & WebSocket API so any local or remote AI agent
can observe the screen through adaptive foveated vision and execute safe actions.
"""

import base64
import os
import sys
import psutil
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.capture.engine import ScreenCaptureEngine
from src.vision.foveated import FoveatedVisionEngine
from src.security.mask import PrivacyMaskEngine
from src.security.window_filter import WindowFilterEngine
from src.actuation.controller import OSActuator

app = FastAPI(
    title="AI-Vision Perception & Actuation Protocol Server",
    description="Universal adaptive visual perception and control interface for AI agents",
    version="1.0.0"
)

# Global engine instances
capture_engine: Optional[ScreenCaptureEngine] = None
vision_engine: Optional[FoveatedVisionEngine] = None
mask_engine: Optional[PrivacyMaskEngine] = None
window_filter: Optional[WindowFilterEngine] = None
actuator: Optional[OSActuator] = None


class CropRequest(BaseModel):
    box: List[int] = Field(..., description="[ymin, xmin, ymax, xmax] normalized to [0, 1000]")
    quality: int = Field(85, ge=10, le=100, description="JPEG compression quality")


class ActionRequest(BaseModel):
    action: str = Field(..., description="'click', 'double_click', 'type', or 'key_combo'")
    norm_x: Optional[int] = Field(None, ge=0, le=1000, description="Normalized X coordinate [0, 1000]")
    norm_y: Optional[int] = Field(None, ge=0, le=1000, description="Normalized Y coordinate [0, 1000]")
    button: Optional[str] = Field("left", description="'left' or 'right'")
    text: Optional[str] = Field(None, description="Text to type")
    key_codes: Optional[List[int]] = Field(None, description="List of Win32 virtual key codes")


class FilterConfigRequest(BaseModel):
    target_keyword: Optional[str] = Field(None, description="Application keyword to whitelist (e.g., 'Godot')")
    mask_taskbar: bool = Field(True, description="Whether to mask the Windows taskbar")


def get_engines():
    global capture_engine, vision_engine, mask_engine, window_filter, actuator
    if capture_engine is None:
        capture_engine = ScreenCaptureEngine()
        vision_engine = FoveatedVisionEngine(macro_size=(640, 360), delta_threshold=0.015)
        mask_engine = PrivacyMaskEngine(mask_taskbar=True)
        window_filter = WindowFilterEngine()
        actuator = OSActuator(capture_engine.width, capture_engine.height, safe_mode=True)
    return capture_engine, vision_engine, mask_engine, window_filter, actuator


@app.on_event("startup")
def startup_event():
    get_engines()


@app.get("/health")
def health_check():
    cap, _, _, _, _ = get_engines()
    return {
        "status": "healthy",
        "service": "AI-Vision Protocol Server",
        "telemetry": cap.get_telemetry()
    }


@app.get("/state")
def get_screen_state(force_full: bool = False):
    """
    Captures the current desktop state, applies privacy masks, computes delta,
    and returns a low-token macro view (base64 JPEG) plus metadata.
    """
    cap, vis, mask, win_filter, _ = get_engines()
    
    # 1. Capture Frame
    frame = cap.capture_frame()
    active_win = win_filter.get_active_window_info()
    
    # 2. Apply window filter if enabled
    if win_filter.target_keyword:
        frame, _ = win_filter.isolate_window_on_frame(frame)
        
    # 3. Apply privacy taskbar mask
    mask.apply_mask(frame)
    
    # 4. Compute perceptual delta
    has_changed, delta_score = vis.compute_delta(frame)
    
    # 5. Generate Macro View
    macro = vis.get_macro_view(frame)
    jpeg_bytes = vis.encode_to_jpeg_bytes(macro, quality=80)
    b64_img = base64.b64encode(jpeg_bytes).decode('utf-8')
    
    return {
        "has_changed": has_changed,
        "delta_score": round(delta_score, 4),
        "resolution": f"{cap.width}x{cap.height}",
        "active_window": active_win["title"],
        "macro_image_b64": b64_img,
        "macro_tokens_approx": 64,
        "telemetry": cap.get_telemetry()
    }


@app.post("/crop")
def get_foveated_crop(req: CropRequest):
    """
    Extracts an on-demand, 1:1 pixel native resolution micro crop
    based on normalized coordinates [ymin, xmin, ymax, xmax].
    """
    cap, vis, _, _, _ = get_engines()
    frame = cap.capture_frame()
    
    if len(req.box) != 4:
        raise HTTPException(status_code=400, detail="Bounding box must contain exactly 4 coordinates [ymin, xmin, ymax, xmax]")
        
    crop = vis.get_foveated_crop(frame, box=req.box)
    jpeg_bytes = vis.encode_to_jpeg_bytes(crop, quality=req.quality)
    b64_crop = base64.b64encode(jpeg_bytes).decode('utf-8')
    
    return {
        "box": req.box,
        "crop_dimensions": [crop.shape[1], crop.shape[0]],  # [w, h]
        "crop_image_b64": b64_crop,
        "tokens_approx": 80
    }


@app.post("/act")
def execute_action(req: ActionRequest):
    """
    Executes a safe OS-level mouse or keyboard actuation.
    """
    _, _, _, _, act = get_engines()
    
    if req.action == "click":
        if req.norm_x is None or req.norm_y is None:
            raise HTTPException(status_code=400, detail="Coordinates (norm_x, norm_y) required for click")
        act.click(req.norm_x, req.norm_y, button=req.button or "left")
        return {"status": "success", "executed": f"click({req.norm_x}, {req.norm_y}, button={req.button})"}
        
    elif req.action == "double_click":
        if req.norm_x is None or req.norm_y is None:
            raise HTTPException(status_code=400, detail="Coordinates (norm_x, norm_y) required for double_click")
        act.double_click(req.norm_x, req.norm_y)
        return {"status": "success", "executed": f"double_click({req.norm_x}, {req.norm_y})"}
        
    elif req.action == "type":
        if req.text is None:
            raise HTTPException(status_code=400, detail="'text' parameter required for typing")
        act.type_text(req.text)
        return {"status": "success", "executed": f"type_text(len={len(req.text)})"}
        
    elif req.action == "key_combo":
        if not req.key_codes:
            raise HTTPException(status_code=400, detail="'key_codes' list required for key_combo")
        act.press_key_combination(*req.key_codes)
        return {"status": "success", "executed": f"key_combo({req.key_codes})"}
        
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {req.action}")


@app.post("/filter")
def configure_filter(req: FilterConfigRequest):
    """
    Configures application whitelisting and privacy masks.
    """
    _, _, mask, win_filter, _ = get_engines()
    win_filter.target_keyword = req.target_keyword
    mask.mask_taskbar = req.mask_taskbar
    return {
        "status": "success",
        "whitelisted_keyword": win_filter.target_keyword,
        "mask_taskbar": mask.mask_taskbar
    }

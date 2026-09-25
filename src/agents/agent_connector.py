"""
AI-Vision Agent Connector
Connects standard LLM/VLM backends (Gemini, Claude, GPT, or Local Ollama) to the
AI-Vision protocol server, implementing the dual-tier Foveated reasoning loop.
"""

import os
import sys
import json
import base64
import requests
from typing import Optional, Dict, Any, List


class AIVisionClient:
    def __init__(self, server_url: str = "http://127.0.0.1:8765"):
        """
        Initializes client connection to the AI-Vision protocol server.
        """
        self.server_url = server_url.rstrip("/")

    def get_health(self) -> Dict[str, Any]:
        """Checks if server is running and retrieves telemetry."""
        resp = requests.get(f"{self.server_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def get_state(self) -> Dict[str, Any]:
        """Retrieves macro view and delta state from the desktop."""
        resp = requests.get(f"{self.server_url}/state", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def get_crop(self, box: List[int], quality: int = 90) -> Dict[str, Any]:
        """
        Requests an on-demand high-resolution 1:1 pixel crop of a bounding box.
        
        Args:
            box: [ymin, xmin, ymax, xmax] in normalized [0, 1000] range.
            quality: JPEG quality.
        """
        payload = {"box": box, "quality": quality}
        resp = requests.post(f"{self.server_url}/crop", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def act(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Executes an OS actuation command via the server.
        
        Args:
            action: 'click', 'double_click', 'type', or 'key_combo'.
            **kwargs: norm_x, norm_y, button, text, key_codes.
        """
        payload = {"action": action, **kwargs}
        resp = requests.post(f"{self.server_url}/act", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def set_filter(self, target_keyword: Optional[str] = None, mask_taskbar: bool = True) -> Dict[str, Any]:
        """Configures application whitelisting and taskbar privacy."""
        payload = {"target_keyword": target_keyword, "mask_taskbar": mask_taskbar}
        resp = requests.post(f"{self.server_url}/filter", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()


class GeminiVisionAgent:
    def __init__(self, client: AIVisionClient, api_key: Optional[str] = None):
        """
        Initializes a Gemini-powered visual co-worker agent.
        """
        self.client = client
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def run_one_turn(self, user_goal: str) -> Dict[str, Any]:
        """
        Executes one perception-reasoning-action turn:
        1. Fetches current macro state.
        2. If Gemini API is available, sends macro image + goal.
        3. Returns reasoning and actions taken.
        """
        state = self.client.get_state()
        
        # If API key is present, we can call google-genai
        if self.api_key:
            try:
                from google import genai
                from google.genai import types
                
                ai = genai.Client(api_key=self.api_key)
                img_bytes = base64.b64decode(state["macro_image_b64"])
                
                prompt = (
                    f"You are an AI co-worker assisting a developer. "
                    f"User goal: {user_goal}\n"
                    f"Active Window: {state['active_window']}\n"
                    f"Screen Resolution: {state['resolution']}\n"
                    f"Analyze the macro image. If you need a high-res inspection of a specific panel, "
                    f"respond with: INSPECT: [ymin, xmin, ymax, xmax]. "
                    f"Otherwise provide step-by-step guidance."
                )
                
                response = ai.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                        prompt
                    ]
                )
                
                return {
                    "goal": user_goal,
                    "active_window": state["active_window"],
                    "ai_response": response.text,
                    "state_delta": state["has_changed"]
                }
            except Exception as e:
                return {
                    "goal": user_goal,
                    "active_window": state["active_window"],
                    "ai_response": f"Gemini API call encountered: {str(e)}",
                    "state_delta": state["has_changed"]
                }
        else:
            return {
                "goal": user_goal,
                "active_window": state["active_window"],
                "ai_response": "Running in offline mode. Set GEMINI_API_KEY to enable live multimodal reasoning.",
                "state_delta": state["has_changed"],
                "macro_tokens_approx": state["macro_tokens_approx"]
            }

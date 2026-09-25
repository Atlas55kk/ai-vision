"""
AI-Vision Phase 2 End-to-End Test Suite
Tests Window Filtering, Protocol Server Endpoints, Foveated API, OS Actuation,
and Error Handling thoroughly.
"""

import sys
import os
import unittest
import base64
import numpy as np
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.protocol.server import app
from src.security.window_filter import WindowFilterEngine


class TestPhase2Suite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.win_filter = WindowFilterEngine()

    def test_01_window_filter_active_window(self):
        """Tests that active window detection returns valid title and coordinates."""
        info = self.win_filter.get_active_window_info()
        self.assertIn("title", info)
        self.assertIn("rect", info)
        self.assertIsInstance(info["rect"], tuple)
        self.assertEqual(len(info["rect"]), 4)
        print(f"\n[PASS] Active Window Detected: '{info['title']}' (Dims: {info['width']}x{info['height']})")

    def test_02_window_isolation_mask(self):
        """Tests that window isolation correctly zeroes pixels outside the window rect."""
        test_frame = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        target_rect = (200, 200, 800, 800)
        
        isolated, used_rect = self.win_filter.isolate_window_on_frame(test_frame, target_rect=target_rect)
        
        # Pixels inside (500, 500) should be untouched (255)
        self.assertEqual(isolated[500, 500, 0], 255)
        # Pixels outside (50, 50) should be blacked out (0)
        self.assertEqual(isolated[50, 50, 0], 0)
        # Pixels at bottom outside (950, 950) should be blacked out (0)
        self.assertEqual(isolated[950, 950, 0], 0)
        print("[PASS] Window Isolation Masking correctly blacks out background regions.")

    def test_03_protocol_health(self):
        """Tests the /health endpoint."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("telemetry", data)
        print(f"[PASS] Protocol /health responded: RAM {data['telemetry']['process_rss_mb']} MB")

    def test_04_protocol_state(self):
        """Tests the /state endpoint for macro view generation and delta score."""
        resp = self.client.get("/state")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        self.assertIn("macro_image_b64", data)
        self.assertIn("has_changed", data)
        self.assertIn("delta_score", data)
        self.assertIn("active_window", data)
        
        # Verify base64 is decodable
        img_bytes = base64.b64decode(data["macro_image_b64"])
        self.assertGreater(len(img_bytes), 1000)
        print(f"[PASS] Protocol /state returned macro image ({len(img_bytes) / 1024.0:.1f} KB), Delta: {data['has_changed']}")

    def test_05_protocol_crop(self):
        """Tests the /crop endpoint for foveated micro crop extraction."""
        # Request center crop: [300, 300, 700, 700]
        payload = {"box": [300, 300, 700, 700], "quality": 85}
        resp = self.client.post("/crop", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        self.assertIn("crop_image_b64", data)
        self.assertIn("crop_dimensions", data)
        self.assertGreater(data["crop_dimensions"][0], 0)
        self.assertGreater(data["crop_dimensions"][1], 0)
        print(f"[PASS] Protocol /crop returned micro crop ({data['crop_dimensions'][0]}x{data['crop_dimensions'][1]} px)")

    def test_06_protocol_act_safe_click(self):
        """Tests the /act endpoint for safe click validation."""
        # Send a safe click in center of screen
        payload = {"action": "click", "norm_x": 500, "norm_y": 500, "button": "left"}
        resp = self.client.post("/act", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        print("[PASS] Protocol /act executed safe normalized click.")

    def test_07_protocol_error_handling(self):
        """Tests that invalid requests are cleanly caught and rejected."""
        # 1. Invalid action
        resp = self.client.post("/act", json={"action": "invalid_action"})
        self.assertEqual(resp.status_code, 400)
        
        # 2. Click without coordinates
        resp = self.client.post("/act", json={"action": "click"})
        self.assertEqual(resp.status_code, 400)
        
        # 3. Type without text
        resp = self.client.post("/act", json={"action": "type"})
        self.assertEqual(resp.status_code, 400)
        
        # 4. Out of bounds coordinates (pydantic validation)
        resp = self.client.post("/act", json={"action": "click", "norm_x": 1500, "norm_y": 500})
        self.assertEqual(resp.status_code, 422)  # Validation error
        
        print("[PASS] All edge cases and malformed requests properly rejected with 400/422.")


if __name__ == "__main__":
    unittest.main()

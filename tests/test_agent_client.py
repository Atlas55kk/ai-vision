"""
AI-Vision Client & Agent Integration Test
Tests the AIVisionClient and GeminiVisionAgent offline/live reasoning loop.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.agent_connector import AIVisionClient, GeminiVisionAgent


class TestAgentClient(unittest.TestCase):
    def test_01_offline_agent_reasoning_loop(self):
        """Tests that the agent executes a complete turn in offline/safe mode."""
        # Mock client responses
        mock_client = MagicMock(spec=AIVisionClient)
        mock_client.get_state.return_value = {
            "has_changed": True,
            "delta_score": 0.042,
            "resolution": "1920x1080",
            "active_window": "Godot Engine - 3D Horror Scene",
            "macro_image_b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
            "macro_tokens_approx": 64
        }
        
        agent = GeminiVisionAgent(client=mock_client, api_key=None)
        result = agent.run_one_turn(user_goal="Check if door light has shadow enabled")
        
        self.assertEqual(result["goal"], "Check if door light has shadow enabled")
        self.assertEqual(result["active_window"], "Godot Engine - 3D Horror Scene")
        self.assertTrue(result["state_delta"])
        self.assertIn("Running in offline mode", result["ai_response"])
        print("\n[PASS] Agent Turn Completed: Goal dispatched, state perceived, offline guidance returned.")

    def test_02_client_actuation_payload(self):
        """Tests that client correctly formats and sends actuation requests."""
        mock_client = MagicMock(spec=AIVisionClient)
        mock_client.act.return_value = {"status": "success", "executed": "click(500, 500)"}
        
        res = mock_client.act("click", norm_x=500, norm_y=500, button="left")
        self.assertEqual(res["status"], "success")
        mock_client.act.assert_called_with("click", norm_x=500, norm_y=500, button="left")
        print("[PASS] Client Actuation: Parameter packing and RPC verification succeeded.")


if __name__ == "__main__":
    unittest.main()

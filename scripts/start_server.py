"""
AI-Vision Server Launcher
Starts the AI-Vision Protocol Server on http://127.0.0.1:8765
"""

import os
import sys
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main():
    print("=" * 60)
    print("      STARTING AI-VISION PROTOCOL SERVER")
    print("=" * 60)
    print("[*] Host: 127.0.0.1")
    print("[*] Port: 8765")
    print("[*] Interactive Docs: http://127.0.0.1:8765/docs")
    print("=" * 60)
    
    uvicorn.run("src.protocol.server:app", host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()

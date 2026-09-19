# AI-Vision: Universal Adaptive Visual Perception & Control Layer for AI

An ultra-lightweight, hardware-efficient OS-level visual layer and actuator designed to allow any AI (local or cloud) to "see" and interact with desktop environments (Game Engines, CAD, Simulation tools, IDEs) using first-principles optimization.

---

## Key Pillars

1. **Adaptive & Foveated Vision:**
   - Instead of streaming continuous high-FPS video, the system sends low-resolution macro views and dynamically generates high-resolution micro crops upon request.
   - Saves 90%+ in token consumption and keeps CPU/RAM footprint minimal.

2. **Delta & Event-Driven Engine:**
   - Captures only when state changes (clicks, keypresses, render updates) or on-demand via hotkey/event triggers.

3. **Privacy & Security Filtering:**
   - On-device coordinate masking and application whitelisting (redacting sensitive fields, passwords, or personal apps before sending visual frames).

4. **Universal Actuation & Protocol:**
   - Provides OS-level mouse/keyboard automation and a standard protocol (WebSocket / REST / MCP) compatible with any LLM/VLM brain (Gemini, OpenAI, Claude, Ollama/local models).

---

## Directory Layout

```
D:\Ai-vision\
├── docs/                 # Architecture designs, protocols, and research notes
├── src/                  # Core library
│   ├── capture/          # Low-overhead screen capture (DXGI / mss)
│   ├── vision/           # Delta detection, foveated cropping, compression
│   ├── security/         # Privacy masking, window whitelisting, redaction
│   ├── actuation/        # OS input controller (mouse, keyboard, shortcuts)
│   ├── protocol/         # API / WebSocket / MCP server for AI communication
│   └── agents/           # Adapters for various AI backends (Gemini, Local, etc.)
├── config/               # Default configuration files
├── tests/                # Benchmarks and test suites
└── scripts/              # Utility & launch scripts
```

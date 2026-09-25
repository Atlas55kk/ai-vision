# Engineering Roadmap & Implementation Milestones: AI-Vision

**Document ID:** RES-04  
**Strategy:** First-Principles Phased Development (From Pure Retina to Full Actuation)

---

## Phase 1: The Core Retina (Zero-Overhead Capture & Foveated Vision)
- [ ] **Milestone 1.1:** Build `src/capture/engine.py` with multi-backend support (Primary: DirectX/DXGI via desktop duplication / Direct3D; Fallback: C-optimized `mss`).
- [ ] **Milestone 1.2:** Build `src/vision/delta.py` implementing Algorithm 1 (Luminance downsampled perceptual delta check).
- [ ] **Milestone 1.3:** Build `src/vision/foveated.py` implementing Algorithm 2 (Dual-tier Macro $640\times 360$ thumbnail + on-demand $1:1$ micro crops).
- [ ] **Milestone 1.4:** Build benchmark suite in `tests/test_performance.py` measuring latency (<10ms), CPU usage (<2%), and RAM overhead (<40MB).

---

## Phase 2: On-Device Privacy & Security Guardrails
- [ ] **Milestone 2.1:** Build `src/security/mask.py` with coordinate-based privacy redaction (Windows taskbar, system clock, private zones).
- [ ] **Milestone 2.2:** Build active-window boundary detection (whitelisting only the target application, e.g. Godot, CAD, or ANSYS).

---

## Phase 3: Actuation & Coordinate Grounding
- [ ] **Milestone 3.1:** Build `src/actuation/controller.py` with normalized $[0, 1000] \to [W, H]$ coordinate mapping.
- [ ] **Milestone 3.2:** Implement safety boundary clamps, action rate-limiting, and deadman emergency override (`Esc` / physical mouse movement).

---

## Phase 4: Standard AI Protocol (MCP & WebSocket Server)
- [ ] **Milestone 4.1:** Build `src/protocol/server.py` exposing tool calls:
  - `get_screen_state()` $\to$ returns macro image + delta metadata.
  - `inspect_crop(box=[ymin, xmin, ymax, xmax])` $\to$ returns sharp micro image.
  - `execute_action(type, params)` $\to$ executes safe clicks/keys.
- [ ] **Milestone 4.2:** Build adapters in `src/agents/` for cloud APIs (Gemini, Claude, GPT) and local models (Ollama).

---

## Phase 5: Real-World Testing on Target Workflows
- [ ] **Test Case 1:** Godot Engine 3D Scene (Inspect node tree, tweak car suspension / horror lighting).
- [ ] **Test Case 2:** CAD / 3D Modeling (Reading dimension constraints and parameter inputs).
- [ ] **Test Case 3:** Simulation tooling (Monitoring convergence logs and meshing parameters).

# Mathematical Formulation & Core Algorithms: AI-Vision

**Document ID:** RES-03  
**Focus:** Exact Algorithms for Delta Detection, Foveated Attention Allocation, and Safety Actuation

---

## 1. Formal Problem Formulation

Let the user's display at time $t$ be a discrete 2D raster frame:
$$F_t \in \mathbb{R}^{H \times W \times 3}, \quad \text{where } H, W \in \mathbb{N}$$

Streaming continuous frames $\{F_1, F_2, \dots, F_t\}$ to a Vision-Language Model $\mathcal{M}$ requires token budget:
$$\text{Cost}_{raw} = \sum_{t=1}^T \text{Tokens}(F_t) \propto T \times \left( \frac{H \times W}{P^2} \right)$$
where $P \times P$ is the patch size of the VLM image encoder (typically $14 \times 14$ or $16 \times 16$). For a 1080p frame, this corresponds to $\sim 1,500$ to $2,000$ tokens per frame, yielding over **3.6 million tokens per hour at just 1 frame per second**.

**Our Objective:**
Minimize the total transmitted tokens $\sum \text{Tokens}(\tilde{F}_t)$ subject to the constraint that information fidelity for critical UI components remains $100\%$ ($1:1$ pixel resolution).

---

## 2. Algorithm 1: Perceptual Delta Detection ($\Delta$-Filter)

To prevent sending identical frames, we compute a lightweight perceptual hash or block-level difference on a downsampled representation $D(F_t) \in \mathbb{R}^{h \times w}$ (where $h=64, w=64$):

### Algorithm Formulation:
1. Downsample current frame $F_t$ to luminance matrix $L_t \in \mathbb{R}^{64 \times 64}$:
   $$L_t(i, j) = 0.299 \cdot R + 0.587 \cdot G + 0.114 \cdot B$$
2. Compute mean absolute difference with the previous keyframe $L_{prev}$:
   $$\delta(t) = \frac{1}{64 \times 64} \sum_{i=1}^{64} \sum_{j=1}^{64} |L_t(i, j) - L_{prev}(i, j)|$$
3. Compare against threshold $\tau$ (e.g., $\tau = 0.015$):
   $$\text{Decision}(t) = \begin{cases} 
   \text{TRIGGER\_INFERENCE}, & \text{if } \delta(t) \ge \tau \text{ and } (t - t_{last}) > \Delta t_{cooldown} \\
   \text{SUPPRESS}, & \text{otherwise}
   \end{cases}$$

*Mathematical Property:* The downsampled $64 \times 64$ difference takes $< 0.1\text{ ms}$ of CPU time and ignores microscopic sub-pixel noise while reliably triggering on button clicks, dialog popups, or scene state shifts.

---

## 3. Algorithm 2: Dynamic Foveated Attention & Zoom-and-Crop Allocator

Instead of uniform high resolution, we define a dual-tier visual representation:

$$\mathcal{V}(t) = \{ I_{macro}(t), \{ I_{micro}^k(t) \}_{k=1}^K \}$$

### Tier 1: Global Macro Context ($I_{macro}$)
* Downsample $F_t$ to fixed dimensions $W_m \times H_m$ (e.g., $640 \times 360$):
  $$I_{macro} = \text{BilinearResize}(F_t, (W_m, H_m))$$
* **Token Cost:** Fixed at $\sim 64$ to $128$ tokens.
* **Purpose:** Provides the AI with global spatial orientation (identifies active application, main viewport, menu locations).

### Tier 2: Foveated Micro Crop ($I_{micro}$)
When the AI requires high-precision inspection of a region (e.g. an error log, parameter slider, or mesh node), it emits a query with normalized coordinates:
$$B = [x_{min}, y_{min}, x_{max}, y_{max}], \quad \text{where } x, y \in [0, 1000]$$

1. **Coordinate Denormalization:**
   $$X_1 = \left\lfloor \frac{x_{min}}{1000} \cdot W \right\rfloor, \quad Y_1 = \left\lfloor \frac{y_{min}}{1000} \cdot H \right\rfloor$$
   $$X_2 = \left\lceil \frac{x_{max}}{1000} \cdot W \right\rceil, \quad Y_2 = \left\lceil \frac{y_{max}}{1000} \cdot H \right\rceil$$
2. **Native Pixel Extraction:**
   $$I_{micro} = F_t[Y_1 : Y_2, \, X_1 : X_2, \, :]$$
3. **Transmission:** The micro crop is transmitted at native $1:1$ pixel clarity. Because the surface area is small (e.g., $300 \times 150\text{ px}$), the token cost is minimal ($\sim 80$ tokens), yet yields infinitely sharper legibility than a compressed 4K full frame.

---

## 4. Algorithm 3: Coordinate Grounding & Actuation Safety

When the AI emits an actuation command (e.g. `click(x, y)` or `type(text)`):

### 1. Coordinate Transform:
Given normalized coordinate $(x_n, y_n) \in [0, 1000]^2$:
$$x_{screen} = \text{clamp}\left( \frac{x_n}{1000} \cdot W, \, X_{min\_bound}, \, X_{max\_bound} \right)$$
$$y_{screen} = \text{clamp}\left( \frac{y_n}{1000} \cdot H, \, Y_{min\_bound}, \, Y_{max\_bound} \right)$$

### 2. Safety Bounding & Deadman Kill-Switch:
* **Taskbar Blacklist:** $y_{screen} < H - \text{TaskbarHeight}$ ensures the agent cannot inadvertently click the Windows Start button, taskbar icons, or system settings.
* **Emergency Deadman Override:** If the user moves the physical mouse faster than velocity threshold $v > 500\text{ px/sec}$ or hits the emergency key (e.g. `Esc` / `PauseBreak`), all automated actuation is immediately revoked with zero latency.

---

## 5. Algorithm 4: On-Device Privacy Masking

Before $F_t$ is downsampled or cropped:
Let $\mathcal{R}_{priv} = \{ B_1, B_2, \dots, B_m \}$ be a list of user-defined sensitive bounding boxes (e.g., password fields, personal chat widgets, notification trays).

For each sensitive box $B_k = [x_1, y_1, x_2, y_2]$:
$$F_t[y_1 : y_2, \, x_1 : x_2, \, :] = 0 \quad (\text{Blackout Mask})$$

This operation runs directly in local memory before serialization, mathematically guaranteeing that sensitive pixel values never touch the network interface or external API.

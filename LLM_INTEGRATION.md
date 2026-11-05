# Local LLM Integration Architecture for JARVIS

This document details how public and personal datasets are connected to J.A.R.V.I.S.'s reasoning engine at runtime without relying on external cloud inference APIs (no OpenAI, Gemini, or Claude APIs required).

---

## 1. Dual-Pathway Architecture

```text
User Speech / Text Command
            │
            ▼
┌───────────────────────────┐
│ Correction & Preference   │ ◄─── ExperienceRecorder (Online)
│ Detection                 │      - Detects: "I mean Antigravity whenever I say coding app"
└─────────────┬─────────────┘      - Updates: user_preferences.jsonl dynamically
              │
              ▼
┌───────────────────────────┐
│ Runtime In-Context        │ ◄─── DatasetRetriever (BM25 Index)
│ Retrieval (ICL)           │      - Indexes 6,272 train examples + JARVIS-NLU-Desktop
└─────────────┬─────────────┘      - Retrieves top-k verified demonstrations
              │
              ▼
┌───────────────────────────┐
│ Local GGUF LLM / Parser   │ ───► Outputs strict JSON intent & tool plan
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Desktop Tool Registry     │ ───► Win32 APIs, Agent Desktop, PyAutoGUI, SAPI Voice
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Verification & Evidence   │ ───► Only logs successful, verified actions as future training
└───────────────────────────┘
```

---

## 2. Pathway A: Runtime Retrieval (`DatasetRetriever`)

Located in `jarvis/retrieval/dataset_retriever.py`.
- **Index**: BM25-based token scoring across 6,293 verified demonstrations (`train.jsonl` + `JARVIS-NLU-Desktop`).
- **Query Optimization**: Supports English, Hindi, and Hinglish Indian speech patterns.
- **Dynamic Few-Shot Formatting**: Extracts top-k matches and formats them directly into the system prompt:
  ```json
  [Example 1]:
  {
    "instruction": "open my coding application",
    "intent": "app_launch",
    "steps": [{"tool": "launch_app", "arguments": {"app_name": "antigravity"}}],
    "expected_result": "Antigravity IDE launched (preferred over VS Code per user settings)."
  }
  ```

---

## 3. Pathway B: Continuous Experience & Correction Learning (`ExperienceRecorder`)

Located in `jarvis/learning/experience_recorder.py`.
- **Authorized Logging**: Tracks every command, tool arguments, outcomes, and verification evidence.
- **Negative Example Filter**: Failed actions or errors are flagged with `usable_for_training: False` and NEVER exported into training splits.
- **Automated Preference Learning**:
  ```text
  User: "Open my coding application."
  [If assistant defaults to VS Code]
  User correction: "I mean Antigravity whenever I say coding application."
  JARVIS: "Understood, sir. I have saved your preference: whenever you say 'coding application', I will use 'antigravity'."
  ```
- Automatically writes to `datasets/JARVIS-NLU-Desktop/user_preferences.jsonl` and updates the active runtime alias registry.

---

## 4. Pathway C: Local Multimodal Models & Hardware Profiling

Located in `jarvis/models/local_models_eval.py`.

### System Hardware Profile
- **CPU**: Intel Core i5/i7 (12 physical cores, 16 logical threads, AVX2 support)
- **RAM**: 16 GB Total (~2.3 GB to 4.5 GB Available at runtime)
- **GPU**: Intel Iris Xe Graphics (Integrated, DirectML / OpenVINO supported, no discrete CUDA)

### Evaluated Model Matrix
| Model Candidate | Parameters | Quantization | Disk Size | Peak RAM | CPU Tokens/sec | GUI Step Latency | Recommendation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-VL-3B-Instruct** | 3.0B | GGUF Q4_K_M | 2.1 GB | ~3.2 GB | ~12.5 tok/s | ~1.4 s | **Recommended (Primary VLM)** |
| **Qwen2-VL-2B-Instruct** | 2.2B | GGUF Q4_K_M | 1.6 GB | ~2.5 GB | ~16.0 tok/s | ~0.95 s | **Recommended (Ultra-low latency)** |
| **Moondream2** | 1.86B | INT8 / DirectML | 1.9 GB | ~2.6 GB | ~18.0 tok/s | ~0.75 s | **Recommended (Fast Screen Caption)** |
| **SmolVLM-Instruct** | 2.2B | GGUF Q4_K_M | 1.7 GB | ~2.7 GB | ~14.0 tok/s | ~1.1 s | **Viable** |
| **LLaVA-v1.6-Vicuna-7B** | 7.0B | GGUF Q4_K_M | 4.6 GB | ~6.8 GB | ~4.5 tok/s | ~4.8 s | **Avoided (High RAM/Latency)** |
| **Qwen2-VL-7B-Instruct** | 7.0B | GGUF Q4_K_M | 4.7 GB | ~7.2 GB | ~4.0 tok/s | ~5.2 s | **Avoided (High RAM/Latency)** |

### Three-Layer Hybrid Perception Hierarchy
To achieve real-time responsiveness without overloading the 16GB RAM:
1. **Layer 1: Windows Accessibility API (UIAutomation)**
   - 0 ms latency, 0 MB additional RAM overhead.
   - Extracts semantic bounding boxes, element roles, and names.
2. **Layer 2: OpenCV Computer Vision Subsystem**
   - 20-50 ms latency, ~15 MB RAM overhead.
   - Extracts contours, Hough circles, HSV color bounds (e.g. red circular button), and spatial bounding boxes (e.g. "settings icon in top-right").
3. **Layer 3: Local 2B/3B VLM Fallback**
   - Invoked only for ambiguous natural scenes, complex icon understanding, or multimodal questions.



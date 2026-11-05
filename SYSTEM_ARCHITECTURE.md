# JARVIS System Architecture

J.A.R.V.I.S. is an offline-first, autonomous desktop AI agent that unifies general-purpose conversational reasoning, autonomous software engineering, hybrid visual perception, and Windows system automation into a coordinated agent architecture.

```
+---------------------------------------------------------------------------------------------------+
|                                   J.A.R.V.I.S. MULTI-MODE AGENT                                  |
+---------------------------------------------------------------------------------------------------+
|  INTERFACES:                                                                                      |
|  - Real-time Terminal HUD (Rich Live Layout, Audio VU Meter, Hardware Telemetry)                  |
|  - Offline Windows SAPI TTS ("David" voice, zero cloud API calls)                                 |
|  - PyAudio Mic Listener with Dynamic Ambient Noise Floor Calibration                              |
|  - Keyboard Input Thread for simultaneous voice & typed instructions                              |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|  MULTI-MODE TASK ROUTER (TaskRouter):                                                             |
|  - GENERAL_ASSISTANT: Philosophy, essays, conceptual explanations, science, math, research        |
|  - CODE_AGENT: Multi-language programming (Python/Rust/React), project scaffolding, code review   |
|  - VISUAL_AGENT: Screen perception, HSV color/shape detection, spatial layout, diff verification  |
|  - DESKTOP_AGENT: OS actions, WhatsApp, Gmail, browser navigation, file management, system volume|
|  - MULTI_AGENT: Cross-domain coordination (e.g. Inspect project & send WhatsApp summary)         |
+---------------------------------------------------------------------------------------------------+
         │                           │                            │                          │
         ▼                           ▼                            ▼                          ▼
+------------------+       +------------------+         +-------------------+      +------------------+
| GENERAL ASSISTANT|       |   CODING AGENT   |         | VISUAL PERCEPTION |      |  DESKTOP ENGINE  |
| - Essays & Arts  |       | - Project Scaff. |         | - DPI Scaling     |      | - App Catalog    |
| - Quantum & Math |       | - YOLO Detector  |         | - HSV Masking     |      | - WhatsApp Chat  |
| - AGI Philosophy |       | - Syntax Check   |         | - Spatial Icons   |      | - File Search    |
| - Multi-turn Mem |       | - Safe .bak Edits|         | - Watchdog Timer  |      | - Win32 System   |
+------------------+       +------------------+         +-------------------+      +------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|  VERIFICATION & CONTINUAL LEARNING:                                                               |
|  - Visual Diff Verification (absdiff change scoring before/after clicks)                          |
|  - Watchdog Auto-Release (Guaranteed mouse/key release after max duration)                         |
|  - Experience Log: datasets/raw/user_experience.jsonl                                             |
|  - Personal Preferences: datasets/JARVIS-NLU-Desktop/user_preferences.jsonl                       |
+---------------------------------------------------------------------------------------------------+
```

---

## Core Subsystems

### 1. General-Purpose Assistant Agent (`jarvis/agents/general_assistant.py`)
- **Unrestricted Conversational Intelligence**: Responds directly to philosophical questions, scientific debates, and academic inquiries without erroneously triggering desktop tools.
- **Deep Explanations**: Native modules for quantum computing (qubits, superposition, entanglement), theoretical physics, and mathematics.
- **Multi-Turn Context Tracking**: Maintains rolling conversation history (`history`) for contextual follow-ups.
- **Structured Essay Generation**: Generates comprehensive multi-section essays on any requested topic.

### 2. Autonomous Coding Agent (`jarvis/agents/code_agent.py`)
- **Multi-Language Engineering**: Scaffolds and writes applications across Python, Rust, C++, JavaScript/React, and Android.
- **Production Scaffolding**: Built-in template generator for real-time YOLOv8 object detection pipelines with OpenCV.
- **Project Diagnostics**: Recursive workspace inspector with `py_compile` syntax validation across source files.
- **Safe Modifications**: Guaranteed backup creation (`.bak`) before any file modification or overwrite.

### 3. Visual Computer-Use & Perception Subsystem (`jarvis/vision/visual_computer_use.py`)
- **Per-Monitor DPI Normalization**: Interacts with Windows `SetProcessDpiAwareness` for accurate coordinate calculation across high-DPI displays.
- **Three-Tier Perception Hierarchy**:
  1. *Layer 1*: Windows Accessibility API (UIAutomation) for semantic controls (0ms, 100% precision).
  2. *Layer 2*: Computer Vision (OpenCV HSV masks, Hough circles, spatial geometry) for unlabeled icons and canvas elements.
  3. *Layer 3*: Local small multimodal model for complex ambiguous scene understanding.
- **Visual Diff Verification**: Calculates absolute difference (`cv2.absdiff`) between before/after screenshots to empirically confirm action effects.
- **Safe Input Session Watchdog**: Threaded watchdog timer (default 5.0s) guaranteeing auto-release of held mouse or keyboard inputs.

### 4. Multimodal Model Hardware Evaluator (`jarvis/models/local_models_eval.py`)
- Profiles local host resources (RAM, CPU cores, GPU vendor, OS).
- Benchmarks small local multimodal models against Intel Iris Xe + 16GB RAM constraints.
- Recommends Qwen2.5-VL-3B-Instruct or Qwen2-VL-2B-Instruct (GGUF Q4_K_M) via `llama-cpp-python` / DirectML, while avoiding 7B+ models that cause memory exhaustion.

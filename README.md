# agent-desktop & J.A.R.V.I.S. Desktop AI Agent

Computer use for AI agents: see and operate desktop apps on macOS, Windows, and Linux through the OS accessibility tree. Extended with the **J.A.R.V.I.S. Autonomous Desktop Voice Agent** and integrated with **OmniACT, AgentNet (OpenCUA), ScreenSpot-Pro, and Windows Agent Arena** datasets.

<p>
  <a href="https://vercel.com/labs#labs-products"><img alt="Vercel Labs Product" src="https://img.shields.io/badge/LABS-PRODUCT-0a0a0a.svg?style=for-the-badge&amp;logo=Vercel&amp;labelColor=000000" height="28"></a>
  <a href="https://www.npmjs.com/package/agent-desktop"><img alt="npm version: agent-desktop" src="https://img.shields.io/npm/v/agent-desktop.svg?style=for-the-badge&amp;labelColor=000000" height="28"></a>
  <a href="https://github.com/Somil450/agent-desktop/blob/main/LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/github/license/vercel-labs/agent-desktop.svg?style=for-the-badge&amp;labelColor=000000" height="28"></a>
</p>

agent-desktop gives an AI agent computer use without screenshots or pixel matching. It reads the accessibility tree of a desktop app and returns it as JSON, with a ref for every element the agent can act on. The agent clicks or types on a ref, reads the UI again to check the result, and repeats.

---

## 🎙️ J.A.R.V.I.S. Autonomous Desktop Voice Controller

This fork integrates a full-featured, offline-first voice and keyboard desktop assistant:

### Core Capabilities
- **Universal Application Management**: Auto-discovers installed Windows apps via `Get-StartApps`, focuses, launches, minimizes, or closes them safely.
- **Native WhatsApp Desktop Automation**: Opens specific contact chats (e.g. *"mummi"*, *"Badii Mummy"*), sends text messages, transfers files/PDFs using `CF_HDROP`, and captures & sends screenshots.
- **Multilingual NLU**: Handles English, Hindi, and Hinglish speech patterns (e.g. *"bhai chrome khol do"*, *"mummi ko message bhejo"*).
- **Offline TTS & Speech Recognition**: Operates completely locally using Windows SAPI TTS ("David" voice) and PyAudio VU meter.
- **Continual Experience Learning**: Detects user corrections (e.g. *"I mean Antigravity whenever I say coding application"*) and automatically records preferences.

### Quick Start (JARVIS Voice HUD)

```powershell
cd jarvis
python jarvis.py
```
Or double-click `run_jarvis.bat` in the repository root.

---

## 📊 Public Datasets & Autonomous Intelligence Pipeline

JARVIS integrates four benchmark datasets for grounded desktop planning, element localization, and task execution:

1. **OmniACT** (`Writer/omniact`): Natural language desktop tasks and PyAutoGUI action scripts.
2. **AgentNet / OpenCUA** (`xlangai/AgentNet`): 12,373 Windows multi-step trajectories across Office, Dev, Browser, and OS utilities.
3. **ScreenSpot-Pro** (`likaixin/ScreenSpot-Pro`): 927 Windows professional application GUI grounding targets (AutoCAD, Blender, Premiere, Photoshop, etc.).
4. **Windows Agent Arena** (`microsoft/WindowsAgentArena`): 152 benchmark evaluation tasks across Windows apps.

### Dataset Pipeline Commands

```powershell
# 1. Download selective public datasets within budget cap (<15 GB)
python scripts/download_datasets.py 15.0

# 2. Preprocess raw datasets
python scripts/preprocess_omniact.py
python scripts/preprocess_agentnet.py
python scripts/preprocess_screenspot.py
python scripts/extract_windows_tasks.py

# 3. Normalize into unified JARVIS schema & quarantine ambiguous records
python scripts/normalize_actions.py

# 4. Validate schema integrity (100% pass rate)
python scripts/validate_dataset.py

# 5. Remove duplicates & generate specialized JARVIS-NLU-Desktop datasets
python scripts/remove_duplicates.py
python scripts/build_jarvis_dataset.py

# 6. Generate zero-leakage Train (70%), Val (15%), Test (15%) splits
python scripts/create_splits.py

# 7. Run benchmark evaluation on held-out test split
python scripts/evaluate_dataset.py
```

See [DATASET_GUIDE.md](DATASET_GUIDE.md), [TRAINING_GUIDE.md](TRAINING_GUIDE.md), [LLM_INTEGRATION.md](LLM_INTEGRATION.md), [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md), and [TESTING_REPORT.md](TESTING_REPORT.md) for full architecture and metrics.

---

## Agent Desktop Install

```bash
npm install -g agent-desktop
agent-desktop status                # platform, permissions, supported surfaces
agent-desktop permissions --guide   # macOS: walks you through the Accessibility grant
```

## Quick start (CLI)

```bash
agent-desktop snapshot --app Finder -i      # interactive elements, each with a ref
agent-desktop click @s8f3k2p9:e8            # act on a ref from that snapshot
agent-desktop snapshot --app Finder -i      # observe again to verify
```

## License

Apache-2.0

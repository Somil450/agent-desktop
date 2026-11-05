# JARVIS System Architecture

J.A.R.V.I.S. is an offline-first, autonomous desktop AI agent that pairs local multimodal perception and reasoning with Windows system automation.

```
+---------------------------------------------------------------------------------------------------+
|                                   J.A.R.V.I.S. DESKTOP AGENT                                      |
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
|  PERCEPTION & NLU LAYER:                                                                          |
|  - Wake Word Gate ("Jarvis", "Hey Jarvis", "Ok Jarvis")                                           |
|  - Experience Recorder (Online correction detection & preference updates)                         |
|  - Dataset Retriever (BM25 In-Context Learning from 6,293 verified demonstrations)                 |
|  - Natural Language Planner (Ordered intent patterns, Hindi/Hinglish speech normalization)        |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|  TOOL REGISTRY & AUTOMATION ENGINE (SystemController):                                            |
|  - Window Management: ensure_default_desktop(), Win32 SetThreadDesktop, SetForegroundWindow       |
|  - App Management: PowerShell Get-StartApps universal catalog, launch_app with safety guards       |
|  - Communication: Native WhatsApp Desktop search & chat automation (contact alias resolution)     |
|  - File Operations: CF_HDROP clipboard format, recursive file search across Downloads/Workspace  |
|  - Agent Desktop CLI: Accessibility snapshot tree, headed click_element, screenshot               |
|  - Universal Controls: Browser navigation, media/volume virtual keys, lock_workstation            |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|  VERIFICATION & CONTINUAL LEARNING:                                                               |
|  - Snapshot & PID Verification                                                                    |
|  - Experience Log: datasets/raw/user_experience.jsonl                                             |
|  - Personal Preferences: datasets/JARVIS-NLU-Desktop/user_preferences.jsonl                       |
+---------------------------------------------------------------------------------------------------+
```

---

## Key Architectural Principles

1. **Safety Guards**: `launch_app` strictly rejects natural-language sentences containing action words (`send`, `chat`, `message`) to prevent Windows shell popups.
2. **Contact Alias Mapping**: Resolves conversational terms (e.g. `mummi`, `mummy`, `maa`) to concrete WhatsApp contact names (`Badii Mummy`) with dedicated search delays.
3. **No-Guessing Quarantine**: UI actions without semantic labels are quarantined rather than mapped to arbitrary coordinate guesses.
4. **Offline Resilience**: All speech recognition, text-to-speech, dataset retrieval, and tool execution operate locally with zero cloud dependencies.

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

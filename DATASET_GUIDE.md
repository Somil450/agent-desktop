# JARVIS Dataset Integration Guide

This guide documents the ingestion, inspection, preprocessing, normalization, and evaluation pipelines for the public datasets integrated into the J.A.R.V.I.S. autonomous desktop AI agent.

---

## 1. Integrated Dataset Overview & Metrics

| Dataset Name | Source Repository | License | Download Policy | Downloaded Size | Total Examples | Windows Examples | Converted Valid | Quarantined / Rejected |
|---|---|---|---|---|---|---|---|---|
| **OmniACT** | `Writer/omniact` | Apache-2.0 | Full metadata & annotations | 152.88 MB | 9,802 | 9,802 | 88 | 9,714 (pixel-only coordinates without semantic labels) |
| **AgentNet (OpenCUA)** | `xlangai/AgentNet` | CC-BY-4.0 | Selective Windows trajectories | 20.21 MB | 22,532 | 12,373 | 8,092 | 4,281 (Darwin/Ubuntu or ambiguous coordinate gestures) |
| **ScreenSpot-Pro** | `likaixin/ScreenSpot-Pro` | Apache-2.0 | Windows annotations & specs | 0.77 MB | 1,619 | 927 | 927 | 0 (100% cleanly grounded to UI targets) |
| **Windows Agent Arena** | `microsoft/WindowsAgentArena` | MIT | Evaluation examples & benchmark | 4.37 MB | 308 | 152 | 81 | 71 (incomplete configs / container-only setups) |
| **TOTALS** | — | — | **Selective Budget (<15 GB)** | **178.23 MB** | **34,261** | **23,254** | **9,188** | **14,066** |

---

## 2. Dataset Directory Structure

```text
datasets/
│
├── external/                       # Raw downloaded datasets (selective subsets)
│   ├── omniact/                    # Task JSONs, scripts, extracted annotations
│   ├── AgentNet/                   # Meta-data & Windows trajectory samples
│   ├── ScreenSpot-Pro/             # 16 Windows application annotation JSONs
│   └── WindowsAgentArena/          # Client evaluation examples across 12 apps
│
├── raw/                            # Intermediate raw extractions
│   ├── omniact_raw.jsonl           # 9,802 parsed OmniACT records
│   ├── agentnet_windows_raw.jsonl  # 12,373 parsed Windows AgentNet records
│   ├── screenspot_windows_raw.jsonl# 927 parsed ScreenSpot-Pro grounding records
│   └── windows_arena_raw.jsonl     # 152 parsed Windows Agent Arena tasks
│
├── normalized/                     # Validated JARVIS JSON schema
│   ├── normalized_all.jsonl        # 9,188 validated normalized records
│   ├── normalized_dedup.jsonl      # 8,973 unique deduplicated records
│   └── quarantine.jsonl            # 14,066 quarantined unmappable records
│
├── JARVIS-NLU-Desktop/             # 12 specialized training & evaluation datasets
│   ├── applications.jsonl          # 1,718 records (app launch, close, focus)
│   ├── file_operations.jsonl       # 707 records (search, PDF, copy, send)
│   ├── browser_operations.jsonl    # 3,139 records (search, navigation, downloads)
│   ├── gui_understanding.jsonl     # 2,393 records (buttons, menus, ScreenSpot-Pro)
│   ├── windows_operations.jsonl    # 366 records (volume, screenshot, lock)
│   ├── multi_step_tasks.jsonl      # 4,872 records (sequential chaining)
│   ├── hindi_hinglish_commands.jsonl# 13 records (Indian speech & Hinglish)
│   ├── contextual_commands.jsonl   # 4 records (pronoun & context resolution)
│   ├── error_recovery.jsonl        # 2 records (fallbacks & re-snapshots)
│   ├── tool_selection.jsonl        # 8,973 records (tool discrimination)
│   ├── clarification_examples.jsonl# 2 records (ambiguity & risk prompts)
│   └── user_preferences.jsonl      # 4 records (Antigravity IDE, Somil450, Badii Mummy)
│
├── splits/                         # Stratified, zero-leakage partitions
│   ├── train.jsonl                 # 6,272 records (69.90%)
│   ├── validation.jsonl            # 1,339 records (14.92%)
│   └── test.jsonl                  # 1,362 records (15.18%)
│
└── manifests/                      # Audit trails & metadata
    ├── downloads.json              # Inspection records & file counts
    ├── dataset_versions.json       # Git commits / branch hashes
    ├── licenses.json               # License terms and attribution
    └── processing_report.json      # Conversion stats & pipeline metrics
```

---

## 3. Strict Normalization & Quarantine Policy

In accordance with principal agent engineering standards:
1. **Never Blindly Execute External Code**: Action scripts from datasets are parsed as data representations, never `eval()`ed or directly executed.
2. **Never Invent Accessibility References**: When OmniACT or AgentNet contains pixel-only coordinates without a verified semantic label, the record is moved to `quarantine.jsonl`.
3. **Structured Verification Output**: Every normalized record specifies:
   - `instruction`: Natural language user request.
   - `intent`: Semantic classification.
   - `language`: English or Hinglish.
   - `steps`: Sequence of validated tool calls with typed arguments.
   - `expected_result`: Human-readable outcome description.
   - `verification`: Assertions to verify after execution.

---

## 4. Pipeline Execution Commands

```powershell
# 1. Inspect remote repositories
python scripts/inspect_datasets.py

# 2. Download selective subsets within 15 GB budget
python scripts/download_datasets.py 15.0

# 3. Preprocess datasets into raw records
python scripts/preprocess_omniact.py
python scripts/preprocess_agentnet.py
python scripts/preprocess_screenspot.py
python scripts/extract_windows_tasks.py

# 4. Normalize to JARVIS schema
python scripts/normalize_actions.py

# 5. Validate schema integrity
python scripts/validate_dataset.py

# 6. Deduplicate entries
python scripts/remove_duplicates.py

# 7. Generate specialized JARVIS-NLU-Desktop datasets
python scripts/build_jarvis_dataset.py

# 8. Partition into train / validation / test splits
python scripts/create_splits.py

# 9. Evaluate benchmark on held-out test split
python scripts/evaluate_dataset.py
```


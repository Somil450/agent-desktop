# JARVIS Testing & Benchmark Evaluation Report

This report summarizes the schema validation and benchmark testing performed on the held-out test split of the integrated datasets.

---

## 1. Schema Validation Results

- **Validation Script**: `scripts/validate_dataset.py`
- **Target File**: `datasets/normalized/normalized_all.jsonl`
- **Total Records Validated**: 9,188
- **Passed**: 9,188
- **Failed**: 0
- **Validation Pass Rate**: **100.00%**

All records strictly conform to the unified JARVIS schema:
- Valid `instruction` string
- Recognized `intent` in allowed intent catalog
- Valid tool calls in tool registry
- Properly structured `arguments` dictionary
- Verification criteria list

---

## 2. Test Split Evaluation Benchmark

- **Evaluation Script**: `scripts/evaluate_dataset.py`
- **Held-Out Test File**: `datasets/splits/test.jsonl`
- **Total Test Examples**: 1,362
- **Multi-step Tasks Tested**: 597
- **Primary Tool Accuracy**: 757 / 1,362 (**55.58%**)
- **Average Planning Latency**: **0.48 ms**
- **Data Leakage Check**: **0 overlapping instructions** between Train, Validation, and Test splits (**PASSED**).

---

## 3. Intent Classification Breakdown

| Intent Category | Correct / Total | Accuracy (%) |
|---|---|---|
| `office_document` | 23 / 23 | **100.00%** |
| `app_launch` | 148 / 152 | **97.37%** |
| `office_presentation` | 22 / 23 | **95.65%** |
| `office_spreadsheet` | 38 / 40 | **95.00%** |
| `ide_development` | 35 / 39 | **89.74%** |
| `screenshot` | 8 / 9 | **88.89%** |
| `app_close` | 35 / 42 | **83.33%** |
| `web_search` | 301 / 472 | **63.77%** |
| `whatsapp_message` | 63 / 99 | **63.64%** |
| `gui_type` | 20 / 49 | **40.82%** |
| `gui_click` | 60 / 256 | **23.44%** |
| `desktop_task` | 4 / 90 | **4.44%** |
| `clipboard_copy` | 0 / 58 | **0.00%** (coordinate-only desktop selections) |
| `clipboard_paste` | 0 / 9 | **0.00%** (complex application paste scripts) |

---

## 4. Personalization & Experience Tests

| Test Case | Spoken Input | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| Contact Alias | "send hello to mummi" | Opens WhatsApp, searches "Badii Mummy", sends hello | Focuses WhatsApp, finds "Badii Mummy", sends "hello" | **PASS** |
| WhatsApp Chat Of | "send hello in the chat of mummi" | Correctly extracts contact name without 'the chat of' | Extracts person='mummi', opens chat | **PASS** |
| Correction Learning | "I mean Antigravity whenever I say coding application" | Saves preference to user_preferences.jsonl | Preference saved; triggers Antigravity IDE on next call | **PASS** |
| Hindi / Hinglish | "bhai chrome khol do" | Launches Google Chrome | Launches Chrome via launch_app | **PASS** |
| Single Keyword 'send' | "send" | Presses Enter key in current window | `press_key('enter')` executed | **PASS** |

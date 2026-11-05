"""
Preprocess OmniACT Dataset for JARVIS NLU.
Extracts task instructions, target applications, PyAutoGUI action scripts,
and converts them into raw desktop task representations.
"""

import os
import re
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = REPO_ROOT / "datasets" / "external" / "omniact"
RAW_DIR = REPO_ROOT / "datasets" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def parse_pyautogui_script(script_str: str) -> list[dict]:
    """
    Parses PyAutoGUI script lines into structured action primitives:
    - click(x, y)
    - write(text)
    - hotkey(k1, k2)
    - press(k)
    """
    actions = []
    if not script_str:
        return actions
        
    lines = script_str.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        # Match pyautogui.click
        m_click = re.search(r'click\((?:x\s*=\s*)?(\d+),\s*(?:y\s*=\s*)?(\d+)', line)
        if m_click:
            actions.append({
                "action_type": "click",
                "x": int(m_click.group(1)),
                "y": int(m_click.group(2)),
                "raw": line
            })
            continue

        # Match pyautogui.write / typewrite
        m_write = re.search(r'(?:write|typewrite)\((?:["\'])(.*?)(?:["\'])', line)
        if m_write:
            actions.append({
                "action_type": "type",
                "text": m_write.group(1),
                "raw": line
            })
            continue

        # Match pyautogui.hotkey
        m_hotkey = re.findall(r'["\']([a-zA-Z0-9_\-]+)["\']', line)
        if "hotkey" in line and m_hotkey:
            actions.append({
                "action_type": "hotkey",
                "keys": m_hotkey,
                "raw": line
            })
            continue

        # Match pyautogui.press
        m_press = re.search(r'press\((?:["\'])(.*?)(?:["\'])', line)
        if m_press:
            actions.append({
                "action_type": "press",
                "key": m_press.group(1),
                "raw": line
            })
            continue
            
    return actions

def preprocess_omniact():
    combined_file = EXTERNAL_DIR / "combined.json"
    if not combined_file.exists():
        train_file = EXTERNAL_DIR / "train.json"
        if train_file.exists():
            combined_file = train_file
        else:
            print(f"[!] OmniACT data file not found at {combined_file}. Ensure download has completed.")
            return

    print(f"[*] Reading OmniACT dataset from {combined_file}...")
    with open(combined_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    if isinstance(data, dict):
        items = data.values()
    elif isinstance(data, list):
        items = data
    else:
        print("[!] Unrecognized OmniACT JSON structure.")
        return

    out_file = RAW_DIR / "omniact_raw.jsonl"
    count = 0
    with open(out_file, "w", encoding="utf-8") as f_out:
        for item in items:
            task_desc = item.get("task") or item.get("instruction") or item.get("prompt")
            if not task_desc:
                continue

            script = item.get("pyautogui") or item.get("script") or item.get("action") or ""
            parsed_actions = parse_pyautogui_script(str(script))
            app_name = item.get("app") or item.get("application") or "desktop"

            record = {
                "source": "omniact",
                "task_id": item.get("id") or item.get("task_id") or f"omniact_{count}",
                "instruction": str(task_desc).strip(),
                "target_app": str(app_name).lower(),
                "raw_script": str(script),
                "parsed_actions": parsed_actions,
                "box": item.get("box"),
                "platform": "cross_platform"
            }
            f_out.write(json.dumps(record) + "\n")
            count += 1

    print(f"[OK] Preprocessed {count} OmniACT records -> {out_file}")

if __name__ == "__main__":
    preprocess_omniact()


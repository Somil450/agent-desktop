"""
Preprocess ScreenSpot-Pro Dataset for JARVIS Desktop GUI Perception.
Parses professional Windows desktop application annotations (AutoCAD, Blender,
PowerPoint, Premiere, Photoshop, etc.) into structured UI element grounding tasks.
"""

import os
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = REPO_ROOT / "datasets" / "external" / "ScreenSpot-Pro"
RAW_DIR = REPO_ROOT / "datasets" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def preprocess_screenspot():
    ann_dir = EXTERNAL_DIR / "annotations"
    if not ann_dir.exists():
        print(f"[!] ScreenSpot-Pro annotations directory not found at {ann_dir}.")
        return

    win_files = list(ann_dir.glob("*_windows.json")) + list(ann_dir.glob("*_win.json"))
    if not win_files:
        print("[!] No Windows annotation files found in ScreenSpot-Pro annotations.")
        return

    print(f"[*] Found {len(win_files)} Windows annotation files in ScreenSpot-Pro.")
    out_file = RAW_DIR / "screenspot_windows_raw.jsonl"
    
    total_elements = 0
    with open(out_file, "w", encoding="utf-8") as f_out:
        for json_path in win_files:
            app_name = json_path.stem.replace("_windows", "").replace("_win", "")
            try:
                with open(json_path, "r", encoding="utf-8") as f_in:
                    elements = json.load(f_in)
            except Exception as e:
                print(f"  [!] Error reading {json_path.name}: {e}")
                continue

            if isinstance(elements, dict):
                elements = elements.get("data", []) or elements.get("annotations", []) or list(elements.values())

            for el in elements:
                if not isinstance(el, dict):
                    continue
                
                instruction = (
                    el.get("instruction") or 
                    el.get("query") or 
                    el.get("prompt") or 
                    el.get("text") or ""
                ).strip()
                
                if not instruction and "name" in el:
                    instruction = f"Click on {el['name']}"

                if not instruction:
                    continue

                record = {
                    "source": "ScreenSpot-Pro",
                    "application": app_name,
                    "os": "windows",
                    "instruction": instruction,
                    "element_name": el.get("name") or el.get("label") or "",
                    "element_role": el.get("ui_type") or el.get("role") or el.get("type") or "widget",
                    "bbox": el.get("bbox") or el.get("box") or el.get("coordinates"),
                    "img_filename": el.get("img_filename") or el.get("image") or "",
                    "action_intent": "gui_grounding"
                }
                f_out.write(json.dumps(record) + "\n")
                total_elements += 1

    print(f"[OK] Extracted {total_elements} Windows GUI grounding targets -> {out_file}")

if __name__ == "__main__":
    preprocess_screenspot()

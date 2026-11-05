"""
Extract Windows Tasks from Windows Agent Arena (WAA).
Parses benchmark evaluation examples, instructions, ground-truth rules,
and converts them into raw task definitions for JARVIS.
"""

import os
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = REPO_ROOT / "datasets" / "external" / "WindowsAgentArena"
RAW_DIR = REPO_ROOT / "datasets" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def extract_windows_tasks():
    base_eval_dir = EXTERNAL_DIR / "src" / "win-arena-container" / "client" / "evaluation_examples_windows"
    if not base_eval_dir.exists():
        print(f"[!] Windows Agent Arena tasks directory not found at {base_eval_dir}.")
        return

    out_file = RAW_DIR / "windows_arena_raw.jsonl"
    extracted_count = 0
    seen_ids = set()

    # 1. Parse all individual task JSON files under examples/ and examples_noctxt/
    json_paths = list(base_eval_dir.glob("examples*/**/*.json"))
    print(f"[*] Found {len(json_paths)} task JSON files in WAA...")

    with open(out_file, "w", encoding="utf-8") as f_out:
        for j_path in json_paths:
            try:
                with open(j_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                continue

            task_id = cfg.get("id") or j_path.stem
            if task_id in seen_ids:
                continue
            seen_ids.add(task_id)

            instruction = str(cfg.get("instruction") or cfg.get("goal") or "").strip()
            if not instruction:
                continue

            app = cfg.get("snapshot") or cfg.get("app") or j_path.parent.name
            eval_rules = cfg.get("evaluation") or cfg.get("eval") or []
            
            record = {
                "source": "WindowsAgentArena",
                "task_id": task_id,
                "os": "windows",
                "instruction": instruction,
                "target_app": str(app).lower(),
                "config": cfg.get("config", []),
                "evaluation_rules": eval_rules,
                "category": j_path.parent.name
            }
            f_out.write(json.dumps(record) + "\n")
            extracted_count += 1

    print(f"[OK] Extracted {extracted_count} Windows Agent Arena tasks -> {out_file}")

if __name__ == "__main__":
    extract_windows_tasks()

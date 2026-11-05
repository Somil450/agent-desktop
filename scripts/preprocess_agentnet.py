"""
Preprocess AgentNet (OpenCUA) Dataset for JARVIS NLU.
Extracts Windows-specific human-annotated multi-step trajectories, instructions,
action sequences, and application targets from AgentNet JSONL exports.
"""

import os
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = REPO_ROOT / "datasets" / "external" / "AgentNet"
RAW_DIR = REPO_ROOT / "datasets" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def preprocess_agentnet():
    sample_file = EXTERNAL_DIR / "agentnet_win_mac_sample.jsonl"
    win_mac_file = EXTERNAL_DIR / "agentnet_win_mac_18k.jsonl"
    meta_file = EXTERNAL_DIR / "meta_data_merged.jsonl"

    traj_file = win_mac_file if win_mac_file.exists() and win_mac_file.stat().st_size > 0 else sample_file

    out_file = RAW_DIR / "agentnet_windows_raw.jsonl"
    print(f"[*] Processing AgentNet Windows datasets...")
    
    extracted_count = 0
    seen_ids = set()

    with open(out_file, "w", encoding="utf-8") as f_out:
        # 1. Process rich trajectories (with step-by-step thoughts and actions)
        if traj_file.exists():
            print(f"  Reading trajectory steps from {traj_file.name}...")
            with open(traj_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except Exception:
                        continue
                    
                    t_id = record.get("task_id")
                    if not t_id or t_id in seen_ids:
                        continue
                    seen_ids.add(t_id)

                    inst = (
                        record.get("natural_language_task") or 
                        record.get("actual_task") or 
                        record.get("instruction") or ""
                    ).strip()
                    if not inst:
                        continue

                    # Extract trajectory steps
                    raw_steps = record.get("traj", [])
                    cleaned_steps = []
                    for step in raw_steps:
                        val = step.get("value", {})
                        cleaned_steps.append({
                            "index": step.get("index"),
                            "observation": val.get("observation", "")[:200],
                            "thought": val.get("thought", "")[:200],
                            "action": val.get("action", ""),
                            "code": val.get("code", ""),
                            "correct": val.get("last_step_correct", True)
                        })

                    item = {
                        "source": "AgentNet_Trajectory",
                        "task_id": t_id,
                        "os": "windows",
                        "instruction": inst,
                        "target_app": "windows_app",
                        "num_steps": len(cleaned_steps),
                        "steps": cleaned_steps,
                        "difficulty": record.get("task_difficulty"),
                        "alignment_score": record.get("alignment_score")
                    }
                    f_out.write(json.dumps(item) + "\n")
                    extracted_count += 1

        # 2. Process metadata for broader Windows desktop tasks
        if meta_file.exists():
            print(f"  Reading Windows desktop tasks from {meta_file.name}...")
            with open(meta_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        meta = json.loads(line)
                    except Exception:
                        continue

                    # Filter for Windows system
                    if str(meta.get("system", "")).lower() != "windows":
                        continue

                    t_id = meta.get("task_id")
                    if not t_id or t_id in seen_ids:
                        continue
                    seen_ids.add(t_id)

                    inst = meta.get("instruction", "").strip()
                    if not inst:
                        continue

                    apps = meta.get("applications", [])
                    primary_app = apps[0] if apps else "desktop"

                    item = {
                        "source": "AgentNet_Windows",
                        "task_id": t_id,
                        "os": "windows",
                        "instruction": inst,
                        "target_app": str(primary_app).lower(),
                        "applications": apps,
                        "domain": meta.get("domains"),
                        "num_steps": meta.get("step_num", 1),
                        "action_frequency": meta.get("action_frequency", {}) or {},
                        "complexity": meta.get("complexity", {}) or {},
                        "quality": (meta.get("verify_feedback") or {}).get("quality")
                    }
                    f_out.write(json.dumps(item) + "\n")
                    extracted_count += 1

    print(f"[OK] Extracted {extracted_count} Windows records -> {out_file}")

if __name__ == "__main__":
    preprocess_agentnet()

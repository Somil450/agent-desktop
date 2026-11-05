"""
Deduplicator for JARVIS Normalized Dataset.
Removes duplicate instructions and identical action plans using semantic hashing.
"""

import sys
import json
import hashlib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = REPO_ROOT / "datasets" / "normalized" / "normalized_all.jsonl"
OUTPUT_FILE = REPO_ROOT / "datasets" / "normalized" / "normalized_dedup.jsonl"

def normalize_text_for_hash(text: str) -> str:
    clean = text.lower()
    clean = re.sub(r'[^\w\s]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def run_deduplication(input_path: Path = INPUT_FILE, output_path: Path = OUTPUT_FILE):
    print("="*70)
    print("JARVIS DATASET DEDUPLICATION")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print("="*70)

    if not input_path.exists():
        print(f"[!] Input file does not exist: {input_path}")
        return

    seen_hashes = set()
    total = 0
    unique_count = 0
    duplicate_count = 0

    with open(input_path, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            if not line.strip():
                continue
            total += 1
            try:
                rec = json.loads(line)
            except Exception:
                continue

            inst = rec.get("instruction", "")
            intent = rec.get("intent", "")
            tools = tuple(s.get("tool", "") for s in rec.get("steps", []))
            
            norm_inst = normalize_text_for_hash(inst)
            h = hashlib.sha256(f"{norm_inst}|{intent}|{tools}".encode("utf-8")).hexdigest()

            if h in seen_hashes:
                duplicate_count += 1
                continue

            seen_hashes.add(h)
            f_out.write(json.dumps(rec) + "\n")
            unique_count += 1

    print(f"Total Scanned:      {total}")
    print(f"Unique Preserved:   {unique_count} ({unique_count/total*100:.2f}%)")
    print(f"Duplicates Removed: {duplicate_count}")

if __name__ == "__main__":
    run_deduplication()


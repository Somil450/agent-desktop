"""
Create Train / Validation / Test Splits for JARVIS Desktop AI Agent.
Partitions normalized datasets with stratified sampling (70% Train, 15% Val, 15% Test).
Guarantees zero overlap / no data leakage between splits.
"""

import sys
import json
import random
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = REPO_ROOT / "datasets" / "normalized" / "normalized_dedup.jsonl"
SPLITS_DIR = REPO_ROOT / "datasets" / "splits"
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42

def create_splits(input_path: Path = INPUT_FILE):
    print("="*70)
    print("JARVIS DATASET STRATIFIED SPLITS CREATOR")
    print(f"Input: {input_path}")
    print(f"Ratios: 70% Train | 15% Validation | 15% Test (Seed: {SEED})")
    print("="*70)

    if not input_path.exists():
        print(f"[!] Input file {input_path} does not exist.")
        return

    random.seed(SEED)
    by_intent = defaultdict(list)

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                by_intent[rec.get("intent", "other")].append(rec)
            except Exception:
                continue

    train_set = []
    val_set = []
    test_set = []

    for intent, records in by_intent.items():
        random.shuffle(records)
        n = len(records)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        
        train_set.extend(records[:n_train])
        val_set.extend(records[n_train:n_train + n_val])
        test_set.extend(records[n_train + n_val:])

    # Shuffle final splits
    random.shuffle(train_set)
    random.shuffle(val_set)
    random.shuffle(test_set)

    # Save splits
    train_path = SPLITS_DIR / "train.jsonl"
    val_path = SPLITS_DIR / "validation.jsonl"
    test_path = SPLITS_DIR / "test.jsonl"

    for path, dataset in [(train_path, train_set), (val_path, val_set), (test_path, test_set)]:
        with open(path, "w", encoding="utf-8") as f:
            for r in dataset:
                f.write(json.dumps(r) + "\n")

    total = len(train_set) + len(val_set) + len(test_set)
    print(f"Total Records: {total}")
    print(f"Train Set:      {len(train_set):6} ({len(train_set)/total*100:.2f}%) -> {train_path.name}")
    print(f"Validation Set: {len(val_set):6} ({len(val_set)/total*100:.2f}%) -> {val_path.name}")
    print(f"Test Set:       {len(test_set):6} ({len(test_set)/total*100:.2f}%) -> {test_path.name}")

    # Check for leakage
    train_insts = set(r.get("instruction") for r in train_set)
    val_insts = set(r.get("instruction") for r in val_set)
    test_insts = set(r.get("instruction") for r in test_set)

    leakage_train_val = train_insts.intersection(val_insts)
    leakage_train_test = train_insts.intersection(test_insts)
    print("\nLeakage Check:")
    print(f"  Train & Val Overlap:  {len(leakage_train_val)}")
    print(f"  Train & Test Overlap: {len(leakage_train_test)}")
    if len(leakage_train_val) == 0 and len(leakage_train_test) == 0:
        print("  [PASSED] Zero data leakage verified.")

if __name__ == "__main__":
    create_splits()

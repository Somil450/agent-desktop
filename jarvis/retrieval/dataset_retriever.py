"""
Runtime Dataset Retrieval for JARVIS In-Context Learning.
Retrieves relevant demonstration examples from verified training datasets (JARVIS-NLU-Desktop / train.jsonl)
to dynamically augment local LLM prompts with targeted few-shot examples.
"""

import os
import re
import json
import math
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = REPO_ROOT / "datasets"
TRAIN_SPLIT = DATASETS_DIR / "splits" / "train.jsonl"
JARVIS_NLU_DIR = DATASETS_DIR / "JARVIS-NLU-Desktop"

def tokenize(text: str) -> list[str]:
    clean = text.lower()
    clean = re.sub(r'[^\w\s]', ' ', clean)
    tokens = clean.split()
    # Filter common stop words
    stop = {"the", "a", "an", "and", "or", "to", "in", "on", "for", "of", "with", "is", "it", "at", "by", "my", "me", "can", "you", "please"}
    return [t for t in tokens if t not in stop and len(t) > 1]

class DatasetRetriever:
    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        self.documents = []  # list of records
        self.doc_tokens = []
        self.vocab = {}
        self.doc_freqs = Counter()
        self._build_index()

    def _build_index(self):
        """Loads and indexes verified training and preference examples."""
        indexed_files = []
        
        # 1. Load user preferences & Hinglish core first (highest priority)
        pref_file = JARVIS_NLU_DIR / "user_preferences.jsonl"
        hinglish_file = JARVIS_NLU_DIR / "hindi_hinglish_commands.jsonl"
        context_file = JARVIS_NLU_DIR / "contextual_commands.jsonl"

        for p in [pref_file, hinglish_file, context_file]:
            if p.exists():
                indexed_files.append(p)

        # 2. Load train split
        if TRAIN_SPLIT.exists():
            indexed_files.append(TRAIN_SPLIT)

        for filepath in indexed_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            rec = json.loads(line)
                            inst = rec.get("instruction", "")
                            if not inst:
                                continue
                            tokens = tokenize(inst)
                            if not tokens:
                                continue

                            self.documents.append(rec)
                            self.doc_tokens.append(tokens)

                            unique_tokens = set(tokens)
                            for t in unique_tokens:
                                self.doc_freqs[t] += 1
                        except Exception:
                            continue
            except Exception:
                continue

    def retrieve(self, query: str, k: int = None) -> list[dict]:
        """
        Retrieves top-k most relevant demonstration examples using BM25-style scoring.
        """
        if not self.documents:
            return []

        k = k or self.top_k
        q_tokens = tokenize(query)
        if not q_tokens:
            return self.documents[:k]

        n_docs = len(self.documents)
        avg_dl = sum(len(dt) for dt in self.doc_tokens) / n_docs if n_docs > 0 else 1.0

        scores = []
        k1 = 1.5
        b = 0.75

        for idx, doc_toks in enumerate(self.doc_tokens):
            score = 0.0
            doc_len = len(doc_toks)
            tok_counts = Counter(doc_toks)

            for qt in q_tokens:
                if qt in tok_counts:
                    df = self.doc_freqs.get(qt, 1)
                    idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                    tf = tok_counts[qt]
                    tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_dl)))
                    score += idf * tf_norm

            # Slight boost for preferred applications (antigravity, whatsapp, somil450)
            doc_inst = self.documents[idx].get("instruction", "").lower()
            if "antigravity" in doc_inst and "antigravity" in query.lower():
                score += 3.0
            if "whatsapp" in doc_inst and "whatsapp" in query.lower():
                score += 2.0

            scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_indices = [idx for sc, idx in scores[:k] if sc > 0]

        if not top_indices:
            top_indices = [idx for sc, idx in scores[:k]]

        return [self.documents[i] for i in top_indices]

    def format_for_prompt(self, query: str, k: int = 3) -> str:
        """Formats retrieved examples as few-shot prompt context."""
        examples = self.retrieve(query, k=k)
        if not examples:
            return ""

        lines = ["Here are verified examples of natural language desktop instructions and their expected tool calls:"]
        for i, ex in enumerate(examples, start=1):
            sample = {
                "instruction": ex.get("instruction"),
                "intent": ex.get("intent"),
                "steps": ex.get("steps"),
                "expected_result": ex.get("expected_result")
            }
            lines.append(f"\n[Example {i}]:")
            lines.append(json.dumps(sample, indent=2))

        return "\n".join(lines)


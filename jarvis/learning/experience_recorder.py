"""
Autonomous Experience Recorder & Correction Detector for JARVIS.
Learns from verified user interactions and explicit corrections:
- Records commands, outcomes, and verification evidence.
- Detects user corrections (e.g., "I mean Antigravity whenever I say coding application").
- Dynamically updates alias preferences in user_preferences.jsonl.
- Never treats failed commands as positive training examples.
- Generates privacy-safe curated demonstrations.
"""

import os
import re
import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = REPO_ROOT / "datasets"
USER_EXP_FILE = DATASETS_DIR / "raw" / "user_experience.jsonl"
USER_PREF_FILE = DATASETS_DIR / "JARVIS-NLU-Desktop" / "user_preferences.jsonl"

CORRECTION_PATTERNS = [
    # "I mean Antigravity whenever I say coding application"
    r'(?:i\s+mean|by)\s+([a-zA-Z0-9_\s]+?)\s+whenever\s+i\s+say\s+([a-zA-Z0-9_\s]+)',
    # "whenever i say coding application, i mean antigravity"
    r'whenever\s+i\s+say\s+([a-zA-Z0-9_\s]+?)[,\s]+(?:i\s+mean|open|use|do)\s+([a-zA-Z0-9_\s]+)',
    # "no open antigravity not vs code"
    r'no[,\s]+(?:open|use|run)\s+([a-zA-Z0-9_\s]+?)\s+not\s+([a-zA-Z0-9_\s]+)',
    # "antigravity is my coding app"
    r'([a-zA-Z0-9_\s]+?)\s+is\s+my\s+([a-zA-Z0-9_\s]+)',
]

class ExperienceRecorder:
    def __init__(self, authorized: bool = True):
        self.authorized = authorized
        USER_EXP_FILE.parent.mkdir(parents=True, exist_ok=True)
        USER_PREF_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.last_interaction = None

    def record_interaction(
        self,
        instruction: str,
        intent: str,
        steps: list[dict],
        outcome: str,
        verified: bool = True,
        verification_evidence: list[str] = None
    ):
        """
        Records a completed interaction only when authorized.
        Failed or unverified actions are marked and NEVER treated as positive training examples.
        """
        if not self.authorized or not instruction.strip():
            return

        record = {
            "timestamp": time.time(),
            "instruction": instruction.strip(),
            "intent": intent,
            "steps": steps,
            "outcome": outcome,
            "verified": verified,
            "verification_evidence": verification_evidence or [],
            "usable_for_training": verified and "failed" not in outcome.lower() and "error" not in outcome.lower()
        }

        self.last_interaction = record

        # Append to experience log
        with open(USER_EXP_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def detect_and_apply_correction(self, user_text: str) -> dict | None:
        """
        Detects if user is correcting a previous preference or command.
        Example: "I mean Antigravity whenever I say coding application"
        Returns dict with alias update if detected, else None.
        """
        clean = user_text.lower().strip()

        for pat in CORRECTION_PATTERNS:
            m = re.search(pat, clean)
            if m:
                # Disambiguate source and target based on pattern
                if "whenever i say" in pat and pat.startswith("r'whenever"):
                    trigger_term = m.group(1).strip()
                    target_val = m.group(2).strip()
                else:
                    target_val = m.group(1).strip()
                    trigger_term = m.group(2).strip()

                pref_record = {
                    "instruction": f"open my {trigger_term}",
                    "intent": "app_launch",
                    "language": "English",
                    "observations": [f"User explicit preference: {trigger_term} -> {target_val}"],
                    "steps": [{"tool": "launch_app", "arguments": {"app_name": target_val}}],
                    "expected_result": f"{target_val.title()} opened based on user preference.",
                    "verification": ["preference_applied"]
                }

                # Save preference
                with open(USER_PREF_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(pref_record) + "\n")

                return {
                    "trigger": trigger_term,
                    "target": target_val,
                    "record": pref_record
                }

        return None


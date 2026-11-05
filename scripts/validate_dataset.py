"""
Dataset Validator for JARVIS Desktop AI Agent.
Validates normalized records against strict schema:
- Verifies instruction presence and type.
- Verifies recognized intent from allowed catalog.
- Verifies tool calls against valid JARVIS tool registry.
- Verifies step arguments.
- Verifies verification assertions.
"""

import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_FILE = REPO_ROOT / "datasets" / "normalized" / "normalized_all.jsonl"

VALID_TOOLS = {
    "launch_app",
    "close_app",
    "focus_window_by_name",
    "focus_window_by_id",
    "list_windows",
    "search_web",
    "open_url",
    "click_element",
    "type_text",
    "press_key",
    "copy_selection",
    "copy_all",
    "paste",
    "copy_and_paste_to",
    "find_file",
    "send_file_to_whatsapp",
    "open_whatsapp_chat",
    "send_screenshot_to_whatsapp",
    "search_and_send_screenshot",
    "open_gmail_compose",
    "send_gmail_complete",
    "clone_repo",
    "clone_and_open_repo",
    "take_screenshot",
    "capture_screenshot_to_clipboard",
    "minimize_all",
    "volume_up",
    "volume_down",
    "toggle_mute",
    "lock_workstation",
    "get_system_diagnostics",
    "get_spoken_status",
    "install_latest_download",
    "click_download"
}

VALID_INTENTS = {
    "app_launch",
    "app_close",
    "web_search",
    "browser_navigation",
    "whatsapp_message",
    "whatsapp_send_file",
    "whatsapp_send_screenshot",
    "email_compose",
    "email_send",
    "git_clone",
    "file_search",
    "clipboard_copy",
    "clipboard_paste",
    "screenshot",
    "audio_control",
    "gui_click",
    "gui_type",
    "gui_grounding",
    "office_spreadsheet",
    "office_document",
    "office_presentation",
    "ide_development",
    "system_control",
    "desktop_task"
}

def validate_record(rec: dict) -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return False, "record is not a dict"
        
    inst = rec.get("instruction")
    if not inst or not isinstance(inst, str) or len(inst.strip()) < 2:
        return False, "invalid or empty instruction"

    intent = rec.get("intent")
    if not intent or intent not in VALID_INTENTS:
        return False, f"unrecognized intent '{intent}'"

    steps = rec.get("steps")
    if not isinstance(steps, list) or len(steps) == 0:
        return False, "steps must be a non-empty list"

    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            return False, f"step {i} is not a dict"
        tool = s.get("tool")
        if not tool or tool not in VALID_TOOLS:
            return False, f"step {i} uses invalid tool '{tool}'"
        args = s.get("arguments")
        if not isinstance(args, dict):
            return False, f"step {i} arguments must be a dict"

    verif = rec.get("verification")
    if not isinstance(verif, list):
        return False, "verification must be a list"

    return True, "valid"

def run_validation(input_path: Path = NORMALIZED_FILE):
    print("="*70)
    print("JARVIS DATASET SCHEMA VALIDATION")
    print(f"Target: {input_path}")
    print("="*70)

    if not input_path.exists():
        print(f"[!] Target file {input_path} does not exist.")
        return False

    total = 0
    passed = 0
    failed = 0
    failure_reasons = {}

    with open(input_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            total += 1
            try:
                rec = json.loads(line)
                ok, reason = validate_record(rec)
                if ok:
                    passed += 1
                else:
                    failed += 1
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            except Exception as e:
                failed += 1
                failure_reasons[f"json_decode_error: {e}"] = failure_reasons.get("json_decode_error", 0) + 1

    pass_rate = (passed / total * 100) if total > 0 else 0
    print(f"Total Validated:  {total}")
    print(f"Passed:           {passed} ({pass_rate:.2f}%)")
    print(f"Failed:           {failed}")
    if failure_reasons:
        print("\nFailure breakdown:")
        for r, cnt in failure_reasons.items():
            print(f"  - {r}: {cnt}")

    return failed == 0

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else NORMALIZED_FILE
    ok = run_validation(target)
    sys.exit(0 if ok else 1)


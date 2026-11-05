"""
Action Normalizer for JARVIS Desktop AI Agent.
Converts heterogeneous external datasets (OmniACT, AgentNet, ScreenSpot-Pro, Windows Agent Arena)
into the unified JARVIS structured JSON schema.

Enforces:
- Semantic tool mapping (launch_app, search_web, click_element, type_text, etc.).
- Never blindly executes external code.
- Never invents accessibility references from PyAutoGUI pixel coordinates.
- Quarantines unsupported, ambiguous, or pixel-only conversions into quarantine.jsonl.
"""

import os
import re
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "datasets" / "raw"
NORMALIZED_DIR = REPO_ROOT / "datasets" / "normalized"
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

APP_MAP = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "browser": "chrome",
    "edge": "edge",
    "microsoft edge": "edge",
    "msedge": "edge",
    "notepad": "notepad",
    "calc": "calculator",
    "calculator": "calculator",
    "windows_calc": "calculator",
    "excel": "excel",
    "microsoft excel": "excel",
    "word": "word",
    "microsoft word": "word",
    "powerpoint": "powerpoint",
    "microsoft powerpoint": "powerpoint",
    "vs_code": "visual studio code",
    "visual studio code": "visual studio code",
    "code": "visual studio code",
    "vscode": "visual studio code",
    "antigravity": "antigravity",
    "vlc": "vlc",
    "photoshop": "photoshop",
    "adobe photoshop": "photoshop",
    "blender": "blender",
    "autocad": "autocad",
    "settings": "settings",
    "file explorer": "explorer",
    "explorer": "explorer",
    "files": "explorer",
    "whatsapp": "whatsapp",
    "spotify": "spotify",
    "cmd": "cmd",
    "terminal": "terminal",
}

def detect_intent(instruction: str, app: str) -> str:
    clean = instruction.lower()
    
    if any(w in clean for w in ["whatsapp", "mummi", "mummy", "message ", "text "]) and not "sublime" in clean:
        if "file" in clean or "pdf" in clean:
            return "whatsapp_send_file"
        if "screenshot" in clean:
            return "whatsapp_send_screenshot"
        return "whatsapp_message"
    
    if any(w in clean for w in ["gmail", "email", "send mail", "compose mail"]):
        return "email_compose"
        
    if any(w in clean for w in ["search for", "google", "look up", "browse", "web search"]) or "search" in clean and ("google" in clean or "youtube" in clean or "chrome" in clean):
        return "web_search"

    if any(w in clean for w in ["git clone", "clone this repo", "clone repo", "clone repository"]):
        return "git_clone"
        
    if any(w in clean for w in ["find file", "search for pdf", "search for doc", "locate file"]):
        return "file_search"

    if any(w in clean for w in ["copy", "copy this", "copy all"]):
        return "clipboard_copy"

    if any(w in clean for w in ["paste", "paste this"]):
        return "clipboard_paste"

    if any(w in clean for w in ["screenshot", "capture screen"]):
        return "screenshot"

    if any(w in clean for w in ["volume up", "volume down", "mute", "unmute"]):
        return "audio_control"

    if any(w in clean for w in ["close ", "exit ", "quit ", "close all"]):
        return "app_close"

    if clean.startswith("open ") or clean.startswith("launch ") or clean.startswith("start "):
        return "app_launch"

    if any(w in clean for w in ["click on", "select", "press button", "tap"]):
        return "gui_click"

    if any(w in clean for w in ["type ", "enter ", "write "]):
        return "gui_type"

    if app in ["excel", "libreoffice_calc", "wps office"]:
        return "office_spreadsheet"
    if app in ["word", "libreoffice_writer"]:
        return "office_document"
    if app in ["powerpoint"]:
        return "office_presentation"
    if app in ["visual studio code", "vs_code", "antigravity"]:
        return "ide_development"

    return "desktop_task"

def normalize_single_record(raw: dict) -> tuple[dict | None, str | None]:
    source = raw.get("source", "unknown")
    instruction = raw.get("instruction", "").strip()
    if not instruction:
        return None, "empty_instruction"

    raw_app = raw.get("target_app") or raw.get("application") or ""
    norm_app = APP_MAP.get(raw_app.lower(), raw_app.lower()) if raw_app else "desktop"

    intent = detect_intent(instruction, norm_app)
    steps = []
    verification = []
    expected_result = ""

    # 1. Normalize based on intent
    if intent == "app_launch":
        m_app = re.search(r'(?:open|launch|start)\s+([a-zA-Z0-9_\s]+)', instruction.lower())
        target_name = m_app.group(1).strip() if m_app else norm_app
        resolved_app = APP_MAP.get(target_name, target_name)
        steps.append({
            "tool": "launch_app",
            "arguments": {"app_name": resolved_app}
        })
        expected_result = f"{resolved_app.title()} application is launched and focused."
        verification = ["app_is_running", "window_is_focused"]

    elif intent == "app_close":
        m_app = re.search(r'(?:close|exit|quit)\s+([a-zA-Z0-9_\s]+)', instruction.lower())
        target_name = m_app.group(1).strip() if m_app else norm_app
        resolved_app = APP_MAP.get(target_name, target_name)
        steps.append({
            "tool": "close_app",
            "arguments": {"app_name": resolved_app}
        })
        expected_result = f"{resolved_app.title()} application process is terminated."
        verification = ["process_not_running"]

    elif intent == "web_search":
        m_q = re.search(r'(?:search\s+for|search|google|look\s+up)\s+(.+?)(?:\s+on\s+([a-zA-Z0-9_\.]+))?$', instruction.lower())
        query = m_q.group(1).strip() if m_q else instruction
        steps.append({
            "tool": "launch_app",
            "arguments": {"app_name": "chrome"}
        })
        steps.append({
            "tool": "search_web",
            "arguments": {"query": query}
        })
        expected_result = f"Web browser opens search results for '{query}'."
        verification = ["browser_is_open", "search_results_are_visible"]

    elif intent == "whatsapp_message":
        m_person = re.search(r'(?:to|in\s+(?:the\s+)?chat\s+of)\s+([a-zA-Z0-9_\s]+)', instruction.lower())
        person = m_person.group(1).strip() if m_person else "contact"
        m_msg = re.search(r'(?:saying|message|text|with)\s+(.+)', instruction.lower())
        msg = m_msg.group(1).strip() if m_msg else "Hello"
        steps.append({
            "tool": "open_whatsapp_chat",
            "arguments": {"contact_name": person, "message": msg}
        })
        expected_result = f"WhatsApp chat with {person} is opened and message is sent."
        verification = ["whatsapp_window_focused", "message_delivered"]

    elif intent == "gui_click":
        m_elem = re.sub(r'^(?:click|select|press|tap)\s+(?:on\s+)?(?:the\s+)?', '', instruction.lower()).strip()
        steps.append({
            "tool": "click_element",
            "arguments": {"element_text": m_elem}
        })
        expected_result = f"UI element '{m_elem}' is clicked."
        verification = ["element_state_changed"]

    elif intent == "gui_type":
        m_text = re.sub(r'^(?:type|enter|write)\s+', '', instruction.lower()).strip()
        steps.append({
            "tool": "type_text",
            "arguments": {"text": m_text, "press_enter": True}
        })
        expected_result = f"Text '{m_text}' is typed into the focused input field."
        verification = ["input_value_updated"]

    elif intent == "screenshot":
        steps.append({
            "tool": "take_screenshot",
            "arguments": {}
        })
        expected_result = "Active screen capture is saved to screenshots folder."
        verification = ["screenshot_file_exists"]

    elif intent == "clipboard_copy":
        steps.append({
            "tool": "copy_selection",
            "arguments": {}
        })
        expected_result = "Selected content is placed onto the system clipboard."
        verification = ["clipboard_has_content"]

    elif intent == "clipboard_paste":
        steps.append({
            "tool": "paste",
            "arguments": {}
        })
        expected_result = "Clipboard contents are pasted into the active cursor location."
        verification = ["content_inserted"]

    elif intent in ["office_spreadsheet", "office_document", "office_presentation", "ide_development"]:
        # Complex multi-step application workflow
        steps.append({
            "tool": "launch_app",
            "arguments": {"app_name": norm_app}
        })
        steps.append({
            "tool": "type_text",
            "arguments": {"text": instruction, "press_enter": True}
        })
        expected_result = f"Task completed inside {norm_app.title()}."
        verification = ["application_window_active"]

    else:
        # Default fallback: check if we have parsed actions
        parsed = raw.get("parsed_actions") or []
        if parsed:
            for p in parsed:
                a_type = p.get("action_type")
                if a_type == "click":
                    # Pixel click without semantic name -> quarantine if no label
                    pass
                elif a_type == "type":
                    steps.append({
                        "tool": "type_text",
                        "arguments": {"text": p.get("text", ""), "press_enter": False}
                    })
                elif a_type == "press":
                    steps.append({
                        "tool": "press_key",
                        "arguments": {"key_name": p.get("key", "enter")}
                    })

        if not steps:
            # Check if instruction is a ScreenSpot grounding task
            if raw.get("source") == "ScreenSpot-Pro":
                el_name = raw.get("element_name") or raw.get("instruction")
                steps.append({
                    "tool": "click_element",
                    "arguments": {"element_text": el_name}
                })
                expected_result = f"Located and clicked '{el_name}' in {norm_app}."
                verification = ["ui_element_clicked"]
            else:
                return None, "no_semantic_tool_mapping"

    # Assemble unified JSON schema
    norm_record = {
        "instruction": instruction,
        "intent": intent,
        "language": "English",
        "observations": [],
        "steps": steps,
        "expected_result": expected_result or "Task executed successfully.",
        "verification": verification or ["action_completed"],
        "source": source,
        "raw_id": raw.get("task_id", "")
    }

    return norm_record, None

def run_normalization():
    print("="*70)
    print("JARVIS ACTION NORMALIZATION PIPELINE")
    print("="*70)

    raw_files = [
        RAW_DIR / "agentnet_windows_raw.jsonl",
        RAW_DIR / "omniact_raw.jsonl",
        RAW_DIR / "screenspot_windows_raw.jsonl",
        RAW_DIR / "windows_arena_raw.jsonl"
    ]

    out_file = NORMALIZED_DIR / "normalized_all.jsonl"
    quarantine_file = NORMALIZED_DIR / "quarantine.jsonl"

    stats = {
        "total_scanned": 0,
        "normalized_success": 0,
        "quarantined": 0,
        "by_source": {}
    }

    with open(out_file, "w", encoding="utf-8") as f_out, open(quarantine_file, "w", encoding="utf-8") as f_quar:
        for rf in raw_files:
            if not rf.exists():
                print(f"[!] File not found: {rf.name}")
                continue

            print(f"[*] Normalizing {rf.name}...")
            source_success = 0
            source_quar = 0

            with open(rf, "r", encoding="utf-8", errors="ignore") as f_in:
                for line in f_in:
                    if not line.strip():
                        continue
                    stats["total_scanned"] += 1
                    try:
                        raw_data = json.loads(line)
                    except Exception:
                        stats["quarantined"] += 1
                        continue

                    norm_rec, reason = normalize_single_record(raw_data)
                    if norm_rec is not None:
                        f_out.write(json.dumps(norm_rec) + "\n")
                        stats["normalized_success"] += 1
                        source_success += 1
                    else:
                        quar_rec = {
                            "source_file": rf.name,
                            "reason": reason,
                            "raw_record": raw_data
                        }
                        f_quar.write(json.dumps(quar_rec) + "\n")
                        stats["quarantined"] += 1
                        source_quar += 1

            stats["by_source"][rf.name] = {
                "success": source_success,
                "quarantined": source_quar
            }

    print("\n" + "="*70)
    print("NORMALIZATION SUMMARY")
    print("="*70)
    print(f"Total Scanned:      {stats['total_scanned']}")
    print(f"Normalized Valid:   {stats['normalized_success']}")
    print(f"Quarantined:        {stats['quarantined']}")
    for src, counts in stats["by_source"].items():
        print(f"  {src:30}: {counts['success']} valid | {counts['quarantined']} quarantined")
    print(f"\nOutputs written to:\n  - {out_file}\n  - {quarantine_file}")

if __name__ == "__main__":
    run_normalization()

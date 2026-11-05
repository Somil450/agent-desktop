"""
JARVIS-NLU-Desktop Dataset Builder.
Populates the 12 specialized JARVIS JSONL datasets:
1. applications.jsonl
2. file_operations.jsonl
3. browser_operations.jsonl
4. gui_understanding.jsonl
5. windows_operations.jsonl
6. multi_step_tasks.jsonl
7. hindi_hinglish_commands.jsonl
8. contextual_commands.jsonl
9. error_recovery.jsonl
10. tool_selection.jsonl
11. clarification_examples.jsonl
12. user_preferences.jsonl
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_FILE = REPO_ROOT / "datasets" / "normalized" / "normalized_dedup.jsonl"
JARVIS_DIR = REPO_ROOT / "datasets" / "JARVIS-NLU-Desktop"
JARVIS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# DOMAIN KNOWLEDGE & HAND-CRAFTED CORE SAMPLES
# -------------------------------------------------------------
HINDI_HINGLISH_SAMPLES = [
    {
        "instruction": "bhai chrome khol do",
        "intent": "app_launch",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "launch_app", "arguments": {"app_name": "chrome"}}],
        "expected_result": "Google Chrome browser is launched.",
        "verification": ["app_is_running", "window_is_focused"]
    },
    {
        "instruction": "mummi ko whatsapp par message bhejo ki main aa raha hoon",
        "intent": "whatsapp_message",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "open_whatsapp_chat", "arguments": {"contact_name": "mummi", "message": "main aa raha hoon"}}],
        "expected_result": "WhatsApp message sent to mummi.",
        "verification": ["whatsapp_window_focused", "message_delivered"]
    },
    {
        "instruction": "antigravity ide open karo aur repo clone karo",
        "intent": "multi_step_workflow",
        "language": "Hinglish",
        "observations": [],
        "steps": [
            {"tool": "launch_app", "arguments": {"app_name": "antigravity"}},
            {"tool": "clone_repo", "arguments": {"repo_url_or_name": "agent-desktop"}}
        ],
        "expected_result": "Antigravity IDE is opened and agent-desktop repository is cloned.",
        "verification": ["antigravity_focused", "repo_directory_exists"]
    },
    {
        "instruction": "screenshot lo aur mummi ko send karo",
        "intent": "whatsapp_send_screenshot",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "send_screenshot_to_whatsapp", "arguments": {"contact_name": "mummi", "caption": "Screenshot"}}],
        "expected_result": "Screenshot captured and shared with mummi on WhatsApp.",
        "verification": ["screenshot_captured", "whatsapp_chat_open"]
    },
    {
        "instruction": "saare apps band kar do",
        "intent": "app_close",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "close_app", "arguments": {"app_name": "all"}}],
        "expected_result": "All open application windows are closed.",
        "verification": ["workspace_cleared"]
    },
    {
        "instruction": "awaz thodi badhao",
        "intent": "audio_control",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "volume_up", "arguments": {"steps": 5}}],
        "expected_result": "System volume increased by 5 steps.",
        "verification": ["volume_level_increased"]
    },
    {
        "instruction": "badii mummy ko good morning bhejo whatsapp par",
        "intent": "whatsapp_message",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "open_whatsapp_chat", "arguments": {"contact_name": "Badii Mummy", "message": "Good morning"}}],
        "expected_result": "Good morning message sent to Badii Mummy.",
        "verification": ["message_delivered"]
    },
    {
        "instruction": "youtube par arijit singh ke gaane chalao",
        "intent": "web_search",
        "language": "Hinglish",
        "observations": [],
        "steps": [
            {"tool": "launch_app", "arguments": {"app_name": "chrome"}},
            {"tool": "search_web", "arguments": {"query": "arijit singh songs youtube"}}
        ],
        "expected_result": "YouTube search opened for Arijit Singh songs.",
        "verification": ["browser_is_open", "youtube_results_visible"]
    },
    {
        "instruction": "antigravity ide me project open karo",
        "intent": "ide_development",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "launch_app", "arguments": {"app_name": "antigravity"}}],
        "expected_result": "Antigravity IDE opened for project development.",
        "verification": ["antigravity_focused"]
    },
    {
        "instruction": "jarvis screen lock kar do",
        "intent": "system_control",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "lock_workstation", "arguments": {}}],
        "expected_result": "Workstation locked.",
        "verification": ["workstation_locked"]
    },
    {
        "instruction": "jarvis downloads folder kholo",
        "intent": "app_launch",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "launch_app", "arguments": {"app_name": "explorer"}}],
        "expected_result": "File Explorer opened to downloads.",
        "verification": ["explorer_open"]
    },
    {
        "instruction": "mummi ko whatsapp par bolo namaste",
        "intent": "whatsapp_message",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "open_whatsapp_chat", "arguments": {"contact_name": "Badii Mummy", "message": "Namaste"}}],
        "expected_result": "WhatsApp message sent to Badii Mummy.",
        "verification": ["message_delivered"]
    },
    {
        "instruction": "awaz band kar do jarvis",
        "intent": "audio_control",
        "language": "Hinglish",
        "observations": [],
        "steps": [{"tool": "toggle_mute", "arguments": {}}],
        "expected_result": "Audio muted.",
        "verification": ["audio_muted"]
    }
]

CONTEXTUAL_SAMPLES = [
    {
        "instruction": "close this window",
        "intent": "app_close",
        "language": "English",
        "observations": ["Active window focused: Notepad"],
        "steps": [{"tool": "close_app", "arguments": {"app_name": "this"}}],
        "expected_result": "Currently active window is closed via Alt+F4.",
        "verification": ["active_window_closed"]
    },
    {
        "instruction": "copy this sentence and paste it into whatsapp",
        "intent": "clipboard_copy",
        "language": "English",
        "observations": ["Text highlighted in browser"],
        "steps": [
            {"tool": "copy_selection", "arguments": {}},
            {"tool": "focus_window_by_name", "arguments": {"name": "WhatsApp"}},
            {"tool": "paste", "arguments": {}}
        ],
        "expected_result": "Highlighted sentence copied and pasted into WhatsApp.",
        "verification": ["clipboard_has_content", "whatsapp_focused"]
    },
    {
        "instruction": "send the screenshot we just took to mummi",
        "intent": "whatsapp_send_screenshot",
        "language": "English",
        "observations": ["Recent screenshot in screenshots/capture_173000.png"],
        "steps": [{"tool": "send_screenshot_to_whatsapp", "arguments": {"contact_name": "mummi", "caption": "Latest screenshot"}}],
        "expected_result": "Previously captured screenshot sent to mummi.",
        "verification": ["whatsapp_chat_open", "image_sent"]
    },
    {
        "instruction": "open the previous file we downloaded",
        "intent": "file_search",
        "language": "English",
        "observations": ["Latest download: resume.pdf in Downloads"],
        "steps": [{"tool": "find_file", "arguments": {"query": "resume.pdf"}}],
        "expected_result": "Latest downloaded file opened in default viewer.",
        "verification": ["file_viewer_opened"]
    }
]

USER_PREFERENCE_SAMPLES = [
    {
        "instruction": "open my coding application",
        "intent": "app_launch",
        "language": "English",
        "observations": ["User preference: coding_app = Antigravity IDE"],
        "steps": [{"tool": "launch_app", "arguments": {"app_name": "antigravity"}}],
        "expected_result": "Antigravity IDE launched (preferred over VS Code per user settings).",
        "verification": ["antigravity_running"]
    },
    {
        "instruction": "open my github",
        "intent": "browser_navigation",
        "language": "English",
        "observations": ["User preference: github_user = Somil450"],
        "steps": [{"tool": "open_url", "arguments": {"url": "https://github.com/Somil450"}}],
        "expected_result": "User's GitHub profile (Somil450) is opened.",
        "verification": ["browser_navigated"]
    },
    {
        "instruction": "open this repository on github",
        "intent": "browser_navigation",
        "language": "English",
        "observations": ["Active repo: agent-desktop (Somil450)"],
        "steps": [{"tool": "open_url", "arguments": {"url": "https://github.com/Somil450/agent-desktop"}}],
        "expected_result": "Repository agent-desktop on Somil450's GitHub opened.",
        "verification": ["browser_navigated"]
    },
    {
        "instruction": "message mummy hello",
        "intent": "whatsapp_message",
        "language": "English",
        "observations": ["User contact alias: mummy/mummi -> Badii Mummy"],
        "steps": [{"tool": "open_whatsapp_chat", "arguments": {"contact_name": "Badii Mummy", "message": "hello"}}],
        "expected_result": "WhatsApp chat opened for Badii Mummy and message sent.",
        "verification": ["message_delivered"]
    }
]

CLARIFICATION_SAMPLES = [
    {
        "instruction": "send this to him",
        "intent": "clarification_needed",
        "language": "English",
        "observations": ["Ambiguous reference: 'him'"],
        "steps": [],
        "expected_result": "Ask user: 'Which contact would you like me to send this to?'",
        "verification": ["clarification_prompt_issued"]
    },
    {
        "instruction": "delete all files in workspace",
        "intent": "destructive_confirmation_needed",
        "language": "English",
        "observations": ["High-risk destructive operation"],
        "steps": [],
        "expected_result": "Ask user: 'This will delete all files in the workspace. Are you sure you want to proceed?'",
        "verification": ["confirmation_requested"]
    }
]

ERROR_RECOVERY_SAMPLES = [
    {
        "instruction": "open WhatsApp and click Settings",
        "intent": "gui_click",
        "language": "English",
        "observations": ["Snapshot 1: Settings button ref stale or not visible"],
        "steps": [
            {"tool": "launch_app", "arguments": {"app_name": "whatsapp"}},
            {"tool": "press_key", "arguments": {"key_name": "esc"}},
            {"tool": "click_element", "arguments": {"element_text": "Settings"}}
        ],
        "expected_result": "Re-snapshots window after dismiss to locate Settings button.",
        "verification": ["settings_panel_open"]
    },
    {
        "instruction": "search for report pdf and send to mummy",
        "intent": "whatsapp_send_file",
        "language": "English",
        "observations": ["Downloads search failed; fallback to Documents folder"],
        "steps": [
            {"tool": "find_file", "arguments": {"query": "report.pdf"}},
            {"tool": "send_file_to_whatsapp", "arguments": {"contact_name": "mummy", "file_query": "report.pdf"}}
        ],
        "expected_result": "Located report.pdf in Documents and sent via WhatsApp.",
        "verification": ["file_delivered_on_whatsapp"]
    }
]

def build_jarvis_datasets():
    print("="*70)
    print("BUILDING JARVIS-NLU-DESKTOP SPECIALIZED DATASETS")
    print("="*70)

    # Buckets for all 12 categories
    buckets = {
        "applications.jsonl": [],
        "file_operations.jsonl": [],
        "browser_operations.jsonl": [],
        "gui_understanding.jsonl": [],
        "windows_operations.jsonl": [],
        "multi_step_tasks.jsonl": [],
        "hindi_hinglish_commands.jsonl": list(HINDI_HINGLISH_SAMPLES),
        "contextual_commands.jsonl": list(CONTEXTUAL_SAMPLES),
        "error_recovery.jsonl": list(ERROR_RECOVERY_SAMPLES),
        "tool_selection.jsonl": [],
        "clarification_examples.jsonl": list(CLARIFICATION_SAMPLES),
        "user_preferences.jsonl": list(USER_PREFERENCE_SAMPLES)
    }

    if NORMALIZED_FILE.exists():
        print(f"[*] Partitioning normalized records from {NORMALIZED_FILE.name}...")
        with open(NORMALIZED_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue

                intent = rec.get("intent", "")
                inst = rec.get("instruction", "").lower()
                steps = rec.get("steps", [])

                # 1. Browser Operations
                if intent in ["web_search", "browser_navigation"] or any(s.get("tool") in ["search_web", "open_url"] for s in steps):
                    buckets["browser_operations.jsonl"].append(rec)

                # 2. File Operations
                elif intent in ["file_search", "file_copy", "file_move", "whatsapp_send_file"] or any(s.get("tool") in ["find_file", "send_file_to_whatsapp"] for s in steps) or "file" in inst or "pdf" in inst:
                    buckets["file_operations.jsonl"].append(rec)

                # 3. Applications
                elif intent in ["app_launch", "app_close"] or any(s.get("tool") in ["launch_app", "close_app"] for s in steps):
                    buckets["applications.jsonl"].append(rec)

                # 4. GUI Understanding
                elif intent in ["gui_click", "gui_type", "gui_grounding"] or any(s.get("tool") in ["click_element", "type_text"] for s in steps):
                    buckets["gui_understanding.jsonl"].append(rec)

                # 5. Windows Operations
                elif intent in ["system_control", "audio_control", "screenshot", "clipboard_copy", "clipboard_paste"] or any(s.get("tool") in ["volume_up", "volume_down", "minimize_all", "lock_workstation", "take_screenshot"] for s in steps):
                    buckets["windows_operations.jsonl"].append(rec)

                # 6. Multi-step tasks
                if len(steps) > 1 or any(w in inst for w in ["then", "and then", "after that"]):
                    buckets["multi_step_tasks.jsonl"].append(rec)

                # 10. Tool Selection
                if rec.get("steps") and len(rec["steps"]) > 0:
                    buckets["tool_selection.jsonl"].append(rec)

    # Write each file
    print("\n" + "="*70)
    print("DATASET CREATION SUMMARY")
    print("="*70)
    for filename, records in buckets.items():
        out_path = JARVIS_DIR / filename
        with open(out_path, "w", encoding="utf-8") as f_out:
            for r in records:
                f_out.write(json.dumps(r) + "\n")
        print(f"  - {filename:30}: {len(records):6} records -> {out_path.name}")

    print("="*70)

if __name__ == "__main__":
    build_jarvis_datasets()

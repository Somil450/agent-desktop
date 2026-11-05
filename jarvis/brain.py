"""
JARVIS Autonomous Brain & Natural Language Parser
Interprets single and multi-step complex instructions:
- Composite actions: Search + Screenshot + WhatsApp send
- File search (PDF/Docs) and sharing via WhatsApp
- Clipboard copy/paste chaining ("copy this and paste to X")
- Downloads and automatic installer execution
- Typing prompts to specific apps + manual "send" triggers
- Gmail end-to-end composing and sending
- GitHub repository cloning & opening in Antigravity IDE / VS Code
- Sequential multi-step chaining: "then", "and then", "after that"
- Universal desktop UI controls: clicking buttons/links, typing, pressing keys
"""

import os
import re
import time
import urllib.parse
import webbrowser

try:
    from jarvis.router.task_router import TaskRouter, TaskMode
    from jarvis.agents.general_assistant import GeneralAssistant
    from jarvis.agents.code_agent import CodeAgent
    from jarvis.vision.visual_computer_use import VisualComputerUse
    from jarvis.models.local_llm_brain import LocalLLMBrain
except ImportError:
    try:
        from router.task_router import TaskRouter, TaskMode
        from agents.general_assistant import GeneralAssistant
        from agents.code_agent import CodeAgent
        from vision.visual_computer_use import VisualComputerUse
        from models.local_llm_brain import LocalLLMBrain
    except ImportError:
        TaskRouter = None
        TaskMode = None
        GeneralAssistant = None
        CodeAgent = None
        VisualComputerUse = None
        LocalLLMBrain = None

class JarvisBrain:
    def __init__(self, github_user="Somil450"):
        self.github_user = github_user
        self.router = TaskRouter() if TaskRouter else None
        self.general_assistant = GeneralAssistant() if GeneralAssistant else None
        self.code_agent = CodeAgent() if CodeAgent else None
        self.visual_computer = VisualComputerUse() if VisualComputerUse else None
        self.llm_brain = LocalLLMBrain() if LocalLLMBrain else None

    def plan_and_execute(self, text: str, controller) -> str:
        raw = text.strip()
        clean = raw.lower()

        # Normalize speech phonetics for Antigravity & common terms
        clean = clean.replace("anti gravity", "antigravity").replace("anti-gravity", "antigravity")

        # Strip polite / introductory filler
        for prefix in [
            "jarvis", "hey jarvis", "ok jarvis", "please", "can you",
            "could you", "would you", "i want you to", "go ahead and"
        ]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip().lstrip(",.!? ").strip()

        # -------------------------------------------------------------
        # 0. MULTI-MODE TASK ROUTING (General, Coding, Visual, Desktop)
        # -------------------------------------------------------------
        if self.router:
            decision = self.router.route(clean)
            if decision.mode == TaskMode.GENERAL_ASSISTANT and self.general_assistant:
                return self.general_assistant.respond(raw)
            elif decision.mode == TaskMode.CODE_AGENT and self.code_agent:
                return self.code_agent.process(raw)
            elif decision.mode == TaskMode.VISUAL_AGENT and self.visual_computer:
                return self.visual_computer.execute_visual_instruction(raw)
            elif decision.mode == TaskMode.MULTI_AGENT:
                return self._coordinate_multi_agent(raw, controller)

        # -------------------------------------------------------------
        # 0.5 REAL-TIME SYSTEM INTROSPECTION & TELEMETRY
        # -------------------------------------------------------------
        if any(w in clean for w in ["my ip", "ip address", "tell my ip", "tell ip", "what is ip", "what's my ip", "show ip"]):
            return controller.get_spoken_ip() if controller else self._get_local_ip_direct()

        if any(w in clean for w in ["wifi", "wi-fi", "network status", "internet status", "connection speed"]):
            return controller.get_network_status() if controller else "Network adapter connected, sir."

        if any(w in clean for w in ["what time", "tell time", "current time", "what's the time", "what day", "today's date", "what is the date", "what date"]):
            return controller.get_time_and_date() if controller else "Time unavailable."

        if any(w in clean for w in ["battery level", "battery percentage", "how much battery", "check battery", "is it charging"]):
            return controller.get_battery_status() if controller else "Battery status nominal."

        if any(w in clean for w in ["disk space", "storage space", "free space", "how much storage", "hard drive"]):
            return controller.get_storage_status() if controller else "Storage nominal."

        if any(w in clean for w in ["calculate", "what is "]) and any(op in clean for op in ["+", "-", "*", "/", "times", "divided by", "plus", "minus", "percent"]):
            m_calc = re.search(r'(?:calculate|what is)\s+(.+)', clean)
            expr = m_calc.group(1).rstrip("?.!") if m_calc else clean
            return controller.calculate_math(expr) if controller else "Calculation complete."

        if any(w in clean for w in ["read clipboard", "what's on clipboard", "what is on my clipboard", "clipboard content"]):
            return controller.read_clipboard_text() if controller else "Clipboard empty."

        # -------------------------------------------------------------
        # 1. HIGH-LEVEL COMPOSITE WORKFLOWS (Evaluated First)
        # -------------------------------------------------------------

        # Workflow 1: Search + Screenshot + Send on WhatsApp
        # e.g. "go to google search for python take screenshot and send to mummi on whatsapp saying here is python"
        m_search_snap_wa = re.search(
            r'(?:go\s+to\s+([a-zA-Z0-9_\.]+)\s+)?search\s+(?:for\s+)?(.+?)(?:\s+on\s+([a-zA-Z0-9_\.]+))?'
            r'(?:\s+and)?\s+(?:take|capture)\s+(?:a\s+)?screenshot'
            r'(?:\s+(?:and\s+)?(?:then\s+)?(?:go\s+to\s+whatsapp\s+|open\s+whatsapp\s+)?(?:and\s+)?send\s+(?:it\s+|the\s+screenshot\s+)?(?:to|in)\s+(?:the\s+chat\s+of\s+)?([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?)'
            r'(?:\s+(?:saying|with\s+message|typing|and\s+type)\s+(.+))?$',
            clean
        )
        if m_search_snap_wa:
            platform = m_search_snap_wa.group(1) or m_search_snap_wa.group(3) or "google"
            query = m_search_snap_wa.group(2).strip()
            person = m_search_snap_wa.group(4).strip().replace(" on whatsapp", "").strip()
            caption = m_search_snap_wa.group(5).strip() if m_search_snap_wa.group(5) else None
            return controller.search_and_send_screenshot(query, platform, person, caption)

        # Workflow 2: File Search (PDF/Doc) & Send on WhatsApp
        # e.g. "go to file explorer search for this pdf and send this to whatsapp to mummi"
        # e.g. "search for cover letter pdf and send to mummi on whatsapp saying here is my resume"
        m_file_wa = re.search(
            r'(?:go\s+to\s+file\s+explorer\s+)?(?:search\s+for|find)\s+(.+?\b(?:pdf|doc|docx|file|zip|png|txt))\s+'
            r'(?:and\s+)?(?:send\s+(?:this\s+|it\s+)?(?:to\s+whatsapp\s+)?(?:to|in)\s+(?:the\s+chat\s+of\s+)?([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?)'
            r'(?:\s+(?:saying|with\s+message|typing)\s+(.+))?$',
            clean
        )
        if m_file_wa:
            file_query = m_file_wa.group(1).strip()
            person = m_file_wa.group(2).strip().replace(" on whatsapp", "").strip()
            caption = m_file_wa.group(3).strip() if m_file_wa.group(3) else None
            return controller.send_file_to_whatsapp(person, file_query, caption)

        # Workflow 3: Copy Text and Paste to Another App
        # e.g. "copy this sentence and go to whatsapp and paste it"
        # e.g. "copy all and go to notepad and paste"
        m_copy_paste = re.search(
            r'copy\s+(?:this\s+)?(?:sentence\s+|all\s+|everything\s+)?(?:and\s+)?(?:go\s+to|switch\s+to)\s+'
            r'([a-zA-Z0-9_\s]+?)\s+(?:and\s+)?paste(?:\s+the\s+copied\s+thing|\s+it)?$',
            clean
        )
        if m_copy_paste:
            target_app = m_copy_paste.group(1).strip()
            select_all = "all" in clean or "everything" in clean
            return controller.copy_and_paste_to(target_app, select_all=select_all)

        # Workflow 4: Screenshot + Send to WhatsApp
        m_snap_wa = re.search(
            r'(?:take|capture)\s+(?:a\s+)?screenshot\s+(?:and\s+)?(?:then\s+)?'
            r'(?:go\s+to\s+whatsapp\s+|open\s+whatsapp\s+)?(?:and\s+)?send\s+(?:it\s+|the\s+screenshot\s+)?'
            r'(?:to|in)\s+(?:the\s+chat\s+of\s+)?([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?'
            r'(?:\s+(?:saying|with\s+message|typing|and\s+type)\s+(.+))?$',
            clean
        )
        if m_snap_wa:
            person = m_snap_wa.group(1).strip().replace(" on whatsapp", "").strip()
            caption = m_snap_wa.group(2).strip() if m_snap_wa.group(2) else None
            return controller.send_screenshot_to_whatsapp(person, caption)

        # Workflow 5: Open WhatsApp + Navigate to Chat + Send
        m_wa_open_send = re.search(
            r'(?:go\s+to\s+whatsapp|open\s+whatsapp)\s+(?:and\s+)?(?:open|go\s+to)\s+(?:the\s+)?chat\s+(?:of|with)\s+'
            r'([a-zA-Z0-9_\s]+?)(?:\s+(?:and\s+send|saying|type|and\s+type|and\s+say)\s+(.+))?$',
            clean
        )
        if m_wa_open_send:
            person = m_wa_open_send.group(1).strip().replace(" on whatsapp", "").strip()
            msg = m_wa_open_send.group(2).strip() if m_wa_open_send.group(2) else None
            if msg and "screenshot" in msg:
                caption = re.sub(r'^(?:this\s+)?screenshot\s*(?:and\s+)?(?:type|say|saying|with\s+message)?\s*', '', msg).strip()
                caption = caption if caption and caption != "screenshot" else None
                return controller.send_screenshot_to_whatsapp(person, caption)
            return controller.open_whatsapp_chat(person, msg)

        # Workflow 6: Gmail End-to-End Compose & Send
        # e.g. "open the mail of this gmail and then click compose and then write this message and then send to this mail"
        m_gmail_full = re.search(
            r'open\s+(?:the\s+mail\s+of\s+)?(?:this\s+)?gmail\s+(?:and\s+)?(?:then\s+)?(?:click\s+)?compose\s+'
            r'(?:and\s+)?(?:then\s+)?(?:write\s+(.+?)\s+)?(?:and\s+)?(?:then\s+)?send\s+(?:to|to\s+this\s+mail)\s+([^\s]+)$',
            clean
        )
        if m_gmail_full:
            body = m_gmail_full.group(1).strip() if m_gmail_full.group(1) else None
            recipient = m_gmail_full.group(2).strip()
            return controller.send_gmail_complete(recipient, body=body)

        # Workflow 7: Git Clone & Open Code in IDE
        # e.g. "clone this repo to my antigravity and then open the code"
        m_clone_open = re.search(
            r'clone\s+(?:this\s+)?(?:repo\s+|repository\s+)?([a-zA-Z0-9_\-\.:/]+)?'
            r'(?:\s+to\s+(?:my\s+)?([a-zA-Z0-9_\s]+?))?(?:\s+(?:and\s+)?(?:then\s+)?open\s+(?:the\s+)?code)?$',
            clean
        )
        if m_clone_open and any(w in clean for w in ["antigravity", "vs", "code", "terminal", "ide"]):
            repo = m_clone_open.group(1).strip() if m_clone_open.group(1) else "agent-desktop"
            if repo in ["this", "repo", "repository"]:
                repo = "agent-desktop"
            ide = m_clone_open.group(2).strip() if m_clone_open.group(2) else "antigravity"
            return controller.clone_and_open_repo(repo, ide=ide)

        # -------------------------------------------------------------
        # 2. SEQUENTIAL MULTI-STEP CHAINING ("and then", "then", "after that")
        #    ONLY split if no WhatsApp/messaging pattern already matched above
        #    and the sentence doesn't look like a single WhatsApp send command
        # -------------------------------------------------------------
        _is_wa_send = any(kw in clean for kw in [
            "send", "message", "text", "chat of", "chat with", "whatsapp"
        ])
        split_pattern = r'\s+(?:and\s+then|then|after\s+that)\s+'
        if re.search(split_pattern, clean) and not _is_wa_send:
            sub_steps = re.split(split_pattern, clean)
            if len(sub_steps) > 1:
                return self._execute_chain(sub_steps, controller)

        # -------------------------------------------------------------
        # 3. SINGLE STEP EXECUTION
        # -------------------------------------------------------------
        return self._execute_single_step(clean, controller)

    def _execute_chain(self, steps: list[str], controller) -> str:
        """Executes a series of sequential sub-commands in order."""
        results = []
        for i, step in enumerate(steps):
            step_clean = step.strip().lstrip(",.!? ").strip()
            if not step_clean:
                continue

            for p in ["jarvis", "and", "also"]:
                if step_clean.startswith(p + " "):
                    step_clean = step_clean[len(p) + 1:].strip()

            res = self._execute_single_step(step_clean, controller)
            results.append(res)
            time.sleep(0.5)

        return " | ".join(results)

    def _execute_single_step(self, clean: str, controller) -> str:
        """Processes an individual action."""

        # -------------------------------------------------------------
        # A. WHATSAPP CHAT & SENDING MESSAGES
        # Broad natural-language patterns: "send X to Y", "message Y saying X",
        # "open whatsapp chat of Y and say X", "whatsapp Y: X" etc.
        # Order: most-specific first to avoid false matches.
        # -------------------------------------------------------------

        # Pattern A1: "send hello in the chat of mummi" (most specific — has 'chat of')
        m_send_chat_of = re.search(
            r'^send\s+(.+?)\s+in\s+(?:the\s+)?chat\s+(?:of|with)\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?$', clean
        )
        if m_send_chat_of:
            msg = m_send_chat_of.group(1).strip()
            person = m_send_chat_of.group(2).strip()
            if "screenshot" in msg:
                return controller.send_screenshot_to_whatsapp(person, None)
            return controller.open_whatsapp_chat(person, msg)

        # Pattern A2: "send hello to/in chat of mummi" (with explicit 'chat of')
        m_send1 = re.search(r'send\s+(.+?)\s+(?:in|to)\s+(?:the\s+)?chat\s+of\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?$', clean)
        if m_send1:
            msg = m_send1.group(1).strip()
            person = m_send1.group(2).strip().replace(" on whatsapp", "").strip()
            if "screenshot" in msg:
                caption = re.sub(r'^(?:this\s+)?screenshot\s*(?:and\s+)?(?:type|say|saying|with\s+message)?\s*', '', msg).strip()
                caption = caption if caption and caption != "screenshot" else None
                return controller.send_screenshot_to_whatsapp(person, caption)
            return controller.open_whatsapp_chat(person, msg)

        # Pattern A3: "in/to the chat of mummi send hello" (reversed order)
        m_send1b = re.search(r'(?:in|to)\s+(?:the\s+)?chat\s+of\s+([a-zA-Z0-9_\s]+?)\s+send\s+(.+)$', clean)
        if m_send1b:
            person = m_send1b.group(1).strip().replace(" on whatsapp", "").strip()
            msg = m_send1b.group(2).strip()
            if "screenshot" in msg:
                caption = re.sub(r'^(?:this\s+)?screenshot\s*(?:and\s+)?(?:type|say|saying|with\s+message)?\s*', '', msg).strip()
                caption = caption if caption and caption != "screenshot" else None
                return controller.send_screenshot_to_whatsapp(person, caption)
            return controller.open_whatsapp_chat(person, msg)

        # Pattern A4: "send hello to mummi" / "send hello to mummy on whatsapp"
        m_simple_send = re.search(
            r'^send\s+(.+?)\s+to\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?$', clean
        )
        if m_simple_send:
            msg = m_simple_send.group(1).strip()
            person = m_simple_send.group(2).strip().replace("on whatsapp", "").strip()
            if person and person not in ["screen", "browser", "desktop", "all", "this", "me"]:
                if "screenshot" in msg:
                    return controller.send_screenshot_to_whatsapp(person, None)
                return controller.open_whatsapp_chat(person, msg)

        # Pattern A5: "message mummi saying hello" / "text mummi: hello"
        m_message_saying = re.search(
            r'^(?:message|text|msg)\s+([a-zA-Z0-9_\s]+?)\s+(?:saying|and\s+say|say|with\s+message|:)?\s*(.+)$', clean
        )
        if m_message_saying:
            person = m_message_saying.group(1).strip()
            msg = m_message_saying.group(2).strip()
            if person and msg and person not in ["him", "her", "them", "it"]:
                return controller.open_whatsapp_chat(person, msg)

        m_open_chat = re.search(r'(?:open\s+)?(?:whatsapp\s+)?chat\s+(?:of|with)\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?(?:\s+(?:and\s+send|saying|and\s+say)\s+(.+))?$', clean)
        if m_open_chat:
            person = m_open_chat.group(1).strip()
            msg = m_open_chat.group(2).strip() if m_open_chat.group(2) else None
            if person and person not in ["chat", "whatsapp", "the app"]:
                return controller.open_whatsapp_chat(person, msg)

        m_msg = re.search(r'(?:message|text)\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?\s+(?:saying|and\s+say|with)\s+(.+)$', clean)
        if m_msg:
            person = m_msg.group(1).strip()
            msg = m_msg.group(2).strip()
            return controller.open_whatsapp_chat(person, msg)

        m_send_snap = re.search(r'send\s+(?:this\s+)?screenshot\s+(?:to|in)\s+(?:the\s+chat\s+of\s+)?([a-zA-Z0-9_\s]+?)(?:\s+saying\s+(.+))?$', clean)
        if m_send_snap:
            person = m_send_snap.group(1).strip()
            caption = m_send_snap.group(2).strip() if m_send_snap.group(2) else None
            return controller.send_screenshot_to_whatsapp(person, caption)

        if clean in ["open whatsapp", "launch whatsapp", "whatsapp"]:
            return controller.launch_app("whatsapp")

        # -------------------------------------------------------------
        # B. CLIPBOARD OPERATIONS (COPY / PASTE)
        # -------------------------------------------------------------
        if clean in ["copy", "copy this", "copy selection", "copy this sentence"]:
            return controller.copy_selection()

        if clean in ["copy all", "copy everything", "select all and copy"]:
            return controller.copy_all()

        if clean in ["paste", "paste this", "paste it", "paste the copied thing"]:
            return controller.paste()

        # -------------------------------------------------------------
        # C. DOWNLOADS & INSTALLATION
        # -------------------------------------------------------------
        if any(w in clean for w in ["download this", "click download", "start download"]):
            return controller.click_download()

        if any(w in clean for w in ["install this", "install", "installl", "run installer", "execute installer"]):
            return controller.install_latest_download()

        # -------------------------------------------------------------
        # D. APPLICATION LIFECYCLE (CLOSE / EXIT)
        # -------------------------------------------------------------
        if any(p in clean for p in ["close all", "close everything", "terminate all apps", "exit all apps", "close all windows"]):
            return controller.close_all_apps()

        if clean.startswith("close ") or clean.startswith("exit ") or clean.startswith("quit "):
            target = clean.split(maxsplit=1)[-1].strip()
            if target and target not in ["all", "everything"]:
                return controller.close_app(target)

        # -------------------------------------------------------------
        # E. ANTIGRAVITY IDE EXPLICIT FOCUS & LAUNCH
        # -------------------------------------------------------------
        if "antigravity" in clean:
            if any(w in clean for w in ["close", "exit", "quit", "kill"]):
                return controller.close_app("antigravity")
            return controller.focus_or_launch_antigravity()

        # -------------------------------------------------------------
        # F. DIRECT UI INTERACTIONS (CLICK, TYPE, PRESS KEYS)
        # -------------------------------------------------------------
        if clean in ["send", "press send", "hit send"]:
            return controller.press_key("enter")

        m_press = re.search(r'^(?:press|hit)\s+(enter|return|escape|esc|tab|space|backspace|delete)$', clean)
        if m_press:
            return controller.press_key(m_press.group(1))

        # Typing with explicit destination: "write <content> to/into <target> (and send)?"
        m_type_target = re.search(r'^(?:type|write|enter|input)\s+(.+?)\s+(?:to|in|into)\s+([a-zA-Z0-9_\s]+?)(?:\s+(?:and\s+)?(?:send|press\s+enter))?$', clean)
        if m_type_target:
            content = m_type_target.group(1).strip()
            target_dest = m_type_target.group(2).strip()
            send_now = any(w in clean for w in ["and send", "then send", "press enter"])
            if content in ["this prompt", "the prompt", "prompt", "this"]:
                import pyperclip
                content = pyperclip.paste().strip()
            return controller.type_text(content, target=target_dest, press_enter=send_now)

        # Direct typing into current focus
        m_type = re.search(r'^(?:type|write|enter|input)\s+(?:this\s+)?(?:prompt\s+)?(.+?)(?:\s+(?:and\s+)?(?:send|press\s+enter))?$', clean)
        if m_type:
            content = m_type.group(1).strip()
            send_now = any(w in clean for w in ["and send", "then send", "press enter"])
            return controller.type_text(content, press_enter=send_now)

        if clean.startswith("click ") or clean.startswith("tap "):
            target_elem = re.sub(r'^(?:click|tap)(?:\s+on)?(?:\s+the)?\s+', '', clean).strip()
            return controller.click_element(target_elem)

        # -------------------------------------------------------------
        # G. GIT CLONE & GITHUB MANAGEMENT
        # -------------------------------------------------------------
        m_clone = re.search(r'(?:git\s+)?clone\s+(?:this\s+)?(?:repo|repository\s+)?([a-zA-Z0-9_\-\.:/]+)(?:\s+to\s+(.+))?$', clean)
        if m_clone:
            target_repo = m_clone.group(1).strip()
            dest = m_clone.group(2).strip() if m_clone.group(2) else r"C:\Users\anand\AI_AGENT"
            if target_repo in ["this", "repo", "repository"]:
                target_repo = "agent-desktop"
            return controller.clone_repo(target_repo, dest)

        if "github" in clean or "repo" in clean:
            if any(p in clean for p in ["my github", "my profile", "my account"]):
                webbrowser.open(f"https://github.com/{self.github_user}")
                return f"Opening your GitHub profile ({self.github_user}), sir."

            match_repo = re.search(r'(?:open|show|go to)\s+(?:my\s+)?(?:repo|repository)\s+([a-zA-Z0-9_\-]+)', clean)
            if match_repo:
                repo_name = match_repo.group(1).strip()
                webbrowser.open(f"https://github.com/{self.github_user}/{repo_name}")
                return f"Opening repository '{repo_name}' on your GitHub, sir."

            if "this repo" in clean:
                webbrowser.open(f"https://github.com/{self.github_user}/agent-desktop")
                return f"Opening current repository agent-desktop on GitHub, sir."

            webbrowser.open("https://github.com")
            return "Opening GitHub, sir."

        # -------------------------------------------------------------
        # H. SCOPED PLATFORM SEARCH (ONLY SEARCH IN THAT PLATFORM)
        # -------------------------------------------------------------
        scoped_result = self._handle_scoped_search(clean)
        if scoped_result:
            return scoped_result

        # -------------------------------------------------------------
        # I. POPULAR WEB SERVICES & URLS
        # -------------------------------------------------------------
        web_services = {
            "chatgpt": "https://chatgpt.com",
            "chat gpt": "https://chatgpt.com",
            "claude": "https://claude.ai",
            "gemini": "https://gemini.google.com",
            "youtube": "https://youtube.com",
            "gmail": "https://mail.google.com",
            "google drive": "https://drive.google.com",
            "drive": "https://drive.google.com",
            "twitter": "https://x.com",
            "reddit": "https://reddit.com",
            "linkedin": "https://linkedin.com",
            "netflix": "https://netflix.com",
            "spotify": "https://open.spotify.com",
        }
        for name, url in web_services.items():
            if f"open {name}" in clean or f"go to {name}" in clean or clean == name:
                webbrowser.open(url)
                return f"Opening {name.title()} in your browser, sir."

        m_goto_url = re.search(r'^(?:go\s+to|open)\s+(?:website\s+|site\s+)?([a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)$', clean)
        if m_goto_url:
            return controller.open_url(m_goto_url.group(1))

        # -------------------------------------------------------------
        # J. CHROME / GOOGLE SEARCH & PROFILE ROUTING
        # -------------------------------------------------------------
        m_chrome_search = re.search(r'(?:open\s+chrome|launch\s+chrome)\s+(?:and\s+)?(?:search\s+(?:for\s+)?(.+)|go\s+to\s+(.+)|as\s+([a-zA-Z0-9]+))', clean)
        if m_chrome_search:
            search_query = m_chrome_search.group(1)
            goto_url = m_chrome_search.group(2)
            profile = m_chrome_search.group(3) or ("anand" if "anand" in clean else "somil")
            if search_query:
                url = f"https://www.google.com/search?q={urllib.parse.quote(search_query.strip())}"
                return controller.launch_chrome(profile=profile, url=url)
            elif goto_url:
                url = goto_url.strip()
                if not url.startswith("http"):
                    url = f"https://{url}"
                return controller.launch_chrome(profile=profile, url=url)
            return controller.launch_chrome(profile=profile)

        search_match = re.search(r'^(?:search|google|look up|find)\s+(?:for\s+)?(.+?)(?:\s+on\s+(?:chrome|google|the web))?$', clean)
        if search_match:
            query = search_match.group(1).strip()
            if not any(a in query for a in ["folder", "file", "app", "pdf", "doc"]):
                return controller.search_web(query)

        if "open chrome" in clean or "launch chrome" in clean or clean in ["chrome", "google chrome"]:
            profile = "anand" if "anand" in clean else "somil"
            return controller.launch_chrome(profile=profile)

        # -------------------------------------------------------------
        # K. LOCAL FOLDERS & DRIVES
        # -------------------------------------------------------------
        user_dirs = {
            "downloads": os.path.expanduser("~/Downloads"),
            "documents": os.path.expanduser("~/Documents"),
            "desktop": os.path.expanduser("~/Desktop"),
            "pictures": os.path.expanduser("~/Pictures"),
            "videos": os.path.expanduser("~/Videos"),
            "music": os.path.expanduser("~/Music"),
            "c drive": "C:\\",
            "root": "C:\\",
            "workspace": "C:\\Users\\anand\\AI_AGENT",
        }
        for dir_name, path in user_dirs.items():
            if f"open {dir_name}" in clean or f"show {dir_name}" in clean:
                import subprocess
                subprocess.Popen(f'explorer "{path}"', shell=True)
                return f"Opening your {dir_name} folder, sir."

        # -------------------------------------------------------------
        # L. HARDWARE, VOLUME & WINDOW CONTROLS
        # -------------------------------------------------------------
        if any(w in clean for w in ["status", "diagnostics", "battery", "cpu", "how are you"]):
            return controller.get_spoken_status()

        if any(w in clean for w in ["minimize all", "show desktop", "minimize windows", "hide everything"]):
            return controller.minimize_all()

        if any(w in clean for w in ["volume up", "louder", "turn up"]):
            return controller.volume_up(5)

        if any(w in clean for w in ["volume down", "quieter", "turn down"]):
            return controller.volume_down(5)

        if any(w in clean for w in ["mute", "unmute"]):
            return controller.toggle_mute()

        if any(w in clean for w in ["screenshot", "capture screen", "snapshot screen"]):
            return controller.take_screenshot()

        if any(w in clean for w in ["lock workstation", "lock computer", "lock pc", "lock laptop"]):
            return controller.lock_workstation()

        # -------------------------------------------------------------
        # M. GENERIC OPEN / LAUNCH / SWITCH
        # -------------------------------------------------------------
        if clean.startswith("open ") or clean.startswith("launch "):
            target = clean.replace("open ", "").replace("launch ", "").strip()
            return controller.launch_app(target)

        if clean.startswith("switch to ") or clean.startswith("bring up "):
            target = clean.replace("switch to ", "").replace("bring up ", "").strip()
            return controller.focus_window_by_name(target)

        # -------------------------------------------------------------
        # N. UNIVERSAL FALLBACK: LOCAL LLM REASONING & APP RESOLUTION
        # -------------------------------------------------------------
        if controller:
            app_result = controller.launch_app(clean)
            if "could not find or recognize" not in app_result.lower():
                return app_result

        if self.llm_brain:
            return self.llm_brain.interpret_and_execute(clean, controller, self.general_assistant, self.code_agent, self.visual_computer)

        if self.general_assistant:
            return self.general_assistant.respond(clean)

        return f"I have processed your request: '{clean}', sir."

    def _get_local_ip_direct(self) -> str:
        try:
            import socket
            hostname = socket.gethostname()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            active_ip = s.getsockname()[0]
            s.close()
            return f"Your local IP address is {active_ip}, sir."
        except Exception:
            return "Your network adapter is active, sir."

    def _handle_scoped_search(self, clean: str) -> str:
        """Searches specifically inside the requested platform only."""
        platforms = {
            "youtube": ("https://www.youtube.com/results?search_query={}", "YouTube"),
            "github": ("https://github.com/search?q={}", "GitHub"),
            "chatgpt": ("https://chatgpt.com/?q={}", "ChatGPT"),
            "chat gpt": ("https://chatgpt.com/?q={}", "ChatGPT"),
            "wikipedia": ("https://en.wikipedia.org/wiki/Special:Search?search={}", "Wikipedia"),
            "amazon": ("https://www.amazon.com/s?k={}", "Amazon"),
            "reddit": ("https://www.reddit.com/search/?q={}", "Reddit"),
            "twitter": ("https://x.com/search?q={}", "Twitter / X"),
            "google": ("https://www.google.com/search?q={}", "Google"),
            "chrome": ("https://www.google.com/search?q={}", "Google Chrome"),
        }
        for p_name, (url_tmpl, disp_name) in platforms.items():
            m1 = re.search(rf'(?:search|look\s+up|find|play)\s+(.+?)\s+on\s+{p_name}$', clean)
            m2 = re.search(rf'(?:search|look\s+up|find|play)\s+{p_name}\s+for\s+(.+)$', clean)
            m3 = re.search(rf'(?:search|look\s+up|find|play)\s+on\s+{p_name}\s+(.+)$', clean)

            m = m1 or m2 or m3
            if m:
                query = m.group(1).strip()
                if query:
                    encoded = urllib.parse.quote(query)
                    webbrowser.open(url_tmpl.format(encoded))
                    return f"Searching {disp_name} for '{query}', sir."

        return None

    def _coordinate_multi_agent(self, raw: str, controller) -> str:
        """
        Coordinates complex cross-domain instructions involving multiple agents:
        e.g. Inspect project and send summary to WhatsApp, or research + code generation.
        """
        clean = raw.lower()
        if "inspect" in clean and any(w in clean for w in ["send", "whatsapp", "message"]):
            report = self.code_agent.inspect_and_diagnose(self.code_agent.workspace_root)
            m_wa = re.search(r'(?:to|in)\s+(?:the\s+chat\s+of\s+)?([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?', clean)
            recipient = m_wa.group(1).strip() if m_wa else "mummi"
            summary_preview = report.split("\n\n")[0]
            return controller.send_whatsapp_message(recipient, f"JARVIS Project Inspection Report:\n{summary_preview}")
        
        # Default delegate to code agent or general assistant
        if self.code_agent and any(w in clean for w in ["code", "python", "script", "project", "build"]):
            return self.code_agent.process(raw)
        elif self.general_assistant:
            return self.general_assistant.respond(raw)
        return "Multi-agent coordination completed."


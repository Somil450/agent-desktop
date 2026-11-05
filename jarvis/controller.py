"""
JARVIS System Controller Module
Executes OS actions, window management, media/volume controls,
universal app launching, application closing, WhatsApp chat & file automation,
clipboard copy/paste chaining, downloads & installer execution, Gmail automation,
git repository cloning, and UI accessibility actions.
"""

import os
import io
import re
import socket
import datetime
import json
import time
import struct
import subprocess
import webbrowser
import urllib.parse
import ctypes
import psutil
import pyautogui
import pyperclip
from PIL import Image
import win32clipboard
import win32con

# Disable PyAutoGUI failsafe to avoid mouse-corner crash
pyautogui.FAILSAFE = False

# Ensure calling thread is attached to the interactive desktop
def ensure_default_desktop():
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopA(b"default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

ensure_default_desktop()

# Virtual key constants for media/volume
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3

# Common phonetic aliases for Indian & international speech names
# Each key maps to ordered list of search candidates to try in WhatsApp
CONTACT_ALIASES = {
    "mummi":  ["Badii Mummy", "mummy", "mummi", "maa", "mom", "mother"],
    "mummy":  ["Badii Mummy", "mummy", "mummi", "maa", "mom", "mother"],
    "maa":    ["Badii Mummy", "maa", "mummy", "mummi", "mom"],
    "mom":    ["mom", "mummy", "mummi", "maa", "Badii Mummy"],
    "mother": ["Badii Mummy", "mummy", "mother"],
    "papa":   ["papa", "dad", "father", "pop"],
    "dad":    ["dad", "papa", "father"],
    "bhai":   ["bhai", "brother", "bro"],
    "didi":   ["didi", "sister", "di"],
}

class SystemController:
    def __init__(self):
        ensure_default_desktop()
        self._installed_apps = []
        self._load_installed_apps()

    def _load_installed_apps(self):
        """Loads all installed Windows applications via Get-StartApps."""
        try:
            cmd = ['powershell', '-NoProfile', '-Command', 'Get-StartApps | ConvertTo-Json']
            out = subprocess.check_output(cmd, text=True, timeout=8)
            apps = json.loads(out)
            if isinstance(apps, list):
                self._installed_apps = apps
            elif isinstance(apps, dict):
                self._installed_apps = [apps]
        except Exception:
            self._installed_apps = []

    def run_agent_desktop(self, args: list) -> dict:
        """Executes agent-desktop with given arguments and returns parsed JSON."""
        cmd = ["agent-desktop"] + args
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                shell=True
            )
            stdout = res.stdout.strip()
            if stdout:
                lines = stdout.splitlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            return json.loads(line)
                        except json.JSONDecodeError:
                            continue
            return {"ok": False, "raw_stdout": stdout, "raw_stderr": res.stderr}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # -------------------------------------------------------------
    # 1. WINDOW & APPLICATION MANAGEMENT
    # -------------------------------------------------------------
    def list_windows(self) -> list:
        """Returns list of open windows from agent-desktop."""
        res = self.run_agent_desktop(["list-windows"])
        if res.get("ok"):
            return res.get("data", [])
        return []

    def focus_window_by_id(self, target_id: str) -> bool:
        """Brings a window to front using Win32 APIs and agent-desktop."""
        ensure_default_desktop()
        if not target_id:
            return False
        try:
            hwnd_str = target_id.replace("w-", "")
            hwnd = int(hwnd_str)
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SwitchToThisWindow(hwnd, True)
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

        res = self.run_agent_desktop(["focus-window", "--window-id", target_id])
        return res.get("ok", False)

    def focus_window_by_name(self, name: str) -> str:
        """Brings a window with matching title or app to front."""
        windows = self.list_windows()
        target_id = None
        target_title = None
        for w in windows:
            title = w.get("title", "").lower()
            app = w.get("app_name", "").lower()
            if name.lower() in title or name.lower() in app:
                target_id = w.get("id")
                target_title = w.get("title")
                break

        if target_id:
            self.focus_window_by_id(target_id)
            return f"Switched to {target_title}, sir."
        return f"Could not find an active window matching '{name}'."

    def focus_or_launch_antigravity(self) -> str:
        """Focuses Antigravity IDE if already running, or launches it."""
        windows = self.list_windows()
        for w in windows:
            title = w.get("title", "").lower()
            app = w.get("app_name", "").lower()
            if "antigravity" in title or "antigravity" in app:
                target_id = w.get("id")
                self.focus_window_by_id(target_id)
                return "Switched to Antigravity IDE, sir."

        try:
            subprocess.Popen('explorer.exe "shell:AppsFolder\\Google.AntigravityIDE"', shell=True)
            return "Opening Antigravity IDE, sir."
        except Exception as e:
            return f"Could not launch Antigravity IDE: {e}"

    def launch_chrome(self, profile: str = "somil", url: str = None) -> str:
        """
        Launches Google Chrome directly into the user's profile, bypassing
        the multi-profile 'Who's using Chrome?' selection screen.
        """
        profile_map = {
            "somil": "Profile 2",
            "anand": "Profile 3",
            "default": "Profile 2",
            "person 1": "Default",
            "riya": "Profile 12",
            "vit": "Profile 17",
        }
        prof_dir = profile_map.get(profile.lower(), "Profile 2")

        cmd = ["cmd.exe", "/c", "start", "chrome", f"--profile-directory={prof_dir}"]
        if url:
            cmd.append(url)

        try:
            subprocess.Popen(cmd, shell=True)
            time.sleep(0.4)
            self._dismiss_chrome_profile_picker_if_open(profile)
            if url:
                return f"Opening Chrome ({profile.title()} profile) to {url}, sir."
            return f"Opening Google Chrome ({profile.title()} profile), sir."
        except Exception as e:
            return f"Could not launch Chrome: {e}"

    def _dismiss_chrome_profile_picker_if_open(self, preferred_profile: str = "somil"):
        """If the Chrome profile picker window is open, automatically click the user's profile card."""
        try:
            windows = self.list_windows()
            picker_win = None
            for w in windows:
                if "chrome" in w.get("app_name", "").lower() and w.get("title") == "Google Chrome":
                    bounds = w.get("bounds", {})
                    if bounds.get("width", 0) < 1600:
                        picker_win = w
                        break
            if picker_win:
                win_id = picker_win.get("id")
                out = subprocess.check_output(f'agent-desktop snapshot --window-id {win_id} -i', shell=True, text=True, timeout=3)
                data = json.loads(out)
                target_ref = None
                def find_profile(node):
                    nonlocal target_ref
                    if target_ref:
                        return
                    name = node.get("name", "").lower()
                    if preferred_profile.lower() in name and "profile" in name:
                        target_ref = node.get("ref_id")
                        return
                    for c in node.get("children", []):
                        find_profile(c)
                find_profile(data.get("data", {}).get("tree", {}))
                if target_ref:
                    subprocess.run(f'agent-desktop click "{target_ref}"', shell=True, timeout=3)
        except Exception:
            pass

    def launch_app(self, app_name: str) -> str:
        """Launches an application by name or common alias, searching all installed Windows apps."""
        clean_name = app_name.lower().strip()

        # Normalize Antigravity
        if "antigravity" in clean_name or "anti gravity" in clean_name:
            return self.focus_or_launch_antigravity()

        # Chrome with direct profile resolution (bypasses profile picker)
        if clean_name in ["chrome", "google chrome", "browser"]:
            return self.launch_chrome(profile="somil")

        # 1. Common direct protocol aliases
        app_map = {
            "chrome": "start chrome",
            "browser": "start chrome",
            "google chrome": "start chrome",
            "notepad": "notepad",
            "calculator": "calc",
            "calc": "calc",
            "explorer": "explorer",
            "files": "explorer",
            "file explorer": "explorer",
            "settings": "start ms-settings:",
            "paint": "mspaint",
            "cmd": "start cmd",
            "terminal": "start wt",
            "task manager": "taskmgr",
            "whatsapp": "start whatsapp:",
            "spotify": "start spotify:",
            "discord": "start discord:",
            "code": "code",
            "vs code": "code",
            "vscode": "code",
            "edge": "start msedge",
            "teams": "start ms-teams:",
        }
        if clean_name in app_map:
            try:
                subprocess.Popen(app_map[clean_name], shell=True)
                return f"Opening {app_name} now, sir."
            except Exception as e:
                return f"Could not launch {app_name}: {e}"

        # 2. Universal Windows App search (Get-StartApps)
        best_match = None
        for a in self._installed_apps:
            name = a.get("Name", "").lower()
            if clean_name == name:
                best_match = a
                break
            elif clean_name in name:
                best_match = a

        if best_match:
            app_id = best_match.get("AppID")
            found_name = best_match.get("Name")
            try:
                subprocess.Popen(f'explorer.exe "shell:AppsFolder\\{app_id}"', shell=True)
                return f"Opening {found_name}, sir."
            except Exception:
                pass

        # 3. Fallback only if single executable name AND clearly not a natural-language phrase
        if (
            len(clean_name.split()) == 1
            and not any(v in clean_name for v in ["send", "chat", "click", "search", "message", "text", "type"])
            and clean_name.isidentifier()  # only valid identifier-style names
        ):
            try:
                subprocess.Popen(f"start {clean_name}", shell=True)
                return f"Opening {app_name}, sir."
            except Exception:
                pass

        return f"Could not find or recognize application '{app_name}', sir."

    def close_app(self, app_name: str) -> str:
        """Closes a specific application or active window."""
        clean = app_name.lower().strip()

        # Close active/current window
        if clean in ["this", "current", "this window", "active window", "window"]:
            pyautogui.hotkey('alt', 'f4')
            return "Closed active window, sir."

        alias_kills = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "whatsapp": "WhatsApp.Root.exe",
            "notepad": "notepad.exe",
            "calculator": "CalculatorApp.exe",
            "calc": "CalculatorApp.exe",
            "settings": "SystemSettings.exe",
            "spotify": "Spotify.exe",
            "antigravity": "Antigravity IDE.exe",
            "antigravity ide": "Antigravity IDE.exe",
            "anti gravity": "Antigravity IDE.exe",
            "edge": "msedge.exe",
            "teams": "ms-teams.exe",
        }

        # 1. Search live windows
        windows = self.list_windows()
        closed_any = False
        for w in windows:
            title = w.get("title", "").lower()
            proc = w.get("app_name", "").lower()
            pid = w.get("pid")
            if clean in title or clean in proc:
                subprocess.run(f"taskkill /PID {pid}", shell=True, capture_output=True)
                closed_any = True

        if closed_any:
            return f"Closed {app_name}, sir."

        # 2. Check alias map
        if clean in alias_kills:
            proc_exe = alias_kills[clean]
            res = subprocess.run(f"taskkill /IM {proc_exe}", shell=True, capture_output=True)
            if res.returncode == 0:
                return f"Closed {app_name}, sir."

        # 3. Generic taskkill
        res = subprocess.run(f"taskkill /IM {clean}.exe", shell=True, capture_output=True)
        if res.returncode == 0:
            return f"Closed {app_name}, sir."

        return f"Could not find an active window for '{app_name}' to close."

    def close_all_apps(self, preserve_ide: bool = True) -> str:
        """Closes all open user application windows, preserving Antigravity IDE and Windows shell."""
        windows = self.list_windows()
        closed_count = 0
        for w in windows:
            proc = w.get("app_name", "").lower()
            title = w.get("title", "").lower()
            pid = w.get("pid")

            if "explorer.exe" in proc or "shellexperiencehost" in proc:
                continue
            if preserve_ide and ("antigravity" in proc or "antigravity" in title):
                continue
            if pid:
                subprocess.run(f"taskkill /PID {pid}", shell=True, capture_output=True)
                closed_count += 1

        return f"Closed {closed_count} applications, sir. Workspace cleared."

    def minimize_all(self) -> str:
        """Minimizes all windows to show the desktop."""
        try:
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # LWin
            ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)  # 'D'
            ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
            return "Displaying desktop, sir."
        except Exception as e:
            return f"Failed to minimize windows: {e}"

    # -------------------------------------------------------------
    # 2. CLIPBOARD & TEXT SELECTION (COPY / PASTE)
    # -------------------------------------------------------------
    def copy_selection(self) -> str:
        """Copies currently selected text to Windows clipboard."""
        ensure_default_desktop()
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        text = pyperclip.paste().strip()
        preview = text[:35] + "..." if len(text) > 35 else text
        return f"Copied '{preview}' to clipboard, sir." if text else "Copied selection, sir."

    def copy_all(self) -> str:
        """Selects all content and copies it to clipboard."""
        ensure_default_desktop()
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        text = pyperclip.paste().strip()
        return f"Copied all text ({len(text)} characters), sir."

    def paste(self) -> str:
        """Pastes current clipboard contents at cursor."""
        ensure_default_desktop()
        pyautogui.hotkey('ctrl', 'v')
        return "Pasted from clipboard, sir."

    def copy_and_paste_to(self, target_app: str, select_all: bool = False) -> str:
        """Copies content from active focus, switches to target app, and pastes."""
        ensure_default_desktop()
        if select_all:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)

        # Switch to target window
        self.focus_window_by_name(target_app)
        time.sleep(0.6)

        # Paste
        pyautogui.hotkey('ctrl', 'v')
        return f"Copied content and pasted into {target_app}, sir."

    # -------------------------------------------------------------
    # 3. FILE SYSTEM SEARCH & WHATSAPP FILE SHARING
    # -------------------------------------------------------------
    def copy_file_to_clipboard(self, filepath: str) -> bool:
        """Copies a physical file to Windows clipboard as CF_HDROP drop file list."""
        ensure_default_desktop()
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            return False
        try:
            offset = 20  # DROPFILES struct offset
            dropfiles_header = struct.pack('IIIIb3x', offset, 0, 0, 0, 1)
            file_bytes = filepath.encode('utf-16le') + b'\x00\x00\x00\x00'
            data = dropfiles_header + file_bytes

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            print(f"[File Clipboard Error] {e}")
            return False

    def find_file(self, query: str, roots: list = None) -> str:
        """Searches Downloads, Documents, Desktop, and workspace for a matching file."""
        if roots is None:
            roots = [
                os.path.expanduser('~/Downloads'),
                os.path.expanduser('~/Documents'),
                os.path.expanduser('~/Desktop'),
                r'C:\Users\anand\AI_AGENT'
            ]
        query_clean = query.lower().strip()
        words = query_clean.split()
        matches = []
        for root in roots:
            if not os.path.exists(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['node_modules', 'target', '__pycache__', 'AppData']]
                for f in filenames:
                    f_lower = f.lower()
                    if all(w in f_lower for w in words):
                        full_p = os.path.join(dirpath, f)
                        matches.append((os.path.getmtime(full_p), full_p))

        if matches:
            matches.sort(reverse=True)
            return matches[0][1]
        return ""

    def send_file_to_whatsapp(self, contact_name: str, file_query: str, caption: str = None) -> str:
        """Finds matching file (e.g. PDF), copies as CF_HDROP, and sends in WhatsApp chat."""
        ensure_default_desktop()
        filepath = self.find_file(file_query)
        if not filepath:
            return f"Could not find any file matching '{file_query}' in your documents or downloads, sir."

        # Put file on clipboard
        copied = self.copy_file_to_clipboard(filepath)
        if not copied:
            return f"Failed to load file '{os.path.basename(filepath)}' to clipboard."

        # Open chat with contact
        self.open_whatsapp_chat(contact_name, message=None)
        time.sleep(0.6)

        # Paste file attachment
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.3)  # Wait for WhatsApp attachment preview

        # Type caption if provided
        if caption:
            pyperclip.copy(caption)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.4)

        pyautogui.press('enter')
        filename = os.path.basename(filepath)
        return f"Found '{filename}' and sent it to {contact_name} on WhatsApp, sir."

    # -------------------------------------------------------------
    # 4. WHATSAPP CHAT & SCREENSHOT AUTOMATION
    # -------------------------------------------------------------
    def open_whatsapp_chat(self, contact_name: str, message: str = None) -> str:
        """Opens a specific contact chat in WhatsApp Desktop and optionally sends a message."""
        ensure_default_desktop()
        try:
            # 1. Bring WhatsApp to front
            subprocess.Popen("start whatsapp:", shell=True)
            time.sleep(1.2)
            self.focus_window_by_name("WhatsApp")
            time.sleep(0.6)

            pyautogui.press('esc')
            time.sleep(0.3)

            # Determine search candidate terms (including phonetic aliases)
            target = contact_name.strip()
            candidates = [target]
            lower_target = target.lower()

            # Always expand aliases — mummi/mummy → try both + "Badii Mummy" for mummy contact
            if lower_target in CONTACT_ALIASES:
                candidates = CONTACT_ALIASES[lower_target]
            # Also try original name in case alias list doesn't match
            if target not in candidates:
                candidates.append(target)

            # Try candidate searches — open Ctrl+F search bar and type each candidate
            opened = False
            for candidate in candidates:
                # Open search
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.4)

                # Clear any existing text
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.press('delete')
                time.sleep(0.1)

                # Type candidate name slowly so WhatsApp registers it
                pyautogui.write(candidate, interval=0.07)
                time.sleep(1.5)  # Wait for WhatsApp search results to populate

                # Press Down to highlight first result, then Enter to open
                pyautogui.press('down')
                time.sleep(0.4)
                pyautogui.press('enter')
                time.sleep(0.8)

                # Press Escape to dismiss search bar if still open
                pyautogui.press('esc')
                time.sleep(0.3)
                opened = True
                break

            if not opened:
                return f"Could not open WhatsApp chat for {contact_name}, sir."

            # 2. Click on the message input box to ensure focus
            time.sleep(0.5)
            # Send message if provided
            if message:
                # Click the message input area (bottom of WhatsApp)
                pyperclip.copy(message)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.4)
                pyautogui.press('enter')  # Send the message
                time.sleep(0.3)
                return f"Sent '{message}' to {contact_name} on WhatsApp, sir."

            return f"Opened WhatsApp chat with {contact_name}, sir."
        except Exception as e:
            return f"Could not open WhatsApp chat for {contact_name}: {e}"

    def capture_screenshot_to_clipboard(self) -> str:
        """Captures active screen with agent-desktop and places it on Windows clipboard."""
        ensure_default_desktop()
        os.makedirs("screenshots", exist_ok=True)
        filename = os.path.join("screenshots", "clipboard_screen.png")
        res = self.run_agent_desktop(["screenshot", filename])
        if res.get("ok") and os.path.exists(filename):
            try:
                img = Image.open(filename)
                output = io.BytesIO()
                img.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]  # Remove BMP header
                output.close()

                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                return filename
            except Exception as e:
                print(f"[Clipboard Error] {e}")
        return ""

    def send_screenshot_to_whatsapp(self, contact_name: str, caption: str = None) -> str:
        """Captures a screenshot, opens WhatsApp chat with contact, and sends the image with caption."""
        ensure_default_desktop()
        try:
            img_path = self.capture_screenshot_to_clipboard()
            if not img_path:
                return "Failed to capture screenshot to clipboard."

            self.open_whatsapp_chat(contact_name, message=None)
            time.sleep(0.6)

            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1.2)

            if caption:
                pyperclip.copy(caption)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.4)

            pyautogui.press('enter')
            return f"Sent screenshot to {contact_name} on WhatsApp, sir."
        except Exception as e:
            return f"Error sending screenshot to {contact_name}: {e}"

    def search_and_send_screenshot(self, query: str, platform: str, contact_name: str, caption: str = None) -> str:
        """Full multi-step autonomous workflow: Searches a platform, screenshots it, and sends via WhatsApp."""
        plat = platform.lower() if platform else "google"
        if plat == "youtube":
            self.play_youtube(query)
        elif plat == "github":
            self.search_github(query)
        else:
            self.search_web(query)

        time.sleep(3.2)
        actual_caption = caption if caption else f"Here is the search result for {query}"
        return self.send_screenshot_to_whatsapp(contact_name, actual_caption)

    # -------------------------------------------------------------
    # 5. DOWNLOADS & INSTALLATION AUTOMATION
    # -------------------------------------------------------------
    def click_download(self) -> str:
        """Finds any Download or Install link/button on active window and clicks it."""
        return self.click_element("download")

    def install_latest_download(self) -> str:
        """Finds the newest installer in ~/Downloads and launches it."""
        downloads = os.path.expanduser('~/Downloads')
        if not os.path.exists(downloads):
            return "Downloads folder not found, sir."

        candidates = []
        for f in os.listdir(downloads):
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.exe', '.msi']:
                full_p = os.path.join(downloads, f)
                candidates.append((os.path.getmtime(full_p), full_p))

        if not candidates:
            return "No installer (.exe or .msi) found in your Downloads folder, sir."

        candidates.sort(reverse=True)
        latest_file = candidates[0][1]
        filename = os.path.basename(latest_file)
        try:
            subprocess.Popen(f'"{latest_file}"', shell=True)
            return f"Launching installer '{filename}', sir."
        except Exception as e:
            return f"Failed to execute installer '{filename}': {e}"

    # -------------------------------------------------------------
    # 6. DIRECT UI INTERACTIONS (CLICK, TYPE, PRESS KEYS)
    # -------------------------------------------------------------
    def click_element(self, element_text: str) -> str:
        """Finds any UI element matching text in the active window and clicks it."""
        ensure_default_desktop()
        clean = element_text.lower().strip()
        windows = self.list_windows()
        if not windows:
            return "No active window found to click on, sir."

        front_app = windows[0].get("app_name", "explorer.exe")
        snap = self.run_agent_desktop(["snapshot", "--app", front_app, "-i"])
        if snap.get("ok"):
            tree = snap.get("data", {}).get("tree", {})
            matched_ref = self._find_ref_by_name(tree, clean)
            if matched_ref:
                res = self.run_agent_desktop(["click", matched_ref, "--headed"])
                if res.get("ok"):
                    return f"Clicked '{element_text}' on {front_app}, sir."

        # Common application shortcuts
        if "compose" in clean:
            pyautogui.press('c')
            return "Triggered Compose in Gmail, sir."
        elif "download" in clean:
            pyautogui.press('enter')
            return "Triggered download action, sir."
        elif "send" in clean:
            pyautogui.press('enter')
            return "Sent, sir."

        return f"Could not locate '{element_text}' on {front_app}, sir."

    def _find_ref_by_name(self, node: dict, target_name: str) -> str:
        name = str(node.get("name", "")).lower()
        desc = str(node.get("description", "")).lower()
        if (target_name in name or target_name in desc) and "ref_id" in node:
            return node["ref_id"]
        for child in node.get("children", []):
            ref = self._find_ref_by_name(child, target_name)
            if ref:
                return ref
        return None

    def type_text(self, text: str, target: str = None, press_enter: bool = False) -> str:
        """Types text at current focus or inside a target application."""
        ensure_default_desktop()
        if target:
            self.focus_window_by_name(target)
            time.sleep(0.4)

        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        if press_enter:
            pyautogui.press('enter')
            return f"Entered and sent '{text}', sir."
        return f"Typed '{text}', sir."

    def press_key(self, key_name: str) -> str:
        """Presses a keyboard key."""
        ensure_default_desktop()
        clean = key_name.lower().strip()
        key_map = {
            "enter": "enter",
            "return": "enter",
            "escape": "esc",
            "esc": "esc",
            "tab": "tab",
            "backspace": "backspace",
            "space": "space",
            "down": "down",
            "up": "up",
            "left": "left",
            "right": "right",
            "send": "enter",
        }
        actual_key = key_map.get(clean, clean)
        pyautogui.press(actual_key)
        return f"Pressed {actual_key}, sir."

    # -------------------------------------------------------------
    # 7. GMAIL AUTOMATION
    # -------------------------------------------------------------
    def open_gmail_compose(self, recipient: str = None, subject: str = None, body: str = None) -> str:
        """Opens Gmail directly to the compose screen with optional recipient and body."""
        url = "https://mail.google.com/mail/?view=cm&fs=1"
        if recipient:
            url += f"&to={urllib.parse.quote(recipient)}"
        if subject:
            url += f"&su={urllib.parse.quote(subject)}"
        if body:
            url += f"&body={urllib.parse.quote(body)}"
        webbrowser.open(url)
        return f"Opened Gmail compose for {recipient if recipient else 'a new message'}, sir."

    def send_gmail_complete(self, recipient: str, subject: str = None, body: str = None) -> str:
        """Opens Gmail compose, writes message, and sends via Ctrl+Enter shortcut."""
        self.open_gmail_compose(recipient=recipient, subject=subject, body=body)
        time.sleep(3.0)  # Wait for compose window to render
        pyautogui.hotkey('ctrl', 'enter')  # Universal Gmail send shortcut
        return f"Sent email to {recipient} via Gmail, sir."

    # -------------------------------------------------------------
    # 8. GIT REPOSITORIES & IDE CLONING
    # -------------------------------------------------------------
    def clone_repo(self, repo_url_or_name: str, target_folder: str = r"C:\Users\anand\AI_AGENT") -> str:
        """Clones a GitHub repository locally."""
        clean = repo_url_or_name.strip()
        if not clean.startswith("http://") and not clean.startswith("https://") and not clean.startswith("git@"):
            url = f"https://github.com/Somil450/{clean}.git"
            repo_name = clean
        else:
            url = clean
            repo_name = clean.rstrip("/").split("/")[-1].replace(".git", "")

        dest_dir = os.path.join(target_folder, repo_name)
        if os.path.exists(dest_dir):
            return f"Repository '{repo_name}' already exists at {dest_dir}, sir."

        try:
            subprocess.run(["git", "clone", url, dest_dir], check=True, capture_output=True, text=True, timeout=60)
            return f"Successfully cloned repository '{repo_name}' to {dest_dir}, sir."
        except Exception as e:
            return f"Git clone failed: {e}"

    def clone_and_open_repo(self, repo_url_or_name: str, ide: str = "antigravity") -> str:
        """Clones a repo and opens it in Antigravity IDE or VS Code."""
        target_folder = r"C:\Users\anand\AI_AGENT"
        clone_res = self.clone_repo(repo_url_or_name, target_folder)

        repo_name = repo_url_or_name.rstrip("/").split("/")[-1].replace(".git", "")
        dest_dir = os.path.join(target_folder, repo_name)

        if "vs" in ide.lower() or "code" in ide.lower():
            subprocess.Popen(f'code "{dest_dir}"', shell=True)
            return f"{clone_res} Opened in VS Code, sir."
        else:
            self.focus_or_launch_antigravity()
            return f"{clone_res} Switched to Antigravity IDE, sir."

    # -------------------------------------------------------------
    # 9. BROWSER & SEARCH
    # -------------------------------------------------------------
    def open_url(self, url: str) -> str:
        """Opens any URL in default web browser."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        webbrowser.open(url)
        return f"Navigating to {url}, sir."

    def search_web(self, query: str) -> str:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Searching Google for '{query}', sir."

    def search_github(self, query: str) -> str:
        url = f"https://github.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Searching GitHub for '{query}', sir."

    def play_youtube(self, query: str) -> str:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Searching YouTube for '{query}', sir."

    # -------------------------------------------------------------
    # 10. HARDWARE, AUDIO & TELEMETRY
    # -------------------------------------------------------------
    def volume_up(self, steps=5) -> str:
        for _ in range(steps):
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            time.sleep(0.02)
        return "Increasing audio volume, sir."

    def volume_down(self, steps=5) -> str:
        for _ in range(steps):
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
            time.sleep(0.02)
        return "Decreasing audio volume, sir."

    def toggle_mute(self) -> str:
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return "Audio mute toggled, sir."

    def media_play_pause(self) -> str:
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
        return "Media playback toggled, sir."

    def take_screenshot(self, folder="screenshots") -> str:
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, f"capture_{int(time.time())}.png")
        res = self.run_agent_desktop(["screenshot", filename])
        if res.get("ok"):
            return f"Screenshot captured and saved to {filename}, sir."
        return "Screenshot capture failed."

    def lock_workstation(self) -> str:
        ctypes.windll.user32.LockWorkStation()
        return "Locking system workstation now, sir."

    def get_system_diagnostics(self) -> dict:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        battery = psutil.sensors_battery()

        bat_info = "No battery detected (AC Desktop)"
        if battery:
            state = "Charging" if battery.power_plugged else "Discharging"
            bat_info = f"{battery.percent}% ({state})"

        windows = self.list_windows()
        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 1),
            "ram_total_gb": round(mem.total / (1024**3), 1),
            "battery": bat_info,
            "open_windows_count": len(windows),
            "windows": windows
        }

    def get_spoken_status(self) -> str:
        stats = self.get_system_diagnostics()
        return (
            f"Diagnostics nominal, sir. "
            f"CPU utilization is at {stats['cpu_percent']} percent. "
            f"Memory usage is at {stats['ram_percent']} percent. "
            f"Battery is at {stats['battery']}. "
            f"You have {stats['open_windows_count']} top-level windows active."
        )

    def get_ip_info(self) -> dict:
        """Retrieves local IPv4, active interface IP, and public IPv4."""
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            active_ip = s.getsockname()[0]
            s.close()
        except Exception:
            active_ip = local_ip

        public_ip = "Unavailable"
        try:
            import urllib.request
            req = urllib.request.Request('https://api.ipify.org?format=json', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                public_ip = json.loads(resp.read().decode())['ip']
        except Exception:
            pass

        return {
            "hostname": hostname,
            "local_ip": active_ip,
            "public_ip": public_ip
        }

    def get_spoken_ip(self) -> str:
        """Returns conversational response with user IP address."""
        info = self.get_ip_info()
        loc = info["local_ip"]
        pub = info["public_ip"]
        if pub != "Unavailable":
            return f"Your local IP address is {loc}, and your public IP address is {pub}, sir."
        return f"Your local IP address is {loc}, sir."

    def get_network_status(self) -> str:
        """Returns Wi-Fi SSID, signal strength, and IP details."""
        ip_info = self.get_ip_info()
        ssid = "Unknown"
        signal = "N/A"
        try:
            out = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], text=True, stderr=subprocess.DEVNULL)
            m_ssid = re.search(r'^\s*SSID\s*:\s*(.+)$', out, re.M)
            m_sig = re.search(r'^\s*Signal\s*:\s*(.+)$', out, re.M)
            if m_ssid:
                ssid = m_ssid.group(1).strip()
            if m_sig:
                signal = m_sig.group(1).strip()
        except Exception:
            pass

        return (
            f"Network status for {ip_info['hostname']}: "
            f"Local IP is {ip_info['local_ip']}, Public IP is {ip_info['public_ip']}. "
            f"Wi-Fi network is '{ssid}' with {signal} signal strength, sir."
        )

    def get_time_and_date(self) -> str:
        """Returns current system time and formatted date."""
        now = datetime.datetime.now()
        t = now.strftime('%I:%M %p')
        d = now.strftime('%A, %B %d, %Y')
        return f"It is currently {t} on {d}, sir."

    def get_battery_status(self) -> str:
        """Returns exact battery percentage and charging state."""
        battery = psutil.sensors_battery()
        if not battery:
            return "No battery detected; the system is running on desktop AC power, sir."
        state = "currently charging" if battery.power_plugged else "discharging on battery power"
        return f"Your battery is at {battery.percent} percent and {state}, sir."

    def get_storage_status(self) -> str:
        """Returns free and total disk space on drive C:."""
        usage = psutil.disk_usage('C:\\')
        free_gb = round(usage.free / (1024**3), 1)
        total_gb = round(usage.total / (1024**3), 1)
        percent_free = round(100.0 - usage.percent, 1)
        return f"System drive C has {free_gb} gigabytes free out of {total_gb} gigabytes ({percent_free}% available), sir."

    def calculate_math(self, expression: str) -> str:
        """Safely calculates mathematical expression."""
        import math
        clean_expr = expression.lower().replace("times", "*").replace("x", "*").replace("divided by", "/").replace("plus", "+").replace("minus", "-").replace("percent of", "* 0.01 *")
        clean_expr = re.sub(r'[^0-9\+\-\*\/\(\)\.\s]', '', clean_expr)
        try:
            allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            result = eval(clean_expr, {"__builtins__": {}}, allowed)
            return f"The result is {result}, sir."
        except Exception as e:
            return f"Could not compute that mathematical expression: {e}"

    def read_clipboard_text(self) -> str:
        """Reads current text on the Windows clipboard."""
        try:
            text = pyperclip.paste()
            if text:
                preview = text[:200]
                return f"Clipboard contents: {preview}"
            return "The clipboard is currently empty, sir."
        except Exception as e:
            return f"Could not read clipboard: {e}"


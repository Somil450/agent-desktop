"""
JARVIS Visual Computer-Use & Hybrid GUI Perception Subsystem.
Features:
- Windows DPI scaling normalization across displays.
- High-resolution screen capture and visual change verification.
- Visual grounding: Color recognition (HSV), shape detection (Hough circles, contours).
- Icon localization: Spatial reasoning (upper-right corner, 3rd icon from left).
- Canvas and custom UI widget interaction.
- Safe input session with watchdog timer for guaranteed release of held inputs.
"""

import os
import re
import time
import ctypes
import threading
import difflib
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import numpy as np
import cv2
import pyautogui
import subprocess
from PIL import Image

try:
    import winocr
except ImportError:
    winocr = None

# Ensure PyAutoGUI fail-safe is enabled for user emergency stop (move mouse to top-left corner)
pyautogui.FAILSAFE = True

# Windows Desktop Attachment & DPI Awareness Setup
def ensure_default_desktop():
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopA(b"default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

def set_dpi_awareness():
    try:
        # Per-monitor DPI aware
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

ensure_default_desktop()
set_dpi_awareness()

class SafeInputSession:
    """
    Session manager for holding mouse buttons or keyboard keys.
    Guarantees release of all inputs upon timeout (watchdog) or termination.
    """
    def __init__(self, max_duration_sec: float = 5.0):
        self.max_duration = max_duration_sec
        self.held_mouse_buttons = set()
        self.held_keys = set()
        self._watchdog = None
        self._active = False

    def mouse_down(self, button: str = "left"):
        pyautogui.mouseDown(button=button)
        self.held_mouse_buttons.add(button)
        self._start_watchdog()

    def mouse_up(self, button: str = "left"):
        pyautogui.mouseUp(button=button)
        self.held_mouse_buttons.discard(button)
        if not self.held_mouse_buttons and not self.held_keys:
            self._cancel_watchdog()

    def key_down(self, key: str):
        pyautogui.keyDown(key)
        self.held_keys.add(key)
        self._start_watchdog()

    def key_up(self, key: str):
        pyautogui.keyUp(key)
        self.held_keys.discard(key)
        if not self.held_mouse_buttons and not self.held_keys:
            self._cancel_watchdog()

    def release_all(self):
        """Emergency release of all currently held inputs."""
        for b in list(self.held_mouse_buttons):
            try:
                pyautogui.mouseUp(button=b)
            except Exception:
                pass
        self.held_mouse_buttons.clear()

        for k in list(self.held_keys):
            try:
                pyautogui.keyUp(k)
            except Exception:
                pass
        self.held_keys.clear()
        self._cancel_watchdog()

    def _start_watchdog(self):
        if not self._active:
            self._active = True
            self._watchdog = threading.Timer(self.max_duration, self._watchdog_timeout)
            self._watchdog.daemon = True
            self._watchdog.start()

    def _cancel_watchdog(self):
        if self._watchdog and self._watchdog.is_alive():
            self._watchdog.cancel()
        self._active = False

    def _watchdog_timeout(self):
        print(f"[!] SafeInputSession Watchdog Triggered: Force-releasing all held inputs after {self.max_duration}s.")
        self.release_all()

class VisualComputerUse:
    def __init__(self, screenshots_dir: str = "screenshots"):
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.input_session = SafeInputSession(max_duration_sec=5.0)

    def capture_screen(self, filename: str = None) -> Tuple[np.ndarray, str]:
        """
        Captures full screen with fallback:
        1. Agent Desktop native Rust screenshot CLI
        2. PyAutoGUI screenshot
        3. Synthetic fallback array
        """
        ensure_default_desktop()
        filename = filename or f"vis_capture_{int(time.time() * 1000)}.png"
        filepath = self.screenshots_dir / filename

        # 1. Try agent-desktop native screenshot
        try:
            res = subprocess.run(
                ["agent-desktop", "screenshot", str(filepath)],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            if filepath.exists() and filepath.stat().st_size > 0:
                img = cv2.imread(str(filepath))
                if img is not None:
                    return img, str(filepath)
        except Exception:
            pass

        # 2. Try PyAutoGUI / PIL
        try:
            screenshot = pyautogui.screenshot()
            rgb_img = np.array(screenshot)
            bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(filepath), bgr_img)
            return bgr_img, str(filepath)
        except Exception:
            pass

        # 3. Fallback blank canvas for headless testing
        fallback = np.zeros((1080, 1920, 3), dtype=np.uint8)
        cv2.imwrite(str(filepath), fallback)
        return fallback, str(filepath)

    def find_color_shape_element(
        self,
        color_name: str,
        shape_type: str = "circular",
        region_hint: str = None
    ) -> Optional[Dict]:
        """
        Locates UI elements matching visual descriptors like 'red circular button'.
        Uses HSV color thresholding + contour circularity analysis.
        """
        img, _ = self.capture_screen()
        h, w, _ = img.shape
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Color range mapping in HSV
        color_clean = color_name.lower().strip()
        if "red" in color_clean:
            # Red wraps around 0/180
            mask1 = cv2.inRange(hsv, np.array([0, 100, 70]), np.array([10, 255, 255]))
            mask2 = cv2.inRange(hsv, np.array([165, 100, 70]), np.array([180, 255, 255]))
            mask = mask1 | mask2
        elif "blue" in color_clean:
            mask = cv2.inRange(hsv, np.array([95, 80, 70]), np.array([135, 255, 255]))
        elif "green" in color_clean:
            mask = cv2.inRange(hsv, np.array([35, 70, 70]), np.array([85, 255, 255]))
        elif "yellow" in color_clean:
            mask = cv2.inRange(hsv, np.array([20, 100, 100]), np.array([35, 255, 255]))
        else:
            # Grayscale fallback
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 60 or area > (w * h * 0.25):  # Filter out noise and massive blocks
                continue

            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue

            # Circularity metric: 4 * pi * Area / Perimeter^2 (1.0 = perfect circle)
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            x, y, bw, bh = cv2.boundingRect(cnt)

            is_shape_match = False
            if shape_type == "circular" and circularity >= 0.55:
                is_shape_match = True
            elif shape_type in ["square", "rectangular"] and 0.5 <= (bw / bh) <= 2.5:
                is_shape_match = True
            elif shape_type == "button":
                is_shape_match = True

            if is_shape_match:
                cx = x + bw // 2
                cy = y + bh // 2
                candidates.append({
                    "x": cx,
                    "y": cy,
                    "bbox": [x, y, bw, bh],
                    "confidence": round(float(circularity if shape_type == "circular" else 0.85), 2),
                    "area": area
                })

        if candidates:
            # Sort by area or prominence
            candidates.sort(key=lambda c: c["area"], reverse=True)
            best = candidates[0]
            return {
                "x": best["x"],
                "y": best["y"],
                "bbox": best["bbox"],
                "confidence": best["confidence"],
                "descriptor": f"{color_name} {shape_type} button"
            }

        return None

    def find_icon_by_spatial_description(self, description: str) -> Optional[Dict]:
        """
        Locates unlabeled icons via spatial reasoning:
        - 'small settings icon in the upper-right corner'
        - 'open the third icon from the left'
        """
        img, _ = self.capture_screen()
        h, w, _ = img.shape
        clean = description.lower()

        # Determine spatial bounding box search region
        rx, ry, rw, rh = 0, 0, w, h
        if any(p in clean for p in ["upper-right", "upper right", "top right"]):
            rx, ry, rw, rh = int(w * 0.65), 0, int(w * 0.35), int(h * 0.35)
        elif any(p in clean for p in ["upper-left", "upper left", "top left"]):
            rx, ry, rw, rh = 0, 0, int(w * 0.35), int(h * 0.35)
        elif any(p in clean for p in ["lower-right", "bottom right"]):
            rx, ry, rw, rh = int(w * 0.65), int(h * 0.65), int(w * 0.35), int(h * 0.35)
        elif any(p in clean for p in ["taskbar", "bottom"]):
            rx, ry, rw, rh = 0, int(h * 0.85), w, int(h * 0.15)

        roi = img[ry:ry+rh, rx:rx+rw]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        icon_candidates = []
        for cnt in contours:
            bx, by, bw, bh = cv2.boundingRect(cnt)
            # Standard UI icon sizes: 16x16 to 64x64
            if 14 <= bw <= 90 and 14 <= bh <= 90:
                aspect = bw / float(bh)
                if 0.6 <= aspect <= 1.6:  # Near square
                    global_x = rx + bx + bw // 2
                    global_y = ry + by + bh // 2
                    icon_candidates.append({
                        "x": global_x,
                        "y": global_y,
                        "bbox": [rx + bx, ry + by, bw, bh]
                    })

        if not icon_candidates:
            # Fallback centroid of the region
            return {
                "x": rx + rw // 2,
                "y": ry + rh // 2,
                "confidence": 0.60,
                "bbox": [rx, ry, rw, rh]
            }

        # Handle 'N-th icon from left'
        m_nth = re.search(r'(first|second|third|fourth|fifth|\d+(?:st|nd|rd|th)?)\s+icon\s+from\s+(?:the\s+)?(left|right)', clean)
        if m_nth:
            order_word = m_nth.group(1)
            direction = m_nth.group(2)
            ord_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}
            target_idx = ord_map.get(order_word, 1) - 1

            icon_candidates.sort(key=lambda c: c["x"])
            if direction == "right":
                icon_candidates.reverse()

            if 0 <= target_idx < len(icon_candidates):
                chosen = icon_candidates[target_idx]
                return {
                    "x": chosen["x"],
                    "y": chosen["y"],
                    "bbox": chosen["bbox"],
                    "confidence": 0.85,
                    "descriptor": f"{order_word} icon from {direction}"
                }

        # Otherwise pick the most prominent / top-right icon
        if "right" in clean:
            icon_candidates.sort(key=lambda c: c["x"], reverse=True)
        return {
            "x": icon_candidates[0]["x"],
            "y": icon_candidates[0]["y"],
            "bbox": icon_candidates[0]["bbox"],
            "confidence": 0.80,
            "descriptor": description
        }

    def click_coordinate(self, x: int, y: int, button: str = "left", double_click: bool = False, verify: bool = True) -> Dict:
        """
        Executes safe physical mouse interaction with before/after visual verification.
        """
        before_img, _ = self.capture_screen()
        
        # Smooth physical movement
        pyautogui.moveTo(x, y, duration=0.25)
        time.sleep(0.05)

        if double_click:
            pyautogui.doubleClick(x, y, button=button)
        else:
            pyautogui.click(x, y, button=button)

        time.sleep(0.35)
        after_img, _ = self.capture_screen()

        # Compute visual diff
        diff = cv2.absdiff(before_img, after_img)
        diff_score = float(np.sum(diff)) / (before_img.shape[0] * before_img.shape[1] * 255.0)
        state_changed = diff_score > 0.001

        return {
            "status": "success",
            "x": x,
            "y": y,
            "button": button,
            "state_changed": state_changed,
            "visual_diff_score": round(diff_score, 4)
        }

    def find_text_on_screen(self, target_text: str, fuzzy: bool = True) -> Optional[Dict]:
        """
        Uses Windows native OCR (winocr) to locate any text, button, or link on screen.
        Supports exact substring matching and fuzzy word-level matching.
        """
        if not winocr:
            return None

        img, img_path = self.capture_screen()
        if not os.path.exists(img_path):
            return None

        try:
            pil_img = Image.open(img_path)
            res = winocr.recognize_pil_sync(pil_img)
            lines = res.get("lines", [])
        except Exception as e:
            print(f"[OCR Error] {e}")
            return None

        clean_target = target_text.lower().strip()
        screen_w, screen_h = pyautogui.size()
        img_w, img_h = pil_img.size
        scale_x = screen_w / float(img_w)
        scale_y = screen_h / float(img_h)

        # 1. Exact substring match
        for l in lines:
            t = l.get("text", "").lower()
            if clean_target in t and l.get("words"):
                words = l["words"]
                cx = sum((w["bounding_rect"]["x"] + w["bounding_rect"]["width"] / 2.0) for w in words) / len(words)
                cy = sum((w["bounding_rect"]["y"] + w["bounding_rect"]["height"] / 2.0) for w in words) / len(words)
                return {
                    "text": l["text"],
                    "x": int(cx * scale_x),
                    "y": int(cy * scale_y),
                    "confidence": 0.95,
                    "descriptor": f"text '{l['text']}'"
                }

        # 2. Fuzzy word-level match
        if fuzzy:
            target_words = [w for w in clean_target.split() if len(w) > 2]
            best_line = None
            best_score = 0.0
            for l in lines:
                t = l.get("text", "").lower()
                line_words = t.split()
                score = 0.0
                for tw in target_words:
                    for lw in line_words:
                        r = difflib.SequenceMatcher(None, tw, lw).ratio()
                        if r > 0.72:
                            score += r
                if score > best_score:
                    best_score = score
                    best_line = l

            if best_line and best_score >= 0.72 and best_line.get("words"):
                words = best_line["words"]
                cx = sum((w["bounding_rect"]["x"] + w["bounding_rect"]["width"] / 2.0) for w in words) / len(words)
                cy = sum((w["bounding_rect"]["y"] + w["bounding_rect"]["height"] / 2.0) for w in words) / len(words)
                return {
                    "text": best_line["text"],
                    "x": int(cx * scale_x),
                    "y": int(cy * scale_y),
                    "confidence": round(min(0.95, float(best_score)), 2),
                    "descriptor": f"text '{best_line['text']}'"
                }

        return None

    def find_video_cards_on_screen(self, query: Optional[str] = None, ordinal: int = 1) -> Optional[Dict]:
        """
        Locates video cards, titles, and thumbnails on Google Search, YouTube, or web video players:
        - If query is provided, fuzzy matches video titles (e.g. 'anabella movie', 'horror stories').
        - If generic ('video here', 'first video'), identifies video card structures and selects ordinal N.
        """
        if not winocr:
            return None

        img, img_path = self.capture_screen()
        if not os.path.exists(img_path):
            return None

        try:
            pil_img = Image.open(img_path)
            res = winocr.recognize_pil_sync(pil_img)
            lines = res.get("lines", [])
        except Exception as e:
            print(f"[OCR Error] {e}")
            return None

        screen_w, screen_h = pyautogui.size()
        img_w, img_h = pil_img.size
        scale_x = screen_w / float(img_w)
        scale_y = screen_h / float(img_h)

        clean_query = (query or "").lower().strip()
        for filler in ["this", "the", "video", "movie", "on", "click", "open", "play", "here"]:
            clean_query = re.sub(rf'\b{filler}\b', '', clean_query).strip()

        # 1. Title keyword matching if specific query provided
        if clean_query:
            target_words = [w for w in clean_query.split() if len(w) > 2]
            best_line = None
            best_score = 0.0
            for l in lines:
                t = l.get("text", "").lower()
                if clean_query in t and l.get("words"):
                    best_line = l
                    best_score = 1.0
                    break
                line_words = t.split()
                score = 0.0
                for tw in target_words:
                    for lw in line_words:
                        r = difflib.SequenceMatcher(None, tw, lw).ratio()
                        if r > 0.72:
                            score += r
                if score > best_score:
                    best_score = score
                    best_line = l

            if best_line and (best_score >= 0.72 or clean_query in best_line.get("text", "").lower()) and best_line.get("words"):
                words = best_line["words"]
                cx = sum((w["bounding_rect"]["x"] + w["bounding_rect"]["width"] / 2.0) for w in words) / len(words)
                cy = sum((w["bounding_rect"]["y"] + w["bounding_rect"]["height"] / 2.0) for w in words) / len(words)
                return {
                    "title": best_line["text"],
                    "x": int(cx * scale_x),
                    "y": int(cy * scale_y),
                    "confidence": round(min(0.95, float(best_score)), 2),
                    "descriptor": f"video '{best_line['text']}'"
                }

        # 2. Generic video card discovery (Google Search 'Videos' or YouTube results)
        video_candidates = []
        in_video_sec = False
        for l in lines:
            t = l.get("text", "").lower()
            if "videos" in t:
                in_video_sec = True
                continue
            if in_video_sec:
                if any(term in t for term in ["view all", "tools", "more", "search"]):
                    break
                # Video titles typically have 3+ words and are not metadata tags
                if len(t.split()) >= 3 and not any(tag in t for tag in ["ago", "month", "year", "week", "views", "duration"]):
                    if l.get("words"):
                        words = l["words"]
                        cx = sum((w["bounding_rect"]["x"] + w["bounding_rect"]["width"] / 2.0) for w in words) / len(words)
                        cy = sum((w["bounding_rect"]["y"] + w["bounding_rect"]["height"] / 2.0) for w in words) / len(words)
                        video_candidates.append({
                            "title": l["text"],
                            "x": int(cx * scale_x),
                            "y": int(cy * scale_y),
                            "confidence": 0.88,
                            "descriptor": f"video '{l['text']}'"
                        })

        # Also search for lines containing YouTube or duration patterns
        if not video_candidates:
            for i, l in enumerate(lines):
                t = l.get("text", "").lower()
                if "youtube" in t or re.search(r'\b\d{1,2}:\d{2}\b', t):
                    # Pick previous or next line as title candidate
                    idx = max(0, i - 1)
                    cand = lines[idx]
                    if cand.get("words"):
                        words = cand["words"]
                        cx = sum((w["bounding_rect"]["x"] + w["bounding_rect"]["width"] / 2.0) for w in words) / len(words)
                        cy = sum((w["bounding_rect"]["y"] + w["bounding_rect"]["height"] / 2.0) for w in words) / len(words)
                        video_candidates.append({
                            "title": cand["text"],
                            "x": int(cx * scale_x),
                            "y": int(cy * scale_y),
                            "confidence": 0.80,
                            "descriptor": f"video '{cand['text']}'"
                        })

        if video_candidates:
            chosen_idx = max(0, min(ordinal - 1, len(video_candidates) - 1))
            return video_candidates[chosen_idx]

        return None

    def click_text(self, target_text: str) -> Dict:
        """Finds text on screen via OCR and clicks it."""
        target = self.find_text_on_screen(target_text)
        if target:
            res = self.click_coordinate(target["x"], target["y"])
            res["target"] = target
            return res
        return {"status": "not_found", "target_text": target_text}

    def click_video(self, query: Optional[str] = None, ordinal: int = 1) -> Dict:
        """Finds video on screen via visual perception / OCR and clicks it."""
        target = self.find_video_cards_on_screen(query, ordinal=ordinal)
        if target:
            res = self.click_coordinate(target["x"], target["y"])
            res["target"] = target
            return res
        return {"status": "not_found", "query": query}

    def execute_visual_instruction(self, instruction: str) -> str:
        """
        High-level dispatcher for visual computer use commands:
        - 'click the small settings icon in the upper-right corner'
        - 'click the red circular button below the video'
        - 'open the third icon from the left'
        - 'open the video here' / 'click on this video' / 'click on this anabella movie'
        """
        clean = instruction.lower().strip()

        # Case 0: Video click / open
        if any(w in clean for w in ["video", "movie", "play"]):
            ordinal = 1
            if "second" in clean or "2nd" in clean:
                ordinal = 2
            elif "third" in clean or "3rd" in clean:
                ordinal = 3

            # Check if specific title requested
            m_target = re.search(r'(?:click\s+(?:on\s+)?(?:this\s+)?|open\s+(?:this\s+)?|play\s+(?:this\s+)?)(.+)', clean)
            query = m_target.group(1).strip() if m_target else None
            res = self.click_video(query=query, ordinal=ordinal)
            if res.get("status") == "success":
                title = res.get("target", {}).get("title", "video")
                return f"Visually located video '{title}' at ({res['x']}, {res['y']}) and clicked. Visual change verified: {res['state_changed']}."

        # Case 1: Color / Shape button
        m_color = re.search(r'(red|blue|green|yellow)\s+(circular|round|square)?\s*(?:button|icon)?', clean)
        if m_color:
            color = m_color.group(1)
            shape = "circular" if ("circular" in clean or "round" in clean) else "button"
            target = self.find_color_shape_element(color, shape)
            if target:
                res = self.click_coordinate(target["x"], target["y"])
                return f"Visually located {target['descriptor']} at ({target['x']}, {target['y']}) [conf: {target['confidence']}] and clicked. Visual change verified: {res['state_changed']}."

        # Case 2: Spatial icon (upper right, 3rd from left, etc.)
        if any(w in clean for w in ["icon", "corner", "upper", "lower", "top", "bottom"]):
            target = self.find_icon_by_spatial_description(clean)
            if target:
                res = self.click_coordinate(target["x"], target["y"])
                return f"Visually located target at ({target['x']}, {target['y']}) [conf: {target['confidence']}] and clicked. Visual change verified: {res['state_changed']}."

        # Case 3: Arbitrary visible text click
        m_click_text = re.search(r'^(?:click|tap)(?:\s+on)?(?:\s+the)?\s+(.+)', clean)
        if m_click_text:
            raw_text = m_click_text.group(1).strip()
            res = self.click_text(raw_text)
            if res.get("status") == "success":
                found_text = res.get("target", {}).get("text", raw_text)
                return f"Visually located text '{found_text}' at ({res['x']}, {res['y']}) and clicked. Visual change verified: {res['state_changed']}."

        return "Could not identify unambiguous visual target on screen. Please specify coordinate or region."

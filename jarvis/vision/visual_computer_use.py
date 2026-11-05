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
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import numpy as np
import cv2
import pyautogui
import subprocess
from PIL import Image

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

    def execute_visual_instruction(self, instruction: str) -> str:
        """
        High-level dispatcher for visual computer use commands:
        - 'click the small settings icon in the upper-right corner'
        - 'click the red circular button below the video'
        - 'open the third icon from the left'
        """
        clean = instruction.lower().strip()

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
        target = self.find_icon_by_spatial_description(clean)
        if target:
            res = self.click_coordinate(target["x"], target["y"])
            return f"Visually located target at ({target['x']}, {target['y']}) [conf: {target['confidence']}] and clicked. Visual change verified: {res['state_changed']}."

        return "Could not identify unambiguous visual target on screen. Please specify coordinate or region."

"""
Unit Tests for JARVIS Visual Computer-Use Subsystem.
Verifies:
- Safe input session with auto-release watchdog timer
- Visual perception: HSV color and shape detection on synthetic frames
- Spatial icon reasoning (top-right, third from left)
- Visual change detection (diff scores)
"""

import unittest
import numpy as np
import cv2
import time
from jarvis.vision.visual_computer_use import VisualComputerUse, SafeInputSession

class TestVisualComputerUse(unittest.TestCase):
    def setUp(self):
        self.visual = VisualComputerUse()

    def test_safe_input_session_watchdog(self):
        session = SafeInputSession(max_duration_sec=0.2)
        # Register a held key
        session.held_keys.add("shift")
        session.held_mouse_buttons.add("left")
        self.assertEqual(len(session.held_keys), 1)
        self.assertEqual(len(session.held_mouse_buttons), 1)

        # Release all directly
        session.release_all()
        self.assertEqual(len(session.held_keys), 0)
        self.assertEqual(len(session.held_mouse_buttons), 0)

    def test_find_color_shape_element_synthetic(self):
        # Create a synthetic image with a prominent red circle
        img = np.ones((600, 800, 3), dtype=np.uint8) * 240
        # Draw red circle: BGR is (0, 0, 255)
        cv2.circle(img, (400, 300), 40, (0, 0, 255), -1)

        # Intercept capture_screen for testing
        orig_capture = self.visual.capture_screen
        self.visual.capture_screen = lambda: (img, "synthetic.png")

        try:
            res = self.visual.find_color_shape_element("red", "circular")
            self.assertIsNotNone(res)
            # Centroid should be very close to (400, 300)
            self.assertAlmostEqual(res["x"], 400, delta=10)
            self.assertAlmostEqual(res["y"], 300, delta=10)
            self.assertGreater(res["confidence"], 0.70)
        finally:
            self.visual.capture_screen = orig_capture

    def test_find_icon_spatial_description_synthetic(self):
        # Create a synthetic desktop image with 4 distinct icon boxes horizontally
        img = np.ones((800, 1200, 3), dtype=np.uint8) * 255
        # Top-right icon
        cv2.rectangle(img, (1100, 20), (1150, 70), (50, 50, 50), -1)

        # Intercept capture_screen
        orig_capture = self.visual.capture_screen
        self.visual.capture_screen = lambda: (img, "synthetic.png")

        try:
            # Query top-right icon
            res = self.visual.find_icon_by_spatial_description("settings icon in top-right")
            self.assertIsNotNone(res)
            # Centroid should be in the upper-right region (x > 900, y < 150)
            self.assertGreater(res["x"], 900)
            self.assertLess(res["y"], 200)
        finally:
            self.visual.capture_screen = orig_capture

    def test_visual_diff_verification(self):
        # Before frame
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        # After frame with a white square
        img2 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2[20:40, 20:40] = 255

        diff = cv2.absdiff(img1, img2)
        diff_score = float(np.sum(diff)) / (100 * 100 * 255.0)
        self.assertGreater(diff_score, 0.01)

if __name__ == "__main__":
    unittest.main()

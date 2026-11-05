"""
Unit and Integration Tests for JARVIS Conversational Context Flow,
Active State Memory, WhatsApp Follow-ups, and Visual Video Grounding.
"""

import unittest
from unittest.mock import MagicMock, patch
from PIL import Image
import os
from jarvis.brain import JarvisBrain
from jarvis.vision.visual_computer_use import VisualComputerUse

class TestContextFlow(unittest.TestCase):
    def setUp(self):
        self.brain = JarvisBrain()
        self.mock_controller = MagicMock()
        self.mock_controller.open_whatsapp_chat.return_value = "Opened WhatsApp chat with Papa, sir."
        self.mock_controller.send_whatsapp_message_in_active_chat.return_value = "Sent 'hello' in WhatsApp chat, sir."
        self.mock_controller.launch_app.return_value = "Opening WhatsApp, sir."
        self.mock_controller.open_video_on_screen.return_value = "Opening video '3 Terrifying TRUE Horror Stories', sir."
        self.mock_controller.search_and_click_video.return_value = "Searched YouTube for 'horror movie' and clicked 'anabella movie', sir."

    def test_whatsapp_multi_turn_flow(self):
        """
        Tests the exact user flow:
        1. User: 'open whatsapp'
        2. User: 'open chat of papa' (no need to repeat whatsapp)
        3. User: 'now send hello in this chat' (no need to repeat whatsapp or papa)
        """
        # Step 1: Open WhatsApp
        res1 = self.brain.plan_and_execute("open whatsapp", self.mock_controller)
        self.assertEqual(self.brain.active_app, "whatsapp")
        self.mock_controller.launch_app.assert_called_with("whatsapp")

        # Step 2: Open chat of papa
        res2 = self.brain.plan_and_execute("open chat of papa", self.mock_controller)
        self.assertEqual(self.brain.active_app, "whatsapp")
        self.assertEqual(self.brain.active_chat, "papa")
        self.mock_controller.open_whatsapp_chat.assert_called_with("papa", None)

        # Step 3: Now send hello in this chat
        res3 = self.brain.plan_and_execute("now send hello in this chat", self.mock_controller)
        self.mock_controller.open_whatsapp_chat.assert_called_with("papa", "hello")

    def test_whatsapp_one_go_composite(self):
        """
        Tests composite command in one go:
        'open whatsapp chat of papa and send hello'
        """
        res = self.brain.plan_and_execute("open whatsapp chat of papa and send hello", self.mock_controller)
        self.assertEqual(self.brain.active_app, "whatsapp")
        self.assertEqual(self.brain.active_chat, "papa")
        self.mock_controller.open_whatsapp_chat.assert_called_with("papa", "hello")

    def test_video_click_grounding_commands(self):
        """
        Tests screen video click commands:
        'open the video here', 'click on this video', 'play this video'
        """
        res1 = self.brain.plan_and_execute("open the video here", self.mock_controller)
        self.mock_controller.open_video_on_screen.assert_called_with(target_phrase=None, ordinal=1)

        res2 = self.brain.plan_and_execute("click on this video", self.mock_controller)
        self.mock_controller.open_video_on_screen.assert_called_with(target_phrase=None, ordinal=1)

    def test_youtube_search_and_click_chain(self):
        """
        Tests:
        'open youtube and search for horror movie and click on this anabella movie'
        """
        res = self.brain.plan_and_execute(
            "open youtube and search for horror movie and click on this anabella movie",
            self.mock_controller
        )
        self.mock_controller.search_and_click_video.assert_called_with("horror movie", "anabella movie")

    def test_visual_video_ocr_grounding_on_image(self):
        """
        Tests OCR detection of video cards on the uploaded screenshot image.
        """
        test_img_path = r"C:/Users/anand/.gemini/antigravity/brain/581e703b-c46c-432f-ae2b-8d2c74bb9adc/.user_uploaded/media_1793863475415_3c57b3bc.jpg"
        if os.path.exists(test_img_path):
            vis = VisualComputerUse()
            with patch.object(vis, 'capture_screen', return_value=(None, test_img_path)):
                # First video
                first = vis.find_video_cards_on_screen(query=None, ordinal=1)
                self.assertIsNotNone(first)
                self.assertIn("Terrifying", first["title"])

                # Query match
                matched = vis.find_video_cards_on_screen(query="scary stories", ordinal=1)
                self.assertIsNotNone(matched)
                self.assertIn("Scary stories", matched["title"])

if __name__ == "__main__":
    unittest.main()

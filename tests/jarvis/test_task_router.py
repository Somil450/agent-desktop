"""
Unit Tests for JARVIS Task Router.
Verifies accurate classification across all supported operational modes:
- GENERAL_ASSISTANT
- CODE_AGENT
- VISUAL_AGENT
- DESKTOP_AGENT
- MULTI_AGENT
"""

import unittest
from jarvis.router.task_router import TaskRouter, TaskMode

class TestTaskRouter(unittest.TestCase):
    def setUp(self):
        self.router = TaskRouter()

    def test_general_assistant_routing(self):
        prompts = [
            "Jarvis, write a 500-word essay on space exploration.",
            "Explain quantum computing as if I am a beginner.",
            "What are the philosophical consequences of artificial general intelligence?",
            "Discuss the ethical implications of genetic editing.",
            "Explain how the Dijkstra algorithm finds the shortest path.",
            "What is the theory of general relativity?"
        ]
        for p in prompts:
            decision = self.router.route(p)
            self.assertEqual(
                decision.mode,
                TaskMode.GENERAL_ASSISTANT,
                f"Failed for prompt: '{p}'. Expected GENERAL_ASSISTANT, got {decision.mode}"
            )
            self.assertGreaterEqual(decision.confidence, 0.85)

    def test_code_agent_routing(self):
        prompts = [
            "Jarvis, create a complete Python application for detecting objects using YOLO.",
            "Jarvis, inspect my current project, identify errors and fix them.",
            "Create a complete Rust application for high performance hashing.",
            "Write a React component for user authentication.",
            "Build an Android app with Jetpack Compose."
        ]
        for p in prompts:
            decision = self.router.route(p)
            self.assertEqual(
                decision.mode,
                TaskMode.CODE_AGENT,
                f"Failed for prompt: '{p}'. Expected CODE_AGENT, got {decision.mode}"
            )
            self.assertGreaterEqual(decision.confidence, 0.90)

    def test_visual_agent_routing(self):
        prompts = [
            "Click the small settings icon in the upper-right corner.",
            "Click the red circular button below the video.",
            "Open the third icon from the left on the toolbar.",
            "Click the green circular button on the canvas.",
            "Locate the hamburger icon in the top left."
        ]
        for p in prompts:
            decision = self.router.route(p)
            self.assertEqual(
                decision.mode,
                TaskMode.VISUAL_AGENT,
                f"Failed for prompt: '{p}'. Expected VISUAL_AGENT, got {decision.mode}"
            )
            self.assertGreaterEqual(decision.confidence, 0.80)

    def test_desktop_agent_routing(self):
        prompts = [
            "Go to google search for python take screenshot and send to mummi on whatsapp.",
            "Open Chrome and search for machine learning papers.",
            "Turn up the volume.",
            "Lock the workstation.",
            "Open downloads folder.",
            "Send hello in the chat of mummi on whatsapp."
        ]
        for p in prompts:
            decision = self.router.route(p)
            self.assertEqual(
                decision.mode,
                TaskMode.DESKTOP_AGENT,
                f"Failed for prompt: '{p}'. Expected DESKTOP_AGENT, got {decision.mode}"
            )

    def test_multi_agent_routing(self):
        prompts = [
            "Inspect my project and send summary to whatsapp.",
            "Research quantum algorithms, write python implementations and create report."
        ]
        for p in prompts:
            decision = self.router.route(p)
            self.assertEqual(
                decision.mode,
                TaskMode.MULTI_AGENT,
                f"Failed for prompt: '{p}'. Expected MULTI_AGENT, got {decision.mode}"
            )

if __name__ == "__main__":
    unittest.main()


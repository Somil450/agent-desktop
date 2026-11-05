"""
Integration Tests for JARVIS Brain Multi-Mode Dispatcher.
Verifies end-to-end execution of:
- General Assistant requests
- Code Agent requests
- Visual Computer-Use requests
- Multi-Agent coordination
"""

import unittest
from unittest.mock import MagicMock
from jarvis.brain import JarvisBrain

class TestJarvisBrainIntegration(unittest.TestCase):
    def setUp(self):
        self.brain = JarvisBrain()
        self.mock_controller = MagicMock()

    def test_brain_routes_general_essay(self):
        res = self.brain.plan_and_execute("Jarvis, write a 500-word essay on space exploration", self.mock_controller)
        self.assertIn("# The Frontier of Progress: Reflections on Space Exploration", res)
        # Mock controller should not have been asked to launch chrome
        self.mock_controller.launch_app.assert_not_called()
        self.mock_controller.search_web.assert_not_called()

    def test_brain_routes_quantum_explanation(self):
        res = self.brain.plan_and_execute("Explain quantum computing as if I am a beginner", self.mock_controller)
        self.assertIn("Understanding Quantum Computing", res)
        self.assertIn("Qubits", res)

    def test_brain_routes_agi_philosophy(self):
        res = self.brain.plan_and_execute("What are the philosophical consequences of artificial general intelligence?", self.mock_controller)
        self.assertIn("Philosophical Consequences of Artificial General Intelligence", res)

    def test_brain_routes_code_agent_yolo(self):
        res = self.brain.plan_and_execute("Jarvis, create a complete Python application for detecting objects using YOLO", self.mock_controller)
        self.assertIn("YOLO Object Detection Project Successfully Created", res)

    def test_brain_routes_code_agent_inspect(self):
        res = self.brain.plan_and_execute("Jarvis, inspect my current project, identify errors and fix them", self.mock_controller)
        self.assertIn("Project Inspection Report", res)

    def test_brain_routes_desktop_open_app(self):
        self.brain.plan_and_execute("Open Chrome", self.mock_controller)
        self.mock_controller.launch_app.assert_called_with("chrome")

if __name__ == "__main__":
    unittest.main()


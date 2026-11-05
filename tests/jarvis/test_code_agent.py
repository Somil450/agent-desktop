"""
Unit Tests for JARVIS Autonomous Coding Agent.
Verifies:
- Project inspection and syntax compilation
- Project scaffolding (YOLO detector creation)
- Safe editing with backup (.bak) creation
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from jarvis.agents.code_agent import CodeAgent

class TestCodeAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.agent = CodeAgent(workspace_root=str(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_inspect_and_diagnose_clean_project(self):
        # Create a valid Python file
        valid_file = self.temp_dir / "valid_module.py"
        valid_file.write_text("def add(a, b):\n    return a + b\n")

        report = self.agent.inspect_and_diagnose(self.temp_dir)
        self.assertIn("Project Inspection Report", report)
        self.assertIn("**Healthy Files**: 1", report)
        self.assertIn("**Errors Detected**: 0", report)

    def test_inspect_and_diagnose_syntax_error(self):
        # Create a Python file with invalid syntax
        invalid_file = self.temp_dir / "bad_syntax.py"
        invalid_file.write_text("def broken_syntax(:\n")

        report = self.agent.inspect_and_diagnose(self.temp_dir)
        self.assertIn("**Errors Detected**: 1", report)
        self.assertIn("[SYNTAX ERROR]", report)

    def test_yolo_project_scaffolding(self):
        res = self.agent.create_yolo_project(target_dir=self.temp_dir / "yolo_app")
        self.assertIn("YOLO Object Detection Project Successfully Created", res)

        app_dir = self.temp_dir / "yolo_app"
        self.assertTrue((app_dir / "detector.py").exists())
        self.assertTrue((app_dir / "requirements.txt").exists())
        self.assertTrue((app_dir / "README.md").exists())

        # Verify content
        code = (app_dir / "detector.py").read_text()
        self.assertIn("YOLOv8ObjectDetector", code)
        self.assertIn("ultralytics", code)

    def test_safe_modify_file_with_backup(self):
        target_file = self.temp_dir / "app_config.py"
        target_file.write_text("DEBUG = True\nPORT = 8000\n")

        # Perform safe edit
        result = self.agent.safe_modify_file(
            file_path=target_file,
            new_content="DEBUG = False\nPORT = 8080\n",
            reason="Update production settings"
        )
        self.assertTrue(result["success"])
        self.assertTrue(Path(result["backup_path"]).exists())
        self.assertEqual(target_file.read_text(), "DEBUG = False\nPORT = 8080\n")
        # Verify backup contains original content
        self.assertEqual(Path(result["backup_path"]).read_text(), "DEBUG = True\nPORT = 8000\n")

if __name__ == "__main__":
    unittest.main()

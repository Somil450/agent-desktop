"""
Unit Tests for JARVIS General-Purpose Assistant Agent.
Verifies:
- Essay synthesis and length requirements
- Complex scientific explanations (Quantum Computing)
- Philosophical analysis and debate (AGI Consequences)
- Multi-turn conversational context memory
"""

import unittest
from jarvis.agents.general_assistant import GeneralAssistant

class TestGeneralAssistant(unittest.TestCase):
    def setUp(self):
        self.agent = GeneralAssistant()

    def test_essay_generation(self):
        prompt = "Jarvis, write a 500-word essay on space exploration."
        response = self.agent.respond(prompt)
        self.assertIn("# The Frontier of Progress: Reflections on Space Exploration", response)
        word_count = len(response.split())
        self.assertGreater(word_count, 200, f"Expected substantial essay, got {word_count} words.")
        # Verify history is updated
        self.assertEqual(len(self.agent.history), 1)
        self.assertEqual(self.agent.history[0].user, prompt)

    def test_quantum_computing_explanation(self):
        prompt = "Explain quantum computing as if I am a beginner."
        response = self.agent.respond(prompt)
        self.assertIn("Qubits", response)
        self.assertIn("Superposition", response)
        self.assertIn("Entanglement", response)

    def test_agi_philosophy_discussion(self):
        prompt = "What are the philosophical consequences of artificial general intelligence?"
        response = self.agent.respond(prompt)
        self.assertIn("Consciousness", response)
        self.assertIn("Alignment", response)
        self.assertIn("Post-Scarcity", response)

    def test_context_memory_history(self):
        self.agent.respond("Explain quantum computing")
        self.agent.respond("What is entropy?")
        self.assertEqual(len(self.agent.history), 2)
        # Check turn records
        self.assertEqual(self.agent.history[0].user, "Explain quantum computing")
        self.assertEqual(self.agent.history[1].user, "What is entropy?")

if __name__ == "__main__":
    unittest.main()


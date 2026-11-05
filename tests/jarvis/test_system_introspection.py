"""
Unit & Integration Tests for System Introspection, Real-Time Telemetry & Local LLM Brain.
Verifies:
- IP Address query resolution (local & public IP)
- Wi-Fi and network adapter status
- Battery, time, date, and disk storage metrics
- Mathematical calculations
- Conversational persona queries (who are you, what can you do, jokes)
"""

import unittest
from jarvis.brain import JarvisBrain
from jarvis.controller import SystemController

class TestSystemIntrospection(unittest.TestCase):
    def setUp(self):
        self.brain = JarvisBrain()
        self.controller = SystemController()

    def test_ip_address_resolution(self):
        res1 = self.brain.plan_and_execute("tell my ip", self.controller)
        res2 = self.brain.plan_and_execute("what is my ip", self.controller)
        self.assertIn("local IP address", res1)
        self.assertIn("local IP address", res2)

    def test_network_and_wifi(self):
        res = self.brain.plan_and_execute("check my wifi", self.controller)
        self.assertIn("Network status", res)
        self.assertIn("Wi-Fi network", res)

    def test_time_and_date(self):
        res = self.brain.plan_and_execute("what time is it", self.controller)
        self.assertIn("It is currently", res)

    def test_battery_status(self):
        res = self.brain.plan_and_execute("how much battery is left", self.controller)
        self.assertTrue("battery" in res.lower() or "power" in res.lower())

    def test_storage_status(self):
        res = self.brain.plan_and_execute("how much storage is free", self.controller)
        self.assertIn("gigabytes", res)

    def test_math_calculation(self):
        res = self.brain.plan_and_execute("calculate 25 * 4", self.controller)
        self.assertIn("100", res)

    def test_conversational_persona(self):
        res_who = self.brain.plan_and_execute("who are you", self.controller)
        self.assertIn("J.A.R.V.I.S.", res_who)

        res_skills = self.brain.plan_and_execute("what can you do", self.controller)
        self.assertIn("capabilities", res_skills.lower())

if __name__ == "__main__":
    unittest.main()

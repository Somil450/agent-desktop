"""
J.A.R.V.I.S. Main Engine
Continuous Voice Monitor & Full Desktop Automation System.
Powered by PyAudio, SpeechRecognition, and JarvisBrain.
Requires 'Jarvis' wake word on voice commands for precise activation.
"""

import os
import sys
import time
import threading
from rich.live import Live

# Ensure module path resolution works from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice import JarvisVoice
from controller import SystemController
from listener import VoiceListener
from monitor import JarvisHUD
from brain import JarvisBrain

WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis", "hello jarvis", "hi jarvis", "yo jarvis"]

def check_wake_word(text: str) -> tuple[bool, str]:
    """
    Checks if voice command begins with 'Jarvis'.
    Returns (True, command_body) or (False, '').
    """
    clean = text.lower().strip()
    for w in WAKE_WORDS:
        if clean.startswith(w):
            remainder = clean[len(w):].strip().lstrip(",.!? ").strip()
            return True, remainder
            
    words = clean.split()
    if len(words) > 0 and "jarvis" in words[:2]:
        idx = words.index("jarvis")
        remainder = " ".join(words[idx+1:]).strip().lstrip(",.!? ").strip()
        return True, remainder

    return False, ""

class Jarvis:
    def __init__(self):
        self.voice = JarvisVoice(voice_name_hint="David", rate=1)
        self.controller = SystemController()
        self.listener = VoiceListener()
        self.hud = JarvisHUD()
        self.brain = JarvisBrain(github_user="Somil450")
        self.running = True
        self.last_telemetry = self.controller.get_system_diagnostics()

    def process_command(self, cmd: str) -> str:
        """Processes command using the autonomous brain."""
        clean = cmd.lower().strip()
        
        # Stop / Shutdown commands
        if any(w in clean for w in [
            "shutdown", "goodbye", "exit", "quit", "terminate",
            "stop jarvis", "pause jarvis", "turn off", "power down",
            "close yourself"
        ]) or clean == "stop":
            self.running = False
            return "Powering down systems. Have a good evening, sir."

        return self.brain.plan_and_execute(cmd, self.controller)

    def start(self):
        """Starts the JARVIS HUD display and main voice monitoring loop."""
        self.hud.status = "CALIBRATING"
        self.hud.add_log("System Boot", "Voice monitor & full access online")
        self.voice.speak("J.A.R.V.I.S. online. Speak 'Jarvis' followed by your command, sir.", async_mode=True)
        
        calibrated_energy = self.listener.calibrate(1.0)
        self.hud.add_log("Mic Ready", f"Listening for 'Jarvis...' (floor: {int(calibrated_energy)})")
        self.hud.status = "LISTENING"

        # Background telemetry updater thread
        def _telemetry_loop():
            while self.running:
                try:
                    self.last_telemetry = self.controller.get_system_diagnostics()
                except Exception:
                    pass
                time.sleep(2.0)

        t_telemetry = threading.Thread(target=_telemetry_loop, daemon=True)
        t_telemetry.start()

        # Keyboard input thread (supports typed commands directly)
        def _keyboard_input_loop():
            while self.running:
                try:
                    user_text = sys.stdin.readline()
                    if user_text and user_text.strip():
                        typed_cmd = user_text.strip()
                        self.hud.last_command = f"[Typed] {typed_cmd}"
                        self.hud.status = "PROCESSING"
                        response = self.process_command(typed_cmd)
                        self.hud.last_response = response
                        self.hud.add_log(f"Typed: {typed_cmd}", response[:40])
                        self.hud.status = "SPEAKING"
                        self.voice.speak(response)
                        if not self.running:
                            break
                        self.hud.status = "LISTENING"
                except Exception:
                    break

        t_keyboard = threading.Thread(target=_keyboard_input_loop, daemon=True)
        t_keyboard.start()

        try:
            with Live(self.hud.generate_layout(self.last_telemetry), refresh_per_second=10) as live:
                while self.running:
                    # Update VU meter and telemetry continuously
                    self.hud.audio_level = self.listener.current_level
                    live.update(self.hud.generate_layout(self.last_telemetry))

                    # Listen for spoken audio with short non-blocking timeouts
                    spoken = self.listener.listen_command(timeout=1.2, phrase_time_limit=7.0)

                    if spoken:
                        self.hud.last_command = spoken
                        live.update(self.hud.generate_layout(self.last_telemetry))

                        # 1. Check for wake word 'Jarvis'
                        has_wake, command_body = check_wake_word(spoken)
                        
                        if not has_wake:
                            self.hud.status = "IGNORED (NO 'JARVIS')"
                            self.hud.add_log(f"Heard: {spoken[:25]}", "Ignored: Missing 'Jarvis'")
                            live.update(self.hud.generate_layout(self.last_telemetry))
                            time.sleep(0.4)
                            self.hud.status = "LISTENING"
                            continue

                        # 2. Wake word present -> process command
                        self.hud.status = "PROCESSING"
                        live.update(self.hud.generate_layout(self.last_telemetry))

                        response = self.process_command(command_body if command_body else spoken)
                        self.hud.last_response = response
                        self.hud.add_log(f"Voice: {spoken[:25]}", response[:40])

                        self.hud.status = "SPEAKING"
                        live.update(self.hud.generate_layout(self.last_telemetry))

                        self.voice.speak(response)
                        if not self.running:
                            break
                        self.hud.status = "LISTENING"
                        live.update(self.hud.generate_layout(self.last_telemetry))

                    time.sleep(0.04)
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.listener.close()
            self.voice.speak("Systems powering down. Goodbye, sir.")

if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.start()

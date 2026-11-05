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

try:
    from jarvis.voice import JarvisVoice
    from jarvis.controller import SystemController
    from jarvis.listener import VoiceListener
    from jarvis.monitor import JarvisHUD
    from jarvis.brain import JarvisBrain
    from jarvis.learning.experience_recorder import ExperienceRecorder
    from jarvis.retrieval.dataset_retriever import DatasetRetriever
except ImportError:
    from voice import JarvisVoice
    from controller import SystemController
    from listener import VoiceListener
    from monitor import JarvisHUD
    from brain import JarvisBrain
    from learning.experience_recorder import ExperienceRecorder
    from retrieval.dataset_retriever import DatasetRetriever

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
        self.experience = ExperienceRecorder(authorized=True)
        self.retriever = DatasetRetriever()
        self.running = True
        self.last_telemetry = self.controller.get_system_diagnostics()
        self.active_flow_expiry = 0.0
        self.flow_timeout_seconds = 25.0

    def process_command(self, cmd: str) -> str:
        """Processes command using the autonomous brain & experience recorder."""
        clean = cmd.lower().strip()
        
        # Stop / Shutdown commands
        if any(w in clean for w in [
            "shutdown", "goodbye", "exit", "quit", "terminate",
            "stop jarvis", "pause jarvis", "turn off", "power down",
            "close yourself"
        ]) or clean == "stop":
            self.running = False
            return "Powering down systems. Have a good evening, sir."

        # 1. Detect user corrections / preference updates
        correction = self.experience.detect_and_apply_correction(clean)
        if correction:
            pref_msg = f"Understood, sir. I have saved your preference: whenever you say '{correction['trigger']}', I will use '{correction['target']}'."
            self.experience.record_interaction(
                instruction=cmd,
                intent="preference_update",
                steps=[{"tool": "save_preference", "arguments": {"trigger": correction["trigger"], "target": correction["target"]}}],
                outcome=pref_msg,
                verified=True,
                verification_evidence=["user_preference_saved"]
            )
            return pref_msg

        # 2. Plan and execute via brain
        response = self.brain.plan_and_execute(cmd, self.controller)

        # 3. Record interaction in autonomous experience dataset
        is_success = "error" not in response.lower() and "failed" not in response.lower() and "sorry" not in response.lower()
        self.experience.record_interaction(
            instruction=cmd,
            intent="desktop_task",
            steps=[],
            outcome=response,
            verified=is_success,
            verification_evidence=["action_executed" if is_success else "execution_failed"]
        )

        return response

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

                    # Listen for spoken audio with conversational flow limits (phrase_time_limit up to 25s)
                    spoken = self.listener.listen_command(timeout=1.5, phrase_time_limit=25.0)

                    if spoken:
                        self.hud.last_command = spoken
                        live.update(self.hud.generate_layout(self.last_telemetry))

                        # 1. Check for wake word 'Jarvis' or ongoing active flow session
                        has_wake, command_body = check_wake_word(spoken)
                        is_active_flow = time.time() < self.active_flow_expiry

                        if not has_wake and not is_active_flow:
                            self.hud.status = "IGNORED (NO 'JARVIS')"
                            self.hud.add_log(f"Heard: {spoken[:25]}", "Ignored: Missing 'Jarvis'")
                            live.update(self.hud.generate_layout(self.last_telemetry))
                            time.sleep(0.3)
                            self.hud.status = "LISTENING"
                            continue

                        # Active flow control: exit flow on dismissive phrases
                        if any(phrase in spoken.lower() for phrase in ["that's all", "that is all", "done for now", "nevermind"]):
                            self.active_flow_expiry = 0.0
                            self.voice.speak("Standing by, sir.", async_mode=True)
                            self.hud.status = "LISTENING"
                            live.update(self.hud.generate_layout(self.last_telemetry))
                            continue

                        # Extend active flow window (25s) so user can talk naturally without repeating 'Jarvis'
                        self.active_flow_expiry = time.time() + self.flow_timeout_seconds

                        effective_cmd = command_body if (has_wake and command_body) else spoken

                        # 2. Process command
                        self.hud.status = "PROCESSING"
                        live.update(self.hud.generate_layout(self.last_telemetry))

                        response = self.process_command(effective_cmd)
                        self.hud.last_response = response
                        self.hud.add_log(f"Voice: {effective_cmd[:25]}", response[:40])

                        self.hud.status = "SPEAKING"
                        live.update(self.hud.generate_layout(self.last_telemetry))

                        self.voice.speak(response)
                        if not self.running:
                            break
                        self.hud.status = "LISTENING (ACTIVE FLOW)"
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

"""
JARVIS Voice Synthesis Module
Thread-safe text-to-speech output using Windows SAPI.
"""

import threading
import win32com.client
import pythoncom

class JarvisVoice:
    def __init__(self, voice_name_hint="David", rate=1, volume=100):
        self.voice_name_hint = voice_name_hint
        self.rate = rate
        self.volume = volume
        self._lock = threading.Lock()

    def speak(self, text: str, async_mode: bool = False):
        """Speaks the text aloud in a thread-safe manner."""
        if not text:
            return

        def _do_speak():
            with self._lock:
                try:
                    pythoncom.CoInitialize()
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Rate = self.rate
                    speaker.Volume = self.volume
                    
                    # Try finding matching voice
                    for v in speaker.GetVoices():
                        if self.voice_name_hint.lower() in v.GetDescription().lower():
                            speaker.Voice = v
                            break
                    
                    speaker.Speak(text)
                except Exception as e:
                    print(f"[Voice Error] {e}")
                finally:
                    try:
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        if async_mode:
            t = threading.Thread(target=_do_speak, daemon=True)
            t.start()
        else:
            _do_speak()

if __name__ == "__main__":
    v = JarvisVoice()
    v.speak("JARVIS voice synthesis initialized and ready, sir.")


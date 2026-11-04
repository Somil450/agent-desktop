"""
JARVIS Voice Monitor & Listener Module
Powered by PyAudio and SpeechRecognition with real-time VU meter streaming
and automatic ambient noise calibration.
"""

import time
import math
import struct
import threading
import speech_recognition as sr
import pyaudio

class VoiceListener:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.non_speaking_duration = 0.5
        
        self.current_level = 0.0  # 0.0 to 1.0 for VU meter
        self.status = "IDLE"
        self._running = True

        # PyAudio for live VU level monitoring
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self._start_vu_meter_thread()

    def _start_vu_meter_thread(self):
        """Continuously reads audio chunks to drive the live HUD VU meter."""
        def _meter_loop():
            try:
                self.stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=1024
                )
                while self._running:
                    try:
                        data = self.stream.read(1024, exception_on_overflow=False)
                        # Compute peak / RMS
                        count = len(data) // 2
                        shorts = struct.unpack(f"{count}h", data)
                        sum_squares = sum(s * s for s in shorts)
                        rms = math.sqrt(sum_squares / count) if count > 0 else 0
                        # Normalize: RMS 100-3000 to 0.0-1.0
                        self.current_level = min(1.0, max(0.0, rms / 1500.0))
                    except Exception:
                        pass
                    time.sleep(0.03)
            except Exception as e:
                pass

        t = threading.Thread(target=_meter_loop, daemon=True)
        t.start()

    def calibrate(self, duration=1.0):
        """Calibrates speech recognizer to current room ambient noise."""
        self.status = "CALIBRATING"
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            self.status = "ONLINE"
            return self.recognizer.energy_threshold
        except Exception:
            self.recognizer.energy_threshold = 300
            self.status = "ONLINE"
            return 300

    def listen_command(self, timeout=1.5, phrase_time_limit=8.0) -> str:
        """
        Listens for a spoken phrase with short non-blocking timeout.
        Returns the recognized string, or empty string if no speech detected.
        """
        self.status = "LISTENING"
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            self.status = "TRANSCRIBING"
            text = self.recognizer.recognize_google(audio)
            self.status = "ONLINE"
            return text.strip()
        except sr.WaitTimeoutError:
            # Silence during timeout period
            self.status = "LISTENING"
            return ""
        except sr.UnknownValueError:
            # Speech detected but could not be understood
            self.status = "LISTENING"
            return ""
        except sr.RequestError as e:
            self.status = "ONLINE"
            return ""
        except Exception as e:
            self.status = "ONLINE"
            return ""

    def close(self):
        self._running = False
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.pa.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    vl = VoiceListener()
    print("Calibrating...")
    vl.calibrate(1.0)
    print("Ready. Speak now:")
    for _ in range(5):
        txt = vl.listen_command(timeout=3)
        if txt:
            print("Heard:", txt)
            break
        else:
            print(f"Listening... Level: {vl.current_level:.2f}")
    vl.close()

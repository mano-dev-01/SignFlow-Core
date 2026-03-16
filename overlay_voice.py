import os
import time

from PyQt5.QtCore import QThread, pyqtSignal


def _safe_import(module_name: str):
    try:
        return __import__(module_name)
    except Exception:  # pragma: no cover - optional dependency
        return None


class VoiceToTextWorker(QThread):
    text_updated = pyqtSignal(str)
    partial_updated = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, language: str = "en-US", parent=None):
        super().__init__(parent)
        self._language = language
        self._running = True
        self._stop_requested = False

    def stop(self):
        self._running = False
        self._stop_requested = True
        self.wait(700)

    def run(self):
        speech_recognition = _safe_import("speech_recognition")
        if speech_recognition is None:
            print("[Voice] SpeechRecognition import failed.")
            self.error.emit("SpeechRecognition is missing. Install SpeechRecognition + PyAudio.")
            return
        print("[Voice] SpeechRecognition imported.")

        sr = speech_recognition
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.3
        recognizer.non_speaking_duration = 0.3

        try:
            mic_index = None
            mic_index_env = os.getenv("SIGNFLOW_MIC_INDEX")
            if mic_index_env is not None and mic_index_env.strip():
                try:
                    mic_index = int(mic_index_env.strip())
                except ValueError:
                    mic_index = None
            mic_names = []
            try:
                mic_names = sr.Microphone.list_microphone_names()
            except Exception:
                mic_names = []
            if mic_names:
                print("[Voice] Microphones:")
                for idx, name in enumerate(mic_names):
                    print(f"[Voice]   {idx}: {name}")
            microphone = sr.Microphone(device_index=mic_index)
        except Exception as exc:
            print(f"[Voice] Microphone init failed: {exc}")
            self.error.emit(f"Failed to start microphone: {exc}")
            return
        print("[Voice] Microphone initialized.")

        engine = os.getenv("SIGNFLOW_STT_ENGINE", "google").strip().lower()
        print(f"[Voice] Engine selected: {engine}")
        self.status_updated.emit("listening")

        with microphone as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
            except Exception:
                pass
            print("[Voice] Listening loop started.")

            while self._running and not self._stop_requested:
                try:
                    audio = recognizer.listen(source, timeout=1.0, phrase_time_limit=6.0)
                    print("[Voice] Audio captured.")
                except sr.WaitTimeoutError:
                    continue
                except Exception as exc:
                    print(f"[Voice] Microphone error: {exc}")
                    self.error.emit(f"Microphone error: {exc}")
                    return

                text = ""
                try:
                    if engine == "sphinx":
                        text = recognizer.recognize_sphinx(audio)
                    else:
                        result = recognizer.recognize_google(audio, language=self._language, show_all=True)
                        if isinstance(result, dict):
                            alternatives = result.get("alternative", []) or []
                            if alternatives:
                                top = alternatives[0]
                                text = str(top.get("transcript", "") or "")
                                conf = top.get("confidence")
                                if conf is not None:
                                    print(f"[Voice] Confidence: {conf}")
                        else:
                            text = str(result or "")
                except sr.UnknownValueError:
                    text = ""
                except sr.RequestError:
                    text = ""
                    # Keep listening; network issues should not hard-stop voice mode.
                except Exception as exc:
                    print(f"[Voice] Speech error: {exc}")
                    self.error.emit(f"Speech error: {exc}")
                    return

                clean = str(text or "").strip()
                if clean:
                    print(f"[Voice] Recognized: {clean}")
                    self.text_updated.emit(clean)
                else:
                    print("[Voice] No speech recognized.")

                time.sleep(0.01)

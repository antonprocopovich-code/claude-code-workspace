#!/usr/bin/env python3
"""VoiceType — локальный голосовой ввод на macOS (Whisper small)"""

import threading
import time
import subprocess
import sys
import numpy as np

try:
    import rumps
    import sounddevice as sd
    import whisper
    import pyperclip
    from pynput import keyboard
except ImportError as e:
    print(f"Отсутствует зависимость: {e}")
    print("Запусти: pip3 install -r requirements.txt")
    sys.exit(1)


SAMPLE_RATE = 16000       # Hz — Whisper требует 16kHz
MODEL_SIZE  = "small"     # tiny / base / small / medium / large
LANGUAGE    = "ru"        # язык транскрипции (None = авто-определение)

# Горячая клавиша: Option + Space
HOTKEY = {keyboard.Key.alt, keyboard.Key.space}


class VoiceTypeApp(rumps.App):
    def __init__(self):
        super().__init__("🎤", quit_button="Выйти")

        self.model       = None
        self.is_recording = False
        self.audio_frames = []
        self._lock        = threading.Lock()

        self._status_item = rumps.MenuItem("Загрузка модели Whisper…")
        self._hotkey_item = rumps.MenuItem("Горячая клавиша: Option + Space")
        self._toggle_item = rumps.MenuItem("Начать запись", callback=self._on_toggle)

        self.menu = [
            self._status_item,
            self._hotkey_item,
            None,
            self._toggle_item,
        ]

        threading.Thread(target=self._load_model, daemon=True).start()
        self._start_hotkey_listener()

    # ------------------------------------------------------------------ model

    def _load_model(self):
        self.title = "⏳"
        try:
            self.model = whisper.load_model(MODEL_SIZE)
            self.title = "🎤"
            self._status_item.title = f"Модель: whisper-{MODEL_SIZE} ✓"
        except Exception as exc:
            self.title = "❌"
            self._status_item.title = f"Ошибка модели: {exc}"

    # --------------------------------------------------------------- hotkey

    def _start_hotkey_listener(self):
        pressed = set()

        def on_press(key):
            pressed.add(key)
            if HOTKEY.issubset(pressed):
                self._on_toggle(None)

        def on_release(key):
            pressed.discard(key)

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.daemon = True
        listener.start()

    # --------------------------------------------------------------- toggle

    def _on_toggle(self, _):
        with self._lock:
            if self.model is None:
                rumps.notification("VoiceType", "", "Модель ещё загружается, подождите")
                return
            if not self.is_recording:
                self._start_recording()
            else:
                self._stop_and_transcribe()

    # ------------------------------------------------------------- recording

    def _start_recording(self):
        self.is_recording  = True
        self.audio_frames  = []
        self.title         = "🔴"
        self._toggle_item.title = "Остановить запись"

        def _record():
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
                while self.is_recording:
                    chunk, _ = stream.read(1024)
                    self.audio_frames.append(chunk.copy())

        threading.Thread(target=_record, daemon=True).start()

    def _stop_and_transcribe(self):
        self.is_recording       = False
        self.title              = "⏳"
        self._toggle_item.title = "Начать запись"
        threading.Thread(target=self._transcribe, daemon=True).start()

    # --------------------------------------------------------- transcription

    def _transcribe(self):
        # нужно хотя бы ~0.5 сек аудио (≈7 чанков по 1024)
        if len(self.audio_frames) < 7:
            self.title = "🎤"
            return

        try:
            audio  = np.concatenate(self.audio_frames, axis=0).flatten()
            result = self.model.transcribe(audio, language=LANGUAGE, fp16=False)
            text   = result["text"].strip()

            if text:
                self._paste_text(text)
                rumps.notification("VoiceType", "Вставлено", text[:120])
            else:
                rumps.notification("VoiceType", "", "Текст не распознан")
        except Exception as exc:
            rumps.notification("VoiceType", "Ошибка транскрипции", str(exc))
        finally:
            self.title = "🎤"

    # -------------------------------------------------------------- paste

    def _paste_text(self, text: str):
        """Копирует текст в буфер и симулирует Cmd+V в активное окно."""
        try:
            original = pyperclip.paste()
        except Exception:
            original = ""

        pyperclip.copy(text)
        time.sleep(0.05)  # даём буферу обновиться

        subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to keystroke "v" using {command down}'],
            capture_output=True,
        )

        # возвращаем исходный буфер после вставки
        time.sleep(0.2)
        pyperclip.copy(original)


if __name__ == "__main__":
    VoiceTypeApp().run()

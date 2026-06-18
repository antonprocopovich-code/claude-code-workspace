#!/usr/bin/env python3
"""
Push-to-talk голосовой ввод.
Зажми Right Option (⌥ правый) → говори → отпусти → текст вставится.
Остановка: Ctrl+C
"""

import subprocess
import tempfile
import os
import wave
import threading
import pyaudio
import whisper
from pynput import keyboard

HOTKEY = keyboard.Key.alt_r   # правый Option — меняй если нужно
MIC_INDEX = 1
SAMPLE_RATE = 16000
CHUNK = 1024

model = None
recording = False
frames = []
stream = None
audio = None

def load_model():
    global model
    print("Загружаю модель Whisper...")
    model = whisper.load_model("medium")
    print("Готово. Зажми правый ⌥ Option и говори.\n")

def start_recording():
    global recording, frames, stream, audio
    if recording:
        return
    recording = True
    frames = []
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=MIC_INDEX,
        frames_per_buffer=CHUNK,
    )
    print("🔴 Запись...", end=" ", flush=True)

    def record():
        while recording:
            frames.append(stream.read(CHUNK, exception_on_overflow=False))

    threading.Thread(target=record, daemon=True).start()

def stop_recording():
    global recording, stream, audio
    if not recording:
        return
    recording = False
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("⏹ Обрабатываю...", end=" ", flush=True)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name

    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))

    result = model.transcribe(tmp_path, language="ru")
    text = result["text"].strip()
    os.unlink(tmp_path)

    if text:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to keystroke "v" using command down'
        ], check=True)
        print(f"→ {text}")
    else:
        print("(тихо)")

def on_press(key):
    if key == HOTKEY:
        start_recording()

def on_release(key):
    if key == HOTKEY:
        stop_recording()

load_model()

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        print("\nОстановлено.")

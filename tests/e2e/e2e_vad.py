"""E2E: VadManager erkennt Sprache in hello.wav und keine in silence.wav.

Aufruf: PYTHONPATH=src .venv/bin/python tests/e2e/e2e_vad.py ~/wk-e2e/hello.wav ~/wk-e2e/silence.wav
"""
import sys
import wave

import numpy as np

from whisper_key.voice_activity_detection import VadManager


def load_wav(path):
    with wave.open(path, 'rb') as w:
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def main():
    speech, silence = load_wav(sys.argv[1]), load_wav(sys.argv[2])
    vad = VadManager(vad_precheck_enabled=True)
    if not vad.is_available():
        print("VAD SKIP: ten-vad nicht verfuegbar (Fallback aktiv)")
        return
    assert vad.check_audio_for_speech(speech) is True, "Sprache nicht erkannt"
    assert vad.check_audio_for_speech(silence) is False, "Stille als Sprache erkannt"
    print("VAD OK")


if __name__ == "__main__":
    main()

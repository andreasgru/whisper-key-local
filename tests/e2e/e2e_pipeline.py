"""E2E: say-WAV -> WhisperEngine (CPU int8) -> Transkript.

Aufruf auf dem Mac:
PYTHONPATH=src .venv/bin/python tests/e2e/e2e_pipeline.py ~/wk-e2e/hello.wav
"""
import sys
import wave

import numpy as np

from whisper_key.whisper_engine import WhisperEngine


def load_wav(path):
    with wave.open(path, 'rb') as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def main():
    audio = load_wav(sys.argv[1])
    engine = WhisperEngine(model_key="base", device="cpu", compute_type="int8")
    engine._load_model()
    text = engine.transcribe_audio(audio)
    print(f"Transkript: {text!r}")
    assert text, "kein Transkript"
    lower = text.lower()
    for word in ("quick", "brown", "fox"):
        assert word in lower, f"'{word}' fehlt in: {text!r}"
    print("PIPELINE OK")


if __name__ == "__main__":
    main()

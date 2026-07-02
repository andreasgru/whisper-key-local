"""E2E: MlxWhisperEngine (GPU) — Laden, Transkription, Latenz, Modellwechsel.

Aufruf auf dem Mac:
PYTHONPATH=src .venv/bin/python tests/e2e/e2e_mlx_engine.py ~/wk-e2e/german.wav
"""
import sys
import time
import wave

import numpy as np

from whisper_key.whisper_engine_mlx import MlxWhisperEngine, is_mlx_available


def load_wav(path):
    with wave.open(path, 'rb') as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def main():
    assert is_mlx_available(), "mlx-whisper nicht installiert"
    audio = load_wav(sys.argv[1])
    duration = len(audio) / 16000

    engine = MlxWhisperEngine(model_key="large-v3-turbo", language="de")
    engine.transcribe_audio(audio[:16000 * 3])  # warmup

    t0 = time.time()
    text = engine.transcribe_audio(audio)
    dt = time.time() - t0
    print(f"Transkript ({dt:.2f}s fuer {duration:.0f}s Audio): {text[:120]!r}")
    assert text and "Quarz" in text, f"Transkript unerwartet: {text[:80]!r}"
    assert dt < duration / 4, f"zu langsam fuer GPU: {dt:.2f}s"

    preview = engine.transcribe_preview(audio[:16000 * 10])
    assert preview, "Preview leer"
    print(f"Preview ok: {preview[:60]!r}")

    done = []
    engine.change_model("small", progress_callback=lambda m: done.append(m))
    while engine.is_loading():
        time.sleep(0.2)
    assert engine.model_key == "small", f"Modellwechsel fehlgeschlagen: {done}"
    text2 = engine.transcribe_audio(audio[:16000 * 10])
    assert text2, "Transkription nach Modellwechsel leer"
    print(f"Modellwechsel ok ({done[-1] if done else '?'}): {text2[:60]!r}")

    engine.change_model("nicht-existent", progress_callback=lambda m: done.append(m))
    assert engine.model_key == "small", "unmapped key haette ignoriert werden muessen"
    print("MLX ENGINE E2E OK")


if __name__ == "__main__":
    main()

"""E2E: openWakeWord laedt und verarbeitet Audio-Chunks ohne Fehler.

TTS triggert Wake-Modelle nicht zuverlaessig -> Score wird geloggt,
harte Assertion nur auf Lauffaehigkeit.

Aufruf: PYTHONPATH=src .venv/bin/python tests/e2e/e2e_wakeword.py ~/wk-e2e/hello.wav
"""
import sys
import wave

import numpy as np


def main():
    try:
        from openwakeword.model import Model as OwwModel
    except ImportError:
        print("WAKEWORD SKIP: openwakeword nicht installiert")
        return
    import openwakeword
    from whisper_key.wake_word import _ensure_tflite_runtime
    openwakeword.utils.download_models()
    framework = "tflite" if _ensure_tflite_runtime() else "onnx"
    print(f"framework: {framework}")
    model = OwwModel(inference_framework=framework)
    with wave.open(sys.argv[1], 'rb') as w:
        raw = w.readframes(w.getnframes())
    audio = np.frombuffer(raw, dtype=np.int16)
    scores = []
    for i in range(0, len(audio) - 1280, 1280):
        pred = model.predict(audio[i:i + 1280])
        scores.append(max(pred.values()) if pred else 0.0)
    assert scores, "keine Chunks verarbeitet"
    print(f"WAKEWORD OK: {len(scores)} chunks, max score {max(scores):.3f}")


if __name__ == "__main__":
    main()

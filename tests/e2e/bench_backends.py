"""Benchmark: Whisper-Backends auf Apple Silicon gegeneinander.

Läuft auf dem Mac in ~/wk-bench/.venv (mlx-whisper, parakeet-mlx, faster-whisper).
Aufruf: .venv/bin/python bench_backends.py <backend> <wav> [runs]
Backends: faster-whisper | mlx-whisper | mlx-whisper-small | parakeet
Misst: Ladezeit (einmalig), warme Transkriptionszeit (Median über runs, Default 3).
Ausgabe: eine JSON-Zeile pro Lauf -> maschinenlesbar fürs Sammeln.
"""
import json
import statistics
import sys
import time

WAV = sys.argv[2]
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
backend = sys.argv[1]


def emit(name, load_s, times, text):
    print(json.dumps({
        "backend": name,
        "load_s": round(load_s, 2),
        "median_s": round(statistics.median(times), 2),
        "runs": [round(t, 2) for t in times],
        "text": text[:220],
    }, ensure_ascii=False))


def bench_faster_whisper():
    import wave
    import numpy as np
    from faster_whisper import WhisperModel
    with wave.open(WAV, "rb") as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    t0 = time.time()
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    load_s = time.time() - t0
    times, text = [], ""
    list(m.transcribe(audio[:16000 * 3], language="de", beam_size=5)[0])  # warmup
    for _ in range(RUNS):
        t0 = time.time()
        segs, _ = m.transcribe(audio, language="de", beam_size=5)
        text = "".join(s.text for s in segs).strip()
        times.append(time.time() - t0)
    emit("faster-whisper-turbo-cpu-int8", load_s, times, text)


def _load_wav_f32(path):
    import wave
    import numpy as np
    with wave.open(path, "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def bench_mlx(repo, label):
    import mlx_whisper
    audio = _load_wav_f32(WAV)  # ffmpeg umgehen: Array direkt uebergeben
    times, text = [], ""
    t0 = time.time()
    text = mlx_whisper.transcribe(audio, path_or_hf_repo=repo, language="de")["text"]
    load_s = time.time() - t0  # inkl. erster Transkription (Modell-Load + Compile)
    for _ in range(RUNS):
        t0 = time.time()
        text = mlx_whisper.transcribe(audio, path_or_hf_repo=repo, language="de")["text"]
        times.append(time.time() - t0)
    emit(label, load_s, times, text.strip())


def bench_parakeet():
    from parakeet_mlx import from_pretrained
    t0 = time.time()
    m = from_pretrained("mlx-community/parakeet-tdt-0.6b-v3")
    load_s = time.time() - t0
    m.transcribe(WAV)  # warmup
    times, text = [], ""
    for _ in range(RUNS):
        t0 = time.time()
        result = m.transcribe(WAV)
        text = result.text.strip()
        times.append(time.time() - t0)
    emit("parakeet-tdt-0.6b-v3-mlx", load_s, times, text)


if backend == "faster-whisper":
    bench_faster_whisper()
elif backend == "mlx-whisper":
    bench_mlx("mlx-community/whisper-large-v3-turbo", "mlx-whisper-turbo")
elif backend == "mlx-whisper-small":
    bench_mlx("mlx-community/whisper-small-mlx", "mlx-whisper-small")
elif backend == "parakeet":
    bench_parakeet()
else:
    sys.exit(f"unbekanntes backend: {backend}")

# Whisper-Backend-Benchmark auf dem Mac M5 Max

**Datum:** 2026-07-02 · **Frage:** Welches GPU-/ANE-beschleunigte Backend ersetzt
faster-whisper-CPU auf dem Mac? · **Harness:** `tests/e2e/bench_backends.py` +
whisper-cli/whisperkit-cli · **Testaudio:** Gesprochene Wikipedia „Quarz" (60 s,
echte Sprecherin, de) + `say`-Satz (~4 s, de) · Median aus 3 warmen Läufen, `language=de`.

## Ergebnis

| Backend | Modell | 60 s Audio | ~4 s Satz | vs. CPU | Deutsch-Qualität |
|---|---|---|---|---|---|
| faster-whisper (CPU int8) | large-v3-turbo | 14,98 s | 3,98 s | 1× | fehlerfrei |
| WhisperKit 1.0 (ANE/CoreML) | large-v3-v20240930_turbo | ~8,4 s¹ | – | ~1,8× | fehlerfrei, ab Mitte Groß-/Kleinschreibung defekt |
| whisper.cpp + Metal (6fc7c33) | ggml-large-v3-turbo | 1,32 s | 0,50 s | 11× | fehlerfrei |
| **mlx-whisper 0.4.x** | **large-v3-turbo** | **0,64 s** | **0,10 s** | **23–40×** | **fehlerfrei** |
| mlx-whisper | small | 0,67 s | – | – | leichte Fehler („Quartz") |
| parakeet-mlx | parakeet-tdt-0.6b-v3 | **0,44 s** | **0,07 s** | 34–57× | gut, leichte Schwächen² |

¹ encoding 1,6 s + decodingLoop 6,8 s laut Report-JSON; Prozess-Wandzeit 12–15 s
  (Modell-Load pro Aufruf). Report-Werte teils inkonsistent (fullPipeline 2,4 s).
² „Enzyklopäd" abgeschnitten, „vage Wörterkennung" statt „Wake-Word-Erkennung"
  (TTS-Testsatz); Whisper-turbo-Backends waren hier korrekt.

## Interpretation

- **MLX gewinnt klar** — die Neural Accelerators in den M5-GPU-Kernen beschleunigen
  den compute-lastigen Whisper-Encoder massiv (passt zu Apples MLX-M5-Zahlen).
- **mlx-whisper small lohnt nicht:** turbo ist gleich schnell und besser — auf MLX
  immer turbo nehmen.
- **whisper.cpp/Metal** ist solide (11×), aber halb so schnell wie MLX und als
  C++-CLI/Server schwerer zu integrieren als die Python-Lib.
- **WhisperKit/ANE enttäuscht auf dem M5:** Die ANE wurde nicht wie die GPU
  aufgerüstet; zudem hoher Prozess-Start-Overhead. (Auf M3/M4 laut Literatur
  konkurrenzfähiger.)
- **parakeet-tdt-0.6b-v3 (MLX)** ist das absolut schnellste Backend und kann
  Deutsch (25 EU-Sprachen), Qualität leicht unter Whisper-turbo. Interessant für
  Realtime-Preview (Streaming), weniger als Haupt-Transkribierer.
- **MetalRT** (RunAnywhere) bewirbt 714× Echtzeit, ist aber proprietär ohne
  öffentlichen Installationsweg → nicht testbar.

## Empfehlung für whisper-key

**mlx-whisper mit large-v3-turbo als macOS-Engine-Backend integrieren** (hinter
der bestehenden `WhisperEngine`-Abstraktion, faster-whisper bleibt Fallback/
Windows-Pfad). Damit fällt die Diktat-Latenz von 4–7 s auf ~0,1–0,3 s pro Satz
bei bester Qualität. Optional später: parakeet-mlx für den Realtime-Preview-Stream
(`transcribe_preview`), da nochmal 1,5× schneller.

## Setup-Referenz (Mac)

- Bench-venv: `~/wk-bench/.venv` (uv-Python 3.12): mlx-whisper, parakeet-mlx,
  faster-whisper, cmake; statisches ffmpeg in `~/wk-bench/` (nur parakeet braucht es)
- whisper.cpp: `~/wk-bench/whisper.cpp` (Metal-Build via venv-cmake),
  Modelle in `~/wk-bench/models/` (ggml-large-v3-turbo, ggml-small)
- WhisperKit: `brew install whisperkit-cli` (ghcr.io ist vom Mac erreichbar!)
- MLX-Modelle im HF-Cache: mlx-community/{whisper-large-v3-turbo, whisper-small-mlx, parakeet-tdt-0.6b-v3}
- Stolperfallen: Mac-Leitung ~1 MB/s (Downloads brechen ab → curl-Retry/Resume);
  mlx-whisper/parakeet wollen ffmpeg (mlx-whisper umgangen via numpy-Array-Input)

## Quellen

- [mac-whisper-speedtest (anvanvan)](https://github.com/anvanvan/mac-whisper-speedtest) — Vergleichsharness, M4-Zahlen
- [MetalRT-Behauptungen (RunAnywhere/HF-Blog)](https://huggingface.co/blog/runanywhere/metalrt-fastest-inference-apple-silicon)
- [Apple MLR: LLMs mit MLX auf M5-Neural-Accelerators](https://machinelearning.apple.com/research/exploring-llms-mlx-m5)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) · [WhisperKit](https://github.com/argmaxinc/argmax-oss-swift)
- Benchmarks Dritter: [JustVoice M1–M4](https://justvoice.ai/blog/whisper-benchmark-apple-silicon-m3-m4), [PromptQuorum whisper.cpp vs faster-whisper](https://www.promptquorum.com/power-local-llm/local-whisper-stt-comparison-2026)

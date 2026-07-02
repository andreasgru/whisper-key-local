# Backlog: whisper-key-local (Fork andreasgru)

## Erledigt

- **2026-07-02: macOS-Port (Branch `feature/macos-port`)**
  - Tag `pre-upstream-merge-20260702` auf local_master
  - Upstream v0.8.2 gemergt (Stop-Key-Fix, Text-Corrections, Console-Mgmt, …)
  - Overlay hinter Platform-Abstraktion: Windows tkinter / macOS natives NSPanel (pyobjc)
  - Echte macOS-Monitor-Implementierung (NSScreen/Quartz, Top-Left-normiert)
  - Bugfixes: log_transcriptions-Merge-Regression; TEN-VAD 256er-Hop-Pflicht (macOS-Build);
    openWakeWord-ONNX-Null-Scores auf arm64 (→ tflite via ai-edge-litert, oww-Issue #336);
    Wake-Word-VAD-Pre-Filter verlor Phrasen-Anfang (→ Pre-Roll-Buffer, betrifft auch Windows)
  - Simulations-Abnahme: HTTP von außen, echtes Mikro + Deutsch (zeichengenau), Continuous,
    Wake-Word-Kette (Alexa-Clip score 1.000), Menu-Bar-Modellwechsel, Deutsch-Benchmark
    (Gesprochene Wikipedia: base 22×/small 8×/turbo 4× Echtzeit; Qualität: turbo ≫ small > base)
- **2026-07-02: mlx-whisper-GPU-Engine integriert** (`whisper.engine: auto|mlx|faster-whisper`)
  - Benchmark aller Backends (doc/research/2026-07-02-whisper-backend-benchmark-m5.md):
    mlx-whisper turbo 0,64s/60s; whisper.cpp Metal 1,3s; WhisperKit/ANE ~8s; parakeet 0,44s
  - `MlxWhisperEngine` mit identischem Interface; alle MLX-Ops auf dediziertem Thread
    (MLX-Streams sind thread-gebunden!); App-E2E: Transkription 0,32s statt 7,75s (CPU)
  - turbo ist damit uneingeschränkt der richtige Default am Mac
  - Automatisierte E2E-Suite `tests/e2e/` (say-TTS-Audio, Fake-Mic, HTTP-Zyklus) — alle grün
  - Deployment-Skript `tests/e2e/deploy_to_mac.sh` (rsync, GitHub am Mac SNI-geblockt)

## Offen

- [ ] Rest-Abnahme am Mac (nur noch: Hotkeys drücken, Auto-Paste am Cursor, Wake Word per echter Stimme, Overlay sichtbar) — Checkliste: `doc/plans/active/2026-07-02-macos-abnahme.md`
- [ ] Optional: parakeet-mlx als Realtime-Preview-Engine (nochmal ~1,5× schneller
      als mlx-whisper, Qualität leicht darunter — für Live-Preview egal)
- [ ] Windows-Regressionstest nach Overlay-Refactoring (tkinter-Code nur verschoben, ungetestet auf Windows)
- [ ] Porcupine-Wake-Word: Access Key besorgen, falls gewünscht (openWakeWord läuft ohne)
- [ ] Ggf. PR des macOS-Ports an Upstream (PinW) — VAD-Hop-Fix ist auch upstream-relevant

# Backlog: whisper-key-local (Fork andreasgru)

## Erledigt

- **2026-07-02: macOS-Port (Branch `feature/macos-port`)**
  - Tag `pre-upstream-merge-20260702` auf local_master
  - Upstream v0.8.2 gemergt (Stop-Key-Fix, Text-Corrections, Console-Mgmt, …)
  - Overlay hinter Platform-Abstraktion: Windows tkinter / macOS natives NSPanel (pyobjc)
  - Echte macOS-Monitor-Implementierung (NSScreen/Quartz, Top-Left-normiert)
  - Bugfixes: log_transcriptions-Merge-Regression; TEN-VAD 256er-Hop-Pflicht (macOS-Build)
  - Automatisierte E2E-Suite `tests/e2e/` (say-TTS-Audio, Fake-Mic, HTTP-Zyklus) — alle grün
  - Deployment-Skript `tests/e2e/deploy_to_mac.sh` (rsync, GitHub am Mac SNI-geblockt)

## Offen

- [ ] Manuelle Abnahme am Mac (Permissions, echte Hotkeys/Mikro, Overlay sichtbar) — Checkliste: `doc/plans/active/2026-07-02-macos-abnahme.md`
- [ ] Metal-/MLX-Whisper-Backend für M5 Max (faster-whisper läuft CPU-only; Kandidaten: mlx-whisper, whisper.cpp Metal). Motivation: large-v3-turbo braucht auf CPU 7,5s für 3,7s Audio (2× langsamer als Echtzeit); Default deshalb vorerst `small` (1,49s)
- [ ] Windows-Regressionstest nach Overlay-Refactoring (tkinter-Code nur verschoben, ungetestet auf Windows)
- [ ] Porcupine-Wake-Word: Access Key besorgen, falls gewünscht (openWakeWord läuft ohne)
- [ ] Ggf. PR des macOS-Ports an Upstream (PinW) — VAD-Hop-Fix ist auch upstream-relevant

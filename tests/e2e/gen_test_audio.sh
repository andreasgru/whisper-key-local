#!/usr/bin/env bash
# Erzeugt Testaudio auf dem Mac via say-TTS (kein Mikrofon noetig).
set -euo pipefail
OUT="${1:-$HOME/wk-e2e}"
mkdir -p "$OUT"
say -o "$OUT/hello.aiff" "The quick brown fox jumps over the lazy dog"
afconvert -f WAVE -d LEI16@16000 -c 1 "$OUT/hello.aiff" "$OUT/hello.wav"
python3 - "$OUT" <<'PY'
import sys, wave
out = sys.argv[1]
w = wave.open(f"{out}/silence.wav", "wb")
w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
w.writeframes(b"\x00\x00" * 16000 * 3)
w.close()
PY
echo "audio ok: $OUT"

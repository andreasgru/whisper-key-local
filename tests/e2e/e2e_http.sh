#!/usr/bin/env bash
# Auf dem Mac ausfuehren. Erwartet laufende App mit Fake-Mic (run_app_fake_mic.py).
set -euo pipefail
BASE="http://127.0.0.1:${WK_PORT:-5757}"

status=$(curl -sf "$BASE/status" | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
echo "status: $status"

curl -sf "$BASE/record" >/dev/null
sleep 6   # Fake-Mic spielt hello.wav (~3-4s) ein
text=$(curl -sf --max-time 120 "$BASE/stop" | python3 -c "import sys,json; print(json.load(sys.stdin).get('text',''))")
echo "transkript: $text"
echo "$text" | grep -qi "fox" || { echo "HTTP E2E FAIL: 'fox' fehlt"; exit 1; }

curl -sf "$BASE/toggle" >/dev/null   # startet Aufnahme
curl -sf "$BASE/cancel" | grep -q '"ok": *true' || { echo "cancel FAIL"; exit 1; }
echo "HTTP E2E OK"

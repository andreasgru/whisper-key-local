"""Smoke: Overlay erzeugen, Text setzen, zeigen, verstecken. Braucht WindowServer-Zugriff.

Aufruf: PYTHONPATH=src .venv/bin/python tests/e2e/e2e_overlay_smoke.py
"""
import threading
import time

from whisper_key.platform.macos import app as mac_app
from whisper_key.platform.macos.overlay import PreviewOverlay


def main():
    mac_app.setup()
    overlay = PreviewOverlay({'monitor': 'primary', 'position': 'bottom_center'})
    shutdown = threading.Event()
    errors = []

    def scenario():
        try:
            time.sleep(0.5)
            overlay.update_text("E2E Overlay Smoke Test")
            time.sleep(1.5)
            overlay.hide()
            time.sleep(0.5)
        except Exception as e:
            errors.append(e)
        finally:
            shutdown.set()

    threading.Thread(target=scenario, daemon=True).start()
    mac_app.run_event_loop(shutdown)
    assert not errors, f"Fehler im Szenario: {errors}"
    assert overlay._panels, "keine Panels erzeugt"
    print("OVERLAY SMOKE OK")


if __name__ == "__main__":
    main()

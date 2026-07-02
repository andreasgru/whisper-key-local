"""Startet whisper-key mit Fake-Mikrofon fuer HTTP-E2E (headless via SSH).

Aufruf: PYTHONPATH=src:tests/e2e .venv/bin/python tests/e2e/run_app_fake_mic.py ~/wk-e2e/hello.wav
"""
import sys

import fake_mic

fake_mic.install(sys.argv[1])
sys.argv = [sys.argv[0], '--test']

from whisper_key.main import main

main()

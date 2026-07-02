"""Monkeypatcht sounddevice: InputStream liefert silence+WAV in Endlosschleife.

MUSS vor dem ersten whisper_key-Import installiert werden (install(wav_path)).
"""
import threading
import time
import wave

import numpy as np
import sounddevice as sd

_audio = None


def install(wav_path):
    global _audio
    with wave.open(wav_path, 'rb') as w:
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    silence = np.zeros(rate // 2, dtype=np.float32)
    _audio = np.concatenate([silence, pcm, silence])

    sd.InputStream = _FakeInputStream
    sd.query_devices = _fake_query_devices
    sd.query_hostapis = lambda i=None: {'name': 'FakeCoreAudio'}


def _fake_query_devices(device=None, kind=None):
    return {'name': 'FakeMic', 'hostapi': 0, 'max_input_channels': 1,
            'default_samplerate': 16000.0, 'index': 0}


class _FakeInputStream:
    def __init__(self, samplerate=16000, channels=1, dtype='float32',
                 blocksize=512, device=None, callback=None, **kwargs):
        self._callback = callback
        self._blocksize = blocksize or 512
        self._rate = int(samplerate)
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()

    def _pump(self):
        pos = 0
        interval = self._blocksize / self._rate
        while self._running:
            chunk = np.zeros((self._blocksize, 1), dtype=np.float32)
            src = _audio[pos:pos + self._blocksize]
            chunk[:len(src), 0] = src
            pos = (pos + self._blocksize) % len(_audio)
            if self._callback:
                self._callback(chunk, self._blocksize, None, None)
            time.sleep(interval)

    def stop(self):
        self._running = False

    def close(self):
        self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *a):
        self.close()

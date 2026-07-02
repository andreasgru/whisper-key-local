"""MLX-Whisper-Engine fuer macOS/Apple Silicon.

Gleiches Public Interface wie WhisperEngine (faster-whisper), aber Inferenz
ueber mlx-whisper auf der GPU (M5-Neural-Accelerators). Benchmark M5 Max:
large-v3-turbo 0,64s/60s Audio bzw. 0,10s pro Satz = 23-40x schneller als
CPU-int8 (doc/research/2026-07-02-whisper-backend-benchmark-m5.md).

Kein Beam-Search (mlx-whisper dekodiert greedy) und keine hotwords —
beides wird mit Warnung ignoriert.
"""
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

import numpy as np

try:
    import mlx.core as mx
    import mlx_whisper
    from mlx_whisper.transcribe import ModelHolder
    HAS_MLX_WHISPER = True
except ImportError:
    mx = None
    mlx_whisper = None
    ModelHolder = None
    HAS_MLX_WHISPER = False

# whisper-key-Modell-Keys -> mlx-community-Repos (alle geprueft, 2026-07-02).
# Nicht gelistete Keys (distil-*, Custom-Sources) laufen weiter ueber faster-whisper.
MLX_MODEL_REPOS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "tiny.en": "mlx-community/whisper-tiny.en-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "base.en": "mlx-community/whisper-base.en-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "small.en": "mlx-community/whisper-small.en-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "medium.en": "mlx-community/whisper-medium.en-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
}


def is_mlx_available() -> bool:
    return HAS_MLX_WHISPER


def _is_repo_cached(repo: str) -> bool:
    cache = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface', 'hub')
    return os.path.exists(os.path.join(cache, "models--" + repo.replace("/", "--")))


class MlxWhisperEngine:
    def __init__(self,
                 model_key: str = "tiny",
                 device: str = "cpu",
                 compute_type: str = "int8",
                 language: str = None,
                 beam_size: int = 5,
                 initial_prompt: str = "",
                 hotwords: list = None,
                 vad_manager=None,
                 model_registry=None,
                 log_transcriptions: bool = False):

        if not HAS_MLX_WHISPER:
            raise ImportError("mlx-whisper is not installed")
        if model_key not in MLX_MODEL_REPOS:
            raise ValueError(f"No MLX repo mapping for model '{model_key}'")

        self.model_key = model_key
        self.language = None if language == 'auto' else language
        self.initial_prompt = initial_prompt or None
        self.log_transcriptions = log_transcriptions
        self.registry = model_registry
        self.vad_manager = vad_manager
        self.model = None  # wird nach erfolgreichem Load auf das MLX-Modell gesetzt

        self.logger = logging.getLogger(__name__)
        if beam_size and beam_size > 1:
            self.logger.info("mlx-whisper decodes greedily; beam_size is ignored")
        if hotwords:
            self.logger.warning("mlx-whisper does not support hotwords; ignoring")

        self._loading_thread = None
        self._transcribe_lock = threading.Lock()
        # MLX bindet Operationen an den Stream des ausfuehrenden Threads;
        # Laden und Inferenz MUESSEN deshalb auf demselben Thread laufen
        # ("There is no Stream(gpu, N) in current thread" sonst).
        self._mlx_thread = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mlx-engine")

        self._load_model()

    def _repo(self, model_key: str = None) -> str:
        return MLX_MODEL_REPOS[model_key or self.model_key]

    def _load_model(self):
        repo = self._repo()
        print(f"🧠 Loading Whisper AI model [{self.model_key}] (MLX/GPU)...")
        if not _is_repo_cached(repo):
            print("Downloading model, this may take a few minutes....")
        with self._transcribe_lock:
            self.model = self._mlx_thread.submit(ModelHolder.get_model, repo, mx.float16).result()
        print(f"   ✓ Whisper model [{self.model_key}] ready!")
        print("   ✓ Running on GPU (MLX, Apple Silicon)")

    def is_loading(self) -> bool:
        return self._loading_thread is not None and self._loading_thread.is_alive()

    def _transcribe(self, audio_data: np.ndarray, condition_on_previous_text: bool = True) -> Optional[str]:
        if len(audio_data.shape) > 1:
            audio_data = audio_data.flatten()
        audio_data = audio_data.astype(np.float32)

        kwargs = dict(
            path_or_hf_repo=self._repo(),
            language=self.language,
            condition_on_previous_text=condition_on_previous_text,
            verbose=None,
        )
        if self.initial_prompt:
            kwargs["initial_prompt"] = self.initial_prompt

        result = self._mlx_thread.submit(mlx_whisper.transcribe, audio_data, **kwargs).result()
        text = (result.get("text") or "").strip()
        return text if text else None

    def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        if self.model is None:
            return None

        if audio_data is None or len(audio_data) == 0:
            self.logger.warning("No audio data to transcribe")
            return None

        with self._transcribe_lock:
            try:
                speech_detected = True
                if self.vad_manager and self.vad_manager.is_available():
                    speech_detected = self.vad_manager.check_audio_for_speech(audio_data)

                if not speech_detected:
                    print("   ✗ No speech detected, skipping transcription")
                    return None

                start_time = time.time()
                text = self._transcribe(audio_data, condition_on_previous_text=False)
                transcription_time = time.time() - start_time
                print(f"   ✓ Transcription completed in {transcription_time:.1f} seconds")

                if not text:
                    self.logger.info("Transcription was empty")
                    return None

                if self.log_transcriptions:
                    self.logger.info(f"Transcribed text: '{text}'")
                else:
                    self.logger.info(f"Transcribed {len(text)} chars")
                self.logger.info(f"Transcription complete (MLX) - Time: {transcription_time:.2f}s")
                return text

            except Exception as e:
                self.logger.error(f"Transcription failed: {e}")
                return None

    def transcribe_preview(self, audio_data: np.ndarray) -> Optional[str]:
        if self.model is None:
            return None

        acquired = self._transcribe_lock.acquire(timeout=0.1)
        if not acquired:
            return None
        try:
            return self._transcribe(audio_data, condition_on_previous_text=False)
        except Exception as e:
            self.logger.error(f"Preview transcription failed: {e}")
            return None
        finally:
            self._transcribe_lock.release()

    def change_model(self,
                     new_model_key: str,
                     progress_callback: Optional[Callable[[str], None]] = None):
        if new_model_key == self.model_key:
            if progress_callback:
                progress_callback("Model already loaded")
            return

        if new_model_key not in MLX_MODEL_REPOS:
            msg = f"Model '{new_model_key}' has no MLX version; set whisper.engine: faster-whisper to use it"
            self.logger.warning(msg)
            if progress_callback:
                progress_callback(msg)
            return

        def _background_loader():
            old_key = self.model_key
            try:
                repo = self._repo(new_model_key)
                if progress_callback:
                    progress_callback("Loading cached model..." if _is_repo_cached(repo) else "Downloading model...")
                with self._transcribe_lock:
                    new_model = self._mlx_thread.submit(ModelHolder.get_model, repo, mx.float16).result()
                    self.model = new_model
                    self.model_key = new_model_key
                self.logger.info(f"MLX Whisper model [{new_model_key}] loaded successfully")
                if progress_callback:
                    progress_callback("Model ready!")
            except Exception as e:
                self.model_key = old_key
                self.logger.error(f"Failed to load MLX model: {e}")
                if progress_callback:
                    progress_callback(f"Failed to load model: {e}")
            finally:
                self._loading_thread = None

        if self._loading_thread and self._loading_thread.is_alive():
            self.logger.warning("Model loading already in progress, ignoring new request")
            return

        self._loading_thread = threading.Thread(target=_background_loader, daemon=True)
        self._loading_thread.start()

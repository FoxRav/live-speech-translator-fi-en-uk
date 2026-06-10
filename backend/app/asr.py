"""Automatic speech recognition using faster-whisper."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from app.config import settings
from app.devices import log_compute_environment

logger = logging.getLogger(__name__)

_CUDA_ERROR_MARKERS = ("cublas", "cuda", "cudnn", "c10_cuda", "out of memory")


class ASRModelLoadError(RuntimeError):
    pass


class ASRTranscriptionError(RuntimeError):
    pass


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    latency_ms: int
    avg_logprob: float = 0.0
    confident: bool = True


class ASREngine:
    def __init__(self) -> None:
        self._model: Any = None
        self._device = settings.asr_device
        self._compute_type = settings.asr_compute_type
        self._loaded = False
        self._previous_text: str = ""

    def set_context(self, previous_text: str) -> None:
        self._previous_text = previous_text[-settings.asr_context_chars :].strip()

    @staticmethod
    def _is_cuda_runtime_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return any(marker in message for marker in _CUDA_ERROR_MARKERS)

    def _create_model(self, device: str, compute_type: str) -> Any:
        from faster_whisper import WhisperModel

        cpu_threads = settings.asr_cpu_threads or max(1, (os.cpu_count() or 4) - 1)
        return WhisperModel(
            settings.asr_model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(settings.models_dir),
            cpu_threads=cpu_threads,
        )

    def _warmup(self) -> None:
        if self._model is None:
            return
        silence = np.zeros(settings.sample_rate, dtype=np.float32)
        segments, _info = self._model.transcribe(
            silence,
            language=settings.asr_language,
            beam_size=1,
            best_of=1,
            vad_filter=False,
        )
        list(segments)

    def _load_on_device(self, device: str, compute_type: str) -> None:
        self._model = self._create_model(device, compute_type)
        self._device = device
        self._compute_type = compute_type
        self._warmup()
        logger.info(
            "ASR model loaded: size=%s device=%s compute=%s",
            settings.asr_model_size,
            self._device,
            self._compute_type,
        )

    def _fallback_to_cpu(self, reason: str) -> None:
        logger.warning("Switching ASR to CPU: %s", reason)
        self._model = None
        self._loaded = False
        self._load_on_device("cpu", settings.asr_cpu_compute_type)
        self._loaded = True

    def load(self) -> None:
        if self._loaded:
            return

        try:
            from faster_whisper import WhisperModel  # noqa: F401
        except ImportError as exc:
            raise ASRModelLoadError("faster-whisper is not installed.") from exc

        settings.models_dir.mkdir(parents=True, exist_ok=True)
        log_compute_environment(
            asr_device=settings.asr_device,
            translate_device=settings.translate_device,
        )

        preferred_device = settings.asr_device
        preferred_compute = (
            settings.asr_compute_type if preferred_device == "cuda" else settings.asr_cpu_compute_type
        )

        try:
            self._load_on_device(preferred_device, preferred_compute)
        except Exception as first_exc:
            if preferred_device == "cuda":
                try:
                    self._fallback_to_cpu(f"CUDA init failed: {first_exc}")
                except Exception as cpu_exc:
                    raise ASRModelLoadError(f"Failed to load ASR model: {cpu_exc}") from cpu_exc
            else:
                raise ASRModelLoadError(f"Failed to load ASR model: {first_exc}") from first_exc

        self._loaded = True

    def transcribe(self, audio: npt.NDArray[np.float32]) -> TranscriptionResult:
        if not self._loaded or self._model is None:
            raise ASRTranscriptionError("ASR model is not loaded.")

        if audio.size == 0:
            return TranscriptionResult(text="", latency_ms=0, confident=False)

        start = time.perf_counter()
        try:
            text, avg_logprob, confident = self._run_transcribe(audio)
        except Exception as exc:
            if self._device == "cuda" and self._is_cuda_runtime_error(exc):
                self._fallback_to_cpu(f"CUDA runtime failed: {exc}")
                start = time.perf_counter()
                try:
                    text, avg_logprob, confident = self._run_transcribe(audio)
                except Exception as retry_exc:
                    raise ASRTranscriptionError(f"Transcription failed: {retry_exc}") from retry_exc
            else:
                raise ASRTranscriptionError(f"Transcription failed: {exc}") from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        if text:
            self._previous_text = text
        return TranscriptionResult(
            text=text,
            latency_ms=latency_ms,
            avg_logprob=avg_logprob,
            confident=confident,
        )

    def _build_prompt(self) -> str:
        prompt = settings.asr_initial_prompt
        if self._previous_text:
            prompt = f"{prompt} {self._previous_text}"
        return prompt

    def _run_transcribe(self, audio: npt.NDArray[np.float32]) -> tuple[str, float, bool]:
        segments, _info = self._model.transcribe(
            audio,
            language=settings.asr_language,
            beam_size=settings.asr_beam_size,
            best_of=max(1, min(settings.asr_best_of, 5)),
            patience=settings.asr_patience,
            temperature=0.0,
            vad_filter=settings.asr_whisper_vad_filter,
            vad_parameters={"min_silence_duration_ms": 500},
            initial_prompt=self._build_prompt(),
            hotwords=settings.asr_hotwords,
            condition_on_previous_text=settings.asr_condition_on_previous,
            compression_ratio_threshold=settings.asr_compression_ratio_threshold,
            length_penalty=settings.asr_length_penalty,
            log_prob_threshold=-1.0,
            no_speech_threshold=settings.asr_max_no_speech_prob,
            hallucination_silence_threshold=settings.asr_hallucination_silence_threshold,
            without_timestamps=True,
        )

        accepted: list[str] = []
        logprobs: list[float] = []
        for seg in segments:
            if seg.no_speech_prob > settings.asr_max_no_speech_prob:
                logger.debug("Skipping segment (no_speech=%.2f): %s", seg.no_speech_prob, seg.text)
                continue
            if seg.avg_logprob < settings.asr_min_avg_logprob:
                logger.debug("Skipping segment (logprob=%.2f): %s", seg.avg_logprob, seg.text)
                continue
            accepted.append(seg.text.strip())
            logprobs.append(seg.avg_logprob)

        text = " ".join(accepted).strip()
        avg_logprob = sum(logprobs) / len(logprobs) if logprobs else -999.0
        confident = bool(text) and avg_logprob >= settings.asr_min_avg_logprob
        return text, avg_logprob, confident

    def transcribe_file(self, path: Path) -> TranscriptionResult:
        import soundfile as sf

        audio, sample_rate = sf.read(str(path), dtype="float32")
        if audio.ndim > 1:
            audio = audio[:, 0]

        if sample_rate != settings.sample_rate:
            duration = len(audio) / sample_rate
            target_length = int(duration * settings.sample_rate)
            indices = np.linspace(0, len(audio) - 1, target_length)
            audio = np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

        return self.transcribe(audio.astype(np.float32))

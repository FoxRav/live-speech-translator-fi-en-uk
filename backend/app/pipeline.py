"""Audio -> ASR -> translation pipeline."""

from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from difflib import SequenceMatcher

import numpy as np
import numpy.typing as npt

from app.asr import ASREngine, ASRModelLoadError, ASRTranscriptionError
from app.audio_capture import AudioCapture, AudioCaptureError, MicrophoneNotFoundError
from app.audio_utils import normalize_peak
from app.fi_text import normalize_finnish_asr, should_publish_transcript, split_finnish_sentences
from app.config import settings
from app.logger import SessionLogger, TranslationLogEntry, utc_timestamp
from app.translator import (
    TranslationError,
    TranslationModelLoadError,
    TranslationResult,
    Translator,
)
from app.vad import EnergyVAD

logger = logging.getLogger(__name__)

StatusCallback = Callable[[str, str], Awaitable[None]]
PartialCallback = Callable[[str], Awaitable[None]]
TranslationCallback = Callable[[dict[str, object]], Awaitable[None]]
ErrorCallback = Callable[[str], Awaitable[None]]


@dataclass
class PipelineState:
    status: str = "idle"
    message: str = "Ready"


class TranslationPipeline:
    def __init__(self) -> None:
        self._asr = ASREngine()
        self._translator = Translator()
        self._vad: EnergyVAD | None = None
        self._audio: AudioCapture | None = None
        self._session_logger = SessionLogger()

        self._running = False
        self._loading = False
        self._processing = False
        self._lock = threading.Lock()
        self._last_transcripts: list[str] = []
        self._segment_queue: asyncio.Queue[npt.NDArray[np.float32]] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker_task: asyncio.Task[None] | None = None

        self._on_status: StatusCallback | None = None
        self._on_partial: PartialCallback | None = None
        self._on_translation: TranslationCallback | None = None
        self._on_error: ErrorCallback | None = None

    def set_callbacks(
        self,
        on_status: StatusCallback,
        on_partial: PartialCallback,
        on_translation: TranslationCallback,
        on_error: ErrorCallback,
    ) -> None:
        self._on_status = on_status
        self._on_partial = on_partial
        self._on_translation = on_translation
        self._on_error = on_error

    @property
    def is_busy(self) -> bool:
        return self._loading or self._running

    @property
    def state(self) -> PipelineState:
        if self._processing:
            return PipelineState(status="processing", message="Käsitellään puhetta...")
        if self._loading:
            return PipelineState(status="processing", message="Ladataan malleja, odota hetki...")
        if self._running:
            return PipelineState(status="listening", message="Kuunnellaan mikrofonia")
        return PipelineState(status="idle", message="Valmis")

    @property
    def session_log_path(self) -> str | None:
        path = self._session_logger.path
        return str(path) if path else None

    async def _emit_status(self, status: str, message: str) -> None:
        if self._on_status:
            await self._on_status(status, message)

    async def _emit_error(self, message: str) -> None:
        logger.error(message)
        if self._on_error:
            await self._on_error(message)
        await self._emit_status("error", message)

    def _is_duplicate(self, text: str) -> bool:
        normalized = self._normalize(text)
        if len(normalized) < settings.min_transcript_length:
            return True

        for prev in self._last_transcripts[-5:]:
            ratio = SequenceMatcher(None, normalized, self._normalize(prev)).ratio()
            if ratio >= settings.duplicate_similarity_threshold:
                return True
        return False

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\säöå]", "", text, flags=re.UNICODE)
        return re.sub(r"\s+", " ", text)

    def _translate_fi_text(self, fi_text: str) -> TranslationResult:
        sentences = split_finnish_sentences(fi_text)
        if len(sentences) <= 1:
            return self._translator.translate(fi_text)

        en_parts: list[str] = []
        uk_parts: list[str] = []
        en_ms_total = 0
        uk_ms_total = 0
        for sentence in sentences:
            result = self._translator.translate(sentence)
            en_parts.append(result.en)
            uk_parts.append(result.uk)
            en_ms_total += result.en_latency_ms
            uk_ms_total += result.uk_latency_ms
        return TranslationResult(
            en=" ".join(en_parts),
            uk=" ".join(uk_parts),
            en_latency_ms=en_ms_total,
            uk_latency_ms=uk_ms_total,
        )

    def _on_audio_chunk(self, chunk: npt.NDArray[np.float32]) -> None:
        if not self._running or self._vad is None or self._segment_queue is None or self._loop is None:
            return

        segment = self._vad.process(chunk)
        if segment is not None:
            asyncio.run_coroutine_threadsafe(self._segment_queue.put(segment), self._loop)

    async def start(self) -> None:
        if self._running or self._loading:
            return

        self._loading = True
        self._loop = asyncio.get_running_loop()
        self._segment_queue = asyncio.Queue()

        if not self._asr._loaded:
            await self._emit_status("processing", "Ladataan puheentunnistusmallia...")
            try:
                await asyncio.to_thread(self._asr.load)
            except ASRModelLoadError as exc:
                self._loading = False
                await self._emit_error(f"ASR model load failed: {exc}")
                return
        else:
            self._asr.set_context("")

        if not self._translator.loaded:
            await self._emit_status("processing", "Ladataan käännösmalleja...")
            try:
                await asyncio.to_thread(self._translator.load)
            except TranslationModelLoadError as exc:
                self._loading = False
                await self._emit_error(f"Translation model load failed: {exc}")
                return

        await self._emit_status("processing", "Avataan mikrofonia...")

        self._vad = EnergyVAD(
            sample_rate=settings.sample_rate,
            energy_threshold=settings.vad_energy_threshold,
            silence_duration_ms=settings.vad_silence_duration_ms,
            min_speech_duration_ms=settings.vad_min_speech_duration_ms,
            max_chunk_duration_sec=settings.vad_max_chunk_duration_sec,
        )

        try:
            self._audio = AudioCapture(
                sample_rate=settings.sample_rate,
                block_size=settings.audio_block_size,
                on_audio=self._on_audio_chunk,
            )
            await asyncio.to_thread(self._audio.start)
        except MicrophoneNotFoundError as exc:
            self._loading = False
            await self._emit_error(str(exc))
            return
        except AudioCaptureError as exc:
            self._loading = False
            await self._emit_error(str(exc))
            return

        log_path = self._session_logger.start_session()
        logger.info("Session log started: %s", log_path)

        self._loading = False
        self._running = True
        self._last_transcripts.clear()
        self._worker_task = asyncio.create_task(self._process_loop())
        await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")

    async def stop(self) -> None:
        if not self._running:
            await self._emit_status("idle", "Stopped")
            return

        self._running = False

        if self._audio is not None:
            await asyncio.to_thread(self._audio.stop)
            self._audio = None

        if self._vad is not None:
            final_segment = self._vad.flush()
            if final_segment is not None and self._segment_queue is not None:
                await self._segment_queue.put(final_segment)
            self._vad.reset()
            self._vad = None

        if self._worker_task is not None:
            await self._worker_task
            self._worker_task = None

        self._session_logger.close()
        self._segment_queue = None
        await self._emit_status("idle", "Stopped")
        logger.info("Pipeline stopped")

    async def _process_loop(self) -> None:
        assert self._segment_queue is not None

        while self._running or not self._segment_queue.empty():
            try:
                segment = await asyncio.wait_for(self._segment_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            await self._process_segment(segment)

    async def _process_segment(self, audio: npt.NDArray[np.float32]) -> None:
        self._processing = True
        audio = normalize_peak(audio)
        duration_sec = len(audio) / settings.sample_rate
        logger.info("Processing audio segment: %.2f s", duration_sec)
        await self._emit_status(
            "processing",
            f"Tunnistetaan puhetta ({duration_sec:.1f} s)...",
        )

        if self._last_transcripts:
            recent = self._last_transcripts[-settings.asr_context_segments :]
            self._asr.set_context(" ".join(recent))

        total_start = time.perf_counter()

        try:
            asr_result = await asyncio.wait_for(
                asyncio.to_thread(self._asr.transcribe, audio),
                timeout=settings.asr_timeout_sec,
            )
        except asyncio.TimeoutError:
            await self._emit_error("Puheentunnistus aikakatkaistiin — paina STOP ja Käynnistä uudelleen")
            self._processing = False
            if self._running:
                await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")
            return
        except ASRTranscriptionError as exc:
            await self._emit_error(f"Puheentunnistus epäonnistui: {exc}")
            self._processing = False
            if self._running:
                await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")
            return

        fi_text = normalize_finnish_asr(asr_result.text.strip())
        logger.info(
            "ASR result (%d ms, logprob=%.2f, confident=%s): %s",
            asr_result.latency_ms,
            asr_result.avg_logprob,
            asr_result.confident,
            fi_text or "(empty)",
        )
        if not fi_text:
            logger.debug("Empty transcription from audio segment")
            self._processing = False
            if self._running:
                await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")
            return

        if not should_publish_transcript(
            fi_text, asr_result.avg_logprob, settings.asr_publish_min_logprob
        ):
            logger.info(
                "Rejected ASR (logprob=%.2f): %s",
                asr_result.avg_logprob,
                fi_text,
            )
            self._asr.set_context(
                self._last_transcripts[-1] if self._last_transcripts else ""
            )
            self._processing = False
            if self._running:
                await self._emit_status("listening", "Kuunnellaan — puhu selkeästi kokonaisia lauseita")
            return

        if self._is_duplicate(fi_text):
            logger.debug("Skipping duplicate: %s", fi_text)
            self._processing = False
            if self._running:
                await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")
            return

        await self._emit_status("processing", f"Käännetään: {fi_text[:60]}...")

        try:
            translation = await asyncio.wait_for(
                asyncio.to_thread(self._translate_fi_text, fi_text),
                timeout=settings.translate_timeout_sec,
            )
        except asyncio.TimeoutError:
            await self._emit_error("Käännös aikakatkaistiin")
            self._processing = False
            if self._running:
                await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")
            return
        except TranslationError as exc:
            await self._emit_error(f"Käännös epäonnistui: {exc}")
            self._processing = False
            if self._running:
                await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")
            return

        total_latency_ms = int((time.perf_counter() - total_start) * 1000)
        timestamp = utc_timestamp()

        self._last_transcripts.append(fi_text)
        if len(self._last_transcripts) > 20:
            self._last_transcripts = self._last_transcripts[-20:]

        payload: dict[str, object] = {
            "type": "translation",
            "timestamp": timestamp,
            "fi": fi_text,
            "en": translation.en,
            "uk": translation.uk,
            "latency_ms": total_latency_ms,
            "asr_ms": asr_result.latency_ms,
            "translate_en_ms": translation.en_latency_ms,
            "translate_uk_ms": translation.uk_latency_ms,
        }

        self._session_logger.log_translation(
            TranslationLogEntry(
                timestamp=timestamp,
                fi=fi_text,
                en=translation.en,
                uk=translation.uk,
                asr_model=settings.asr_model_size,
                translation_engine=settings.translation_engine,
                latency_ms=total_latency_ms,
                asr_ms=asr_result.latency_ms,
                translate_en_ms=translation.en_latency_ms,
                translate_uk_ms=translation.uk_latency_ms,
            )
        )

        if self._on_translation:
            await self._on_translation(payload)

        logger.info(
            "Translation done (%d ms): EN=%s | UK=%s",
            total_latency_ms,
            translation.en,
            translation.uk,
        )
        self._processing = False
        if self._running:
            await self._emit_status("listening", "Kuunnellaan — puhu suomea mikrofoniin")

    def export_session_markdown(self) -> str | None:
        path = self._session_logger.export_markdown()
        return str(path) if path else None

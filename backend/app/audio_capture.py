"""Microphone audio capture using sounddevice."""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import sounddevice as sd

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MicrophoneNotFoundError(RuntimeError):
    pass


class AudioCaptureError(RuntimeError):
    pass


class AudioCapture:
    """Captures audio from the default or configured input device."""

    def __init__(
        self,
        sample_rate: int,
        block_size: int,
        on_audio: Callable[[npt.NDArray[np.float32]], None],
        device: int | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.on_audio = on_audio
        self.device = device

        self._stream: sd.InputStream | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._queue: queue.Queue[npt.NDArray[np.float32]] = queue.Queue(maxsize=100)

    @staticmethod
    def list_devices() -> list[dict[str, object]]:
        devices: list[dict[str, object]] = []
        for idx, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append(
                    {
                        "index": idx,
                        "name": dev["name"],
                        "channels": dev["max_input_channels"],
                        "sample_rate": dev["default_samplerate"],
                    }
                )
        return devices

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        try:
            sd.query_devices(self.device, "input")
        except sd.PortAudioError as exc:
            raise MicrophoneNotFoundError("Microphone not found or not accessible.") from exc

        self._stop_event.clear()

        def _capture_loop() -> None:
            try:
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    blocksize=self.block_size,
                    device=self.device,
                    callback=self._callback,
                ):
                    while not self._stop_event.is_set():
                        try:
                            chunk = self._queue.get(timeout=0.1)
                            self.on_audio(chunk)
                        except queue.Empty:
                            continue
            except sd.PortAudioError as exc:
                logger.error("Audio capture failed: %s", exc)
                raise AudioCaptureError("Audio capture failed.") from exc

        self._thread = threading.Thread(target=_capture_loop, name="audio-capture", daemon=True)
        self._thread.start()
        logger.info("Audio capture started (device=%s, rate=%d)", self.device, self.sample_rate)

    def _callback(
        self,
        indata: npt.NDArray[np.float32],
        _frames: int,
        _time: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            logger.warning("Audio callback status: %s", status)
        chunk = indata[:, 0].copy()
        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            logger.warning("Audio queue full, dropping chunk")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        logger.info("Audio capture stopped")

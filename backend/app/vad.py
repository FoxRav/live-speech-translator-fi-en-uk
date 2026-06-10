"""Energy-based voice activity detection."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


class EnergyVAD:
    """Simple energy-threshold VAD for speech segment detection."""

    def __init__(
        self,
        sample_rate: int,
        energy_threshold: float,
        silence_duration_ms: int,
        min_speech_duration_ms: int,
        max_chunk_duration_sec: float,
    ) -> None:
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_samples = int(sample_rate * silence_duration_ms / 1000)
        self.min_speech_samples = int(sample_rate * min_speech_duration_ms / 1000)
        self.max_chunk_samples = int(sample_rate * max_chunk_duration_sec)

        self._speech_buffer: list[npt.NDArray[np.float32]] = []
        self._silence_counter = 0
        self._in_speech = False
        self._speech_sample_count = 0

    def reset(self) -> None:
        self._speech_buffer.clear()
        self._silence_counter = 0
        self._in_speech = False
        self._speech_sample_count = 0

    @staticmethod
    def _rms_energy(audio: npt.NDArray[np.float32]) -> float:
        if audio.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))

    def process(self, chunk: npt.NDArray[np.float32]) -> npt.NDArray[np.float32] | None:
        """Process audio chunk; return completed speech segment or None."""
        energy = self._rms_energy(chunk)
        is_speech = energy >= self.energy_threshold

        if is_speech:
            if not self._in_speech:
                self._in_speech = True
                self._speech_sample_count = 0
            self._speech_buffer.append(chunk.copy())
            self._speech_sample_count += len(chunk)
            self._silence_counter = 0

            if self._speech_sample_count >= self.max_chunk_samples:
                return self._flush_segment()
            return None

        if self._in_speech:
            self._speech_buffer.append(chunk.copy())
            self._speech_sample_count += len(chunk)
            self._silence_counter += len(chunk)

            if self._silence_counter >= self.silence_samples:
                return self._flush_segment()

        return None

    def flush(self) -> npt.NDArray[np.float32] | None:
        """Flush any remaining speech on stop."""
        if self._in_speech and self._speech_sample_count >= self.min_speech_samples:
            return self._flush_segment()
        self.reset()
        return None

    def _flush_segment(self) -> npt.NDArray[np.float32] | None:
        if self._speech_sample_count < self.min_speech_samples:
            self.reset()
            return None

        segment = np.concatenate(self._speech_buffer).astype(np.float32)
        self.reset()
        return segment

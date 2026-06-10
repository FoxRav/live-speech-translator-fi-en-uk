"""Audio preprocessing helpers."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def normalize_peak(audio: npt.NDArray[np.float32], target_peak: float = 0.85) -> npt.NDArray[np.float32]:
    """Boost quiet microphone input without clipping."""
    if audio.size == 0:
        return audio
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-6:
        return audio
    if peak >= target_peak:
        return audio
    scaled = audio * (target_peak / peak)
    return np.clip(scaled, -1.0, 1.0).astype(np.float32)

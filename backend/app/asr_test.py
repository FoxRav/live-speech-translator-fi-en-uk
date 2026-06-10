"""CLI tool to test ASR + translation on a WAV file."""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import numpy as np

from app.asr import ASREngine
from app.config import settings
from app.translator import Translator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_wav(path: Path) -> np.ndarray:
    try:
        import soundfile as sf
    except ImportError as exc:
        raise SystemExit("soundfile is required: pip install soundfile") from exc

    audio, sample_rate = sf.read(str(path), dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    if sample_rate != settings.sample_rate:
        logger.warning(
            "Sample rate %d != %d. Resampling with linear interpolation.",
            sample_rate,
            settings.sample_rate,
        )
        duration = len(audio) / sample_rate
        target_length = int(duration * settings.sample_rate)
        indices = np.linspace(0, len(audio) - 1, target_length)
        audio = np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    return audio


def main() -> None:
    parser = argparse.ArgumentParser(description="Test ASR and translation on a WAV file")
    parser.add_argument("--input", required=True, type=Path, help="Path to input WAV file")
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"File not found: {args.input}")

    audio = load_wav(args.input)

    asr = ASREngine()
    translator = Translator()

    logger.info("Loading models...")
    asr.load()
    translator.load()

    start = time.perf_counter()
    asr_result = asr.transcribe(audio)
    translation = translator.translate(asr_result.text)
    total_ms = int((time.perf_counter() - start) * 1000)

    print(f"FI: {asr_result.text}")
    print(f"EN: {translation.en}")
    print(f"UK: {translation.uk}")
    print(f"latency_ms: {total_ms}")
    print(f"  asr_ms: {asr_result.latency_ms}")
    print(f"  translate_en_ms: {translation.en_latency_ms}")
    print(f"  translate_uk_ms: {translation.uk_latency_ms}")


if __name__ == "__main__":
    main()

"""Resolve compute devices for ASR and translation."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def is_ctranslate2_cuda_available() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def is_torch_cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except ImportError:
        return False


@dataclass(frozen=True)
class ComputeStatus:
    asr_cuda_available: bool
    translate_cuda_available: bool
    gpu_name: str | None
    vram_gb: float | None


def get_compute_status() -> ComputeStatus:
    gpu_name: str | None = None
    vram_gb: float | None = None
    if is_torch_cuda_available():
        try:
            import torch

            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except Exception:
            pass
    return ComputeStatus(
        asr_cuda_available=is_ctranslate2_cuda_available(),
        translate_cuda_available=is_torch_cuda_available(),
        gpu_name=gpu_name,
        vram_gb=vram_gb,
    )


def resolve_torch_device(preferred: str) -> str:
    normalized = preferred.strip().lower()
    if normalized == "cuda" and is_torch_cuda_available():
        return "cuda"
    return "cpu"


def resolve_asr_device(preferred: str) -> str:
    normalized = preferred.strip().lower()
    if normalized == "cuda" and is_ctranslate2_cuda_available():
        return "cuda"
    return "cpu"


def resolve_nllb_device(preferred: str) -> str:
    """NLLB 600M + Whisper large-v3 exceed 6 GB VRAM — keep NLLB on CPU there."""
    if preferred.strip().lower() != "cuda" or not is_torch_cuda_available():
        return "cpu"
    status = get_compute_status()
    if status.vram_gb is not None and status.vram_gb < 8.0:
        logger.info(
            "NLLB uses CPU (%.1f GB VRAM — ASR large-v3 needs GPU)",
            status.vram_gb,
        )
        return "cpu"
    return "cuda"


def log_compute_environment(*, asr_device: str, translate_device: str) -> None:
    status = get_compute_status()
    if status.gpu_name and status.vram_gb is not None:
        logger.info("GPU: %s (%.1f GB VRAM)", status.gpu_name, status.vram_gb)
    logger.info(
        "Compute: ASR cuda=%s (ctranslate2), translate cuda=%s (torch), "
        "configured asr=%s translate=%s",
        status.asr_cuda_available,
        status.translate_cuda_available,
        asr_device,
        translate_device,
    )
    if asr_device == "cuda" and not status.asr_cuda_available:
        logger.warning("ASR_DEVICE=cuda but ctranslate2 has no CUDA — will fall back to CPU")
    if translate_device == "cuda" and not status.translate_cuda_available:
        logger.warning(
            "TRANSLATE_DEVICE=cuda but PyTorch has no CUDA — install: "
            "pip install torch --index-url https://download.pytorch.org/whl/cu124"
        )

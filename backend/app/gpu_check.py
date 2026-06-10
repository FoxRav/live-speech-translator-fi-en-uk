"""Print GPU status for ASR (ctranslate2) and translation (torch)."""

from __future__ import annotations

import sys

from app.config import settings
from app.devices import get_compute_status


def main() -> int:
    status = get_compute_status()
    print("=== GPU-tarkistus ===")
    print(f"ASR-malli:     {settings.asr_model_size}")
    print(f"ASR-laite:     {settings.asr_device}")
    print(f"Käännös-laite: {settings.translate_device}")
    print()
    print(f"ctranslate2 CUDA (ASR):      {'KYLLA' if status.asr_cuda_available else 'EI'}")
    print(f"PyTorch CUDA (käännökset):   {'KYLLA' if status.translate_cuda_available else 'EI'}")
    if status.gpu_name:
        print(f"GPU: {status.gpu_name} ({status.vram_gb:.1f} GB)")
    print()

    ok = True
    if settings.asr_device == "cuda" and not status.asr_cuda_available:
        print("VAROITUS: ASR_DEVICE=cuda mutta ctranslate2 ei nae CUDA:ta")
        ok = False
    if settings.translate_device == "cuda" and not status.translate_cuda_available:
        print("VAROITUS: TRANSLATE_DEVICE=cuda mutta PyTorch CUDA puuttuu.")
        print("Asenna VAIN projektin .venv:hen (sulje backend ensin):")
        print("  .\\install_torch_gpu.ps1")
        ok = False

    if status.asr_cuda_available and settings.asr_device == "cuda":
        print("ASR kayttaa GPU:ta (ctranslate2 OK).")
    if status.translate_cuda_available and settings.translate_device == "cuda":
        print("Käännökset kayttavat GPU:ta (PyTorch OK).")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

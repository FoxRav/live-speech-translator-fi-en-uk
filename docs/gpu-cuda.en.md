# GPU and CUDA

| Component | Library | Device |
|-----------|---------|--------|
| ASR (Whisper) | ctranslate2 | `ASR_DEVICE=cuda` |
| Translation (OPUS) | PyTorch | `TRANSLATE_DEVICE=cuda` |
| Translation (NLLB) | PyTorch | CPU if VRAM < 8 GB |

## Verification

```powershell
cd backend
.\check_gpu.ps1
```

Expected with NVIDIA GPU:

```
ctranslate2 CUDA (ASR):      KYLLA
PyTorch CUDA (translation):  KYLLA
```

Or: `Invoke-RestMethod http://127.0.0.1:8000/health`

## Notes

- PyTorch CUDA is installed via `install_torch_gpu.ps1` (not in requirements.txt).
- If CUDA fails, ASR falls back to CPU automatically.
- On 6 GB VRAM: large-v3 ASR + OPUS works; NLLB may use OPUS EN→UK fallback.

## Typical latency (GPU)

| Stage | Time |
|-------|------|
| VAD pause | 1.2–1.5 s |
| ASR large-v3 | 1–4 s |
| Hybrid translation | 1–5 s |
| **Total** | **3–10 s** |

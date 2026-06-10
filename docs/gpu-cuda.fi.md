# GPU ja CUDA

| Komponentti | Kirjasto | Laite |
|-------------|----------|-------|
| ASR (Whisper) | ctranslate2 | `ASR_DEVICE=cuda` |
| Käännös (OPUS) | PyTorch | `TRANSLATE_DEVICE=cuda` |
| Käännös (NLLB) | PyTorch | CPU jos VRAM < 8 GB |

## Tarkistus

```powershell
cd backend
.\check_gpu.ps1
```

Odotettu tulos NVIDIA GPU:lla:

```
ctranslate2 CUDA (ASR):      KYLLA
PyTorch CUDA (käännökset):   KYLLA
```

Tai: `Invoke-RestMethod http://127.0.0.1:8000/health`

```json
{
  "asr_model": "large-v3",
  "asr_device": "cuda",
  "asr_cuda_available": true,
  "translate_cuda_available": true,
  "gpu_name": "NVIDIA GeForce RTX ..."
}
```

## Huomiot

- PyTorch CUDA asennetaan `install_torch_gpu.ps1`:llä (ei requirements.txt:stä).
- Jos CUDA puuttuu, ASR putoaa automaattisesti CPU:lle.
- 6 GB VRAM: large-v3 ASR + OPUS toimii; NLLB voi vaatia OPUS EN→UK -fallbackin.

## Latenssi (tyypillinen, GPU)

| Vaihe | Aika |
|-------|------|
| VAD | 1,2–1,5 s tauko |
| ASR large-v3 | 1–4 s |
| Käännös hybrid | 1–5 s |
| **Yhteensä** | **3–10 s** |

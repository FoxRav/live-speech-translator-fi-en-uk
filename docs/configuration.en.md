# Configuration

Copy `backend/.env.example` to `backend/.env`:

```env
ASR_MODEL_SIZE=large-v3
ASR_DEVICE=cuda
ASR_COMPUTE_TYPE=float16
ASR_BEAM_SIZE=5
ASR_BEST_OF=5
TRANSLATE_DEVICE=cuda
TRANSLATION_ENGINE=hybrid
TRANSLATE_NUM_BEAMS=4

VAD_SILENCE_DURATION_MS=1500
VAD_MIN_SPEECH_DURATION_MS=1200

# Custom vocabulary:
# ASR_HOTWORDS=helluntai seurakunta meeting presentation ...
# ASR_INITIAL_PROMPT=Finnish speech. Meeting, presentation, church, ...
```

## Settings

| Setting | Effect |
|---------|--------|
| `ASR_MODEL_SIZE=large-v3` | Best Finnish ASR (default) |
| `ASR_MODEL_SIZE=medium` | Good Finnish, less VRAM |
| `ASR_DEVICE=cuda` | Whisper on GPU |
| `ASR_BEAM_SIZE=5` | More accurate, slower ASR |
| `ASR_HOTWORDS` | Whisper hotwords for domain terms |
| `ASR_INITIAL_PROMPT` | ASR context hint |
| `VAD_SILENCE_DURATION_MS` | Silence before sentence end (default 1500 ms) |
| `VAD_MIN_SPEECH_DURATION_MS` | Minimum speech chunk (default 1200 ms) |
| `TRANSLATION_ENGINE=hybrid` | OPUS FI→EN + NLLB/OPUS UK (default) |
| `TRANSLATION_ENGINE=opus` | Fastest |
| `TRANSLATION_ENGINE=nllb` | Best quality, slowest |

## Finnish ASR enhancements

| Layer | File | Purpose |
|-------|------|---------|
| Hotwords + prompt | `config.py` / `.env` | Guide Whisper vocabulary |
| Text cleanup | `fi_text.py` | Fix common ASR errors (no censorship) |
| Sentence split | `pipeline.py` | Per-sentence translation |
| Hallucination filter | `asr.py` | Drop empty/noise segments |

Add recurring misrecognized words to `ASR_HOTWORDS` and `ASR_INITIAL_PROMPT` in `.env`.

## Hybrid engine and 6 GB VRAM

1. **OPUS FI→EN** (GPU)
2. **NLLB FI→UK** (attempts load)

If NLLB cannot load, **OPUS EN→UK** fallback is used automatically.

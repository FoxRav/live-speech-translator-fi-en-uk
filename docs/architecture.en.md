# Architecture

## Data flow

```
Microphone (sounddevice)
  → Energy VAD (vad.py)
  → ASR Whisper large-v3 (asr.py, ctranslate2)
  → Finnish text cleanup (fi_text.py)
  → Hybrid translation (translator.py)
  → WebSocket (main.py)
  → React UI (frontend/)
```

## Backend modules

| Module | Responsibility |
|--------|----------------|
| `main.py` | FastAPI, `/health`, WebSocket `/ws` |
| `pipeline.py` | Live loop, queuing, callbacks |
| `audio_capture.py` | Microphone capture |
| `vad.py` | Speech segmentation |
| `asr.py` | faster-whisper transcription |
| `fi_text.py` | ASR post-processing, sentence split |
| `translator.py` | OPUS / NLLB / hybrid |
| `devices.py` | GPU detection |
| `logger.py` | Session JSONL logging |
| `config.py` | Pydantic settings |

## Frontend

| File | Responsibility |
|------|----------------|
| `App.tsx` | UI, fullscreen, settings |
| `TranslationDisplay.tsx` | Scrolling translation feed |
| `websocket.ts` | WebSocket client |
| `types.ts` | Message types |

## Models (auto-downloaded)

| Model | Purpose |
|-------|---------|
| `Systran/faster-whisper-large-v3` | Finnish speech → text |
| `Helsinki-NLP/opus-mt-fi-en` | Finnish → English |
| `Helsinki-NLP/opus-mt-en-uk` | English → Ukrainian (fallback) |
| `facebook/nllb-200-distilled-600M` | Finnish → Ukrainian |

## Dependencies

See `backend/requirements.txt`. Torch is installed separately for GPU.

## Project layout

```
live-speech-translator-fi/
  backend/app/          Python source
  backend/models/       Downloaded models (gitignored)
  backend/logs/         Session logs (gitignored)
  frontend/src/         React UI
  docs/                 Documentation
  examples/             Sample data
```

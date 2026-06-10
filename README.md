# Live Speech Translator FI

Local live speech translation app for Finnish speech. Browser UI, FastAPI backend, Whisper transcription, and English/Ukrainian translation.

**No cloud APIs.** After models are downloaded once, processing runs entirely on your machine.

**Suomenkielinen dokumentaatio: [README.fi.md](README.fi.md)**

## Features

- **Finnish ASR** — faster-whisper `large-v3` with GPU support (ctranslate2)
- **Live translation** — Finnish → English + Ukrainian (hybrid OPUS / NLLB pipeline)
- **Browser UI** — React/Vite display for projector use (fullscreen, scrolling feed)
- **WebSocket control** — start/stop, live updates, session log export
- **No censorship** — recognized speech is shown as transcribed
- **Offline capable** — works without internet after models are cached locally
- **Windows-first** — PowerShell setup and startup scripts

## Architecture

```
Microphone → FastAPI backend (backend/.venv)
               → VAD → Whisper large-v3 (FI text)
               → Hybrid translation (FI→EN, FI/EN→UK)
               → WebSocket
             → React/Vite browser UI
```

Details: [docs/architecture.en.md](docs/architecture.en.md)

## Requirements

| Component | Minimum |
|-----------|---------|
| OS | Windows 11 (primary target) |
| Python | 3.10 or 3.11 |
| Node.js | 18+ |
| RAM | 16 GB (24 GB recommended) |
| GPU | Optional NVIDIA 6+ GB VRAM for low latency |
| Disk | ~10–14 GB for venv + models |

## Quick start

```powershell
git clone https://github.com/YOUR_USER/live-speech-translator-fi.git
cd live-speech-translator-fi

.\setup_backend.ps1
.\install_torch_gpu.ps1      # optional, NVIDIA GPU
cd backend
.\check_gpu.ps1

cd ..\frontend
npm install

# Terminal 1
cd backend
.\start.ps1

# Terminal 2 (repo root)
.\start_frontend.ps1
```

Open **http://localhost:5173** → click **Start** → speak Finnish in full sentences.

Full guide: [docs/installation.en.md](docs/installation.en.md)

## Configuration

Copy `backend/.env.example` to `backend/.env`. Key options:

```env
ASR_MODEL_SIZE=large-v3
ASR_DEVICE=cuda
TRANSLATION_ENGINE=hybrid
```

Custom vocabulary via `ASR_HOTWORDS` and `ASR_INITIAL_PROMPT` in `.env`.

Details: [docs/configuration.en.md](docs/configuration.en.md)

## Offline usage

After models are cached in `backend/models/`, the app runs without internet. First run downloads models from Hugging Face (2–15 minutes).

## GPU notes

- ASR uses **ctranslate2 CUDA**
- Translation uses **PyTorch CUDA** (installed via `install_torch_gpu.ps1`)
- On 6 GB VRAM, NLLB may fall back to OPUS EN→UK automatically

Details: [docs/gpu-cuda.en.md](docs/gpu-cuda.en.md)

## Privacy

All audio and text processing is local. Session logs are stored in `backend/logs/` on your machine and may contain spoken content. No speech is sent to third-party APIs.

Details: [docs/privacy.en.md](docs/privacy.en.md)

## Documentation

| Topic | English | Finnish |
|-------|---------|---------|
| Installation | [installation.en.md](docs/installation.en.md) | [installation.fi.md](docs/installation.fi.md) |
| Configuration | [configuration.en.md](docs/configuration.en.md) | [configuration.fi.md](docs/configuration.fi.md) |
| GPU / CUDA | [gpu-cuda.en.md](docs/gpu-cuda.en.md) | [gpu-cuda.fi.md](docs/gpu-cuda.fi.md) |
| Architecture | [architecture.en.md](docs/architecture.en.md) | [architecture.fi.md](docs/architecture.fi.md) |
| Troubleshooting | [troubleshooting.en.md](docs/troubleshooting.en.md) | [troubleshooting.fi.md](docs/troubleshooting.fi.md) |
| Privacy | [privacy.en.md](docs/privacy.en.md) | [privacy.fi.md](docs/privacy.fi.md) |

Component docs: [backend/README.md](backend/README.md) · [frontend/README.md](frontend/README.md)

## License

MIT License — see [LICENSE](LICENSE). Copyright (c) 2026 Marko Virta.

## GitHub topics

`whisper` `faster-whisper` `speech-to-text` `real-time-translation` `finnish` `ukrainian` `english` `fastapi` `websocket` `react` `vite` `local-ai` `windows`

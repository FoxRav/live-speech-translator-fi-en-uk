# Backend

Python FastAPI backend for local live Finnish speech translation (FI → EN + UK).

## Quick start

```powershell
cd backend
.\setup.ps1
.\install_torch_gpu.ps1    # optional, NVIDIA GPU
.\check_gpu.ps1
.\start.ps1
```

Server: http://127.0.0.1:8000

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Server health, GPU info, pipeline status |
| `WS /ws` | WebSocket: start, stop, clear, save_log, live translations |

## Manual run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Configuration

Copy `.env.example` to `.env`. See [../docs/configuration.en.md](../docs/configuration.en.md).

## Test without microphone

```powershell
.\.venv\Scripts\python.exe -m app.asr_test --input test_audio.wav
```

## Logs

Sessions save to `logs/session_YYYYMMDD_HHMMSS.jsonl` (gitignored).

## Modules

| Module | Role |
|--------|------|
| `main.py` | FastAPI + WebSocket |
| `pipeline.py` | Audio → ASR → translation |
| `asr.py` | Whisper ASR |
| `translator.py` | OPUS / NLLB / hybrid |
| `fi_text.py` | Finnish ASR cleanup |

Full architecture: [../docs/architecture.en.md](../docs/architecture.en.md)

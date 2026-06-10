# Contributing

Thank you for your interest in contributing to Live Speech Translator FI.

## Development setup (Windows)

```powershell
cd live-speech-translator-fi
.\setup_backend.ps1
.\install_torch_gpu.ps1    # optional, NVIDIA GPU
cd backend
.\check_gpu.ps1

cd ..\frontend
npm install
```

## Running locally

```powershell
# Terminal 1
cd backend
.\start.ps1

# Terminal 2 (repo root)
.\start_frontend.ps1
```

Open http://localhost:5173

## Guidelines

- Keep changes focused and test manually on Windows when touching audio, ASR, or WebSocket code.
- Do not commit `.env`, `backend/.venv/`, `node_modules/`, model weights, or session logs.
- Match existing code style: typed Python, minimal scope, no unnecessary refactors.
- Update `docs/` when changing configuration or startup commands.
- Add tests for pure functions (e.g. `fi_text.py`) when possible; avoid GPU/model download in CI.

## Pull requests

1. Fork and create a feature branch.
2. Describe the change and how you tested it.
3. Ensure no secrets or personal session data are included.

See [docs/installation.en.md](docs/installation.en.md) for full setup details.

# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-06-09

### Added

- Open-source repository structure for GitHub release
- English `README.md` and Finnish `README.fi.md`
- Documentation in `docs/` (Finnish and English)
- MIT License
- `SECURITY.md`, `CONTRIBUTING.md`, and anonymized `examples/sample-session.jsonl`
- Expanded `.gitignore` for models, logs, venv, and local artifacts

### Changed

- Repository folder renamed to `live-speech-translator-fi`
- Personal default hotword removed from `config.py` (use `.env` instead)

### Unchanged (runtime)

- FastAPI backend, WebSocket protocol, ASR, VAD, and translation pipeline
- Existing PowerShell startup scripts at repository root and `backend/`

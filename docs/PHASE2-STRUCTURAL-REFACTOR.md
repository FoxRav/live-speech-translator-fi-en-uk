# Phase 2 — Structural Refactor Proposal

**Status:** Not executed. Awaiting review after Phase 1 GitHub release.

## Goals

- Cleaner repository layout without changing runtime behavior
- Better testability and contributor onboarding
- Preserve Windows PowerShell workflows during migration

## Proposed changes

### 1. Scripts consolidation

| Action | Detail |
|--------|--------|
| Move | Root `*.ps1` → `scripts/` as canonical copies |
| Move | `backend/*.ps1` → `backend/scripts/` |
| Keep | Thin wrapper shims at old paths for one release cycle |
| Add | `scripts/dev.ps1` — start backend + frontend |
| Add | `scripts/setup_frontend.ps1` — `npm install` in frontend |

**Authoritative scripts after Phase 2:**

- `scripts/setup_backend.ps1`
- `scripts/install_torch_gpu.ps1`
- `scripts/start_backend.ps1`
- `scripts/start_frontend.ps1`
- `scripts/check_gpu.ps1`

### 2. Backend module extraction

| Action | Detail |
|--------|--------|
| Extract | WebSocket handler from `main.py` → `app/websocket.py` |
| Rename | `logger.py` → `logging_config.py` (update imports) |
| Keep | `audio_capture.py`, `devices.py`, `gpu_check.py`, `asr_test.py` |

No changes to WebSocket message protocol or pipeline logic.

### 3. Frontend reorganization

```
frontend/src/
  components/TranslationDisplay.tsx
  hooks/useTranslatorWebSocket.ts   # optional thin wrapper
  lib/websocket.ts
  types/index.ts
  styles/global.css
```

Update imports in `App.tsx` and `main.tsx` only.

### 4. Tests and tooling

| Action | Detail |
|--------|--------|
| Add | `pyproject.toml` with pytest, ruff (dev deps) |
| Add | `tests/test_config.py` — settings load smoke test |
| Add | `tests/test_pipeline.py` — `TranslationPipeline()` init without `.load()` |
| Keep | `tests/test_fi_text.py` |

No GPU or model download in tests.

### 5. Not in Phase 2

- Changing `MODELS_DIR` path
- ASR / VAD / translation algorithm changes
- WebSocket protocol changes
- Removing legacy PS shim scripts (until verified)

## Execution order (when approved)

1. Add `pyproject.toml` + tests (no moves)
2. Extract `websocket.py` + rename `logging_config.py`
3. Reorganize frontend `src/`
4. Move scripts + add shims
5. Update docs and README paths
6. Remove shims in follow-up release

## Risk assessment

| Change | Risk |
|--------|------|
| Script moves | Medium — mitigated by shims |
| websocket.py extract | Low — move only |
| logger rename | Low — import updates |
| Frontend folder moves | Low — import updates |
| pyproject.toml | Low — additive |

## Approval checklist

- [ ] Script shim removal timeline agreed
- [ ] Frontend import paths verified
- [ ] All startup commands tested on Windows
- [ ] CI strategy defined (CPU-only tests)

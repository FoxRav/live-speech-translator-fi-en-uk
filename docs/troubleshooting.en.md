# Troubleshooting

| Problem | Solution |
|---------|----------|
| `transformers is not installed` | Re-run `.\setup.ps1`; use transformers 4.x (not 5.x) |
| `Translation model load failed` | Run `.\install_torch_gpu.ps1`; check `.\check_gpu.ps1` |
| NLLB fails to load | Normal on 6 GB VRAM — hybrid uses OPUS fallback |
| `cublas64_12.dll` missing | Install CUDA Toolkit 12 or set `ASR_DEVICE=cpu` |
| Nothing happens on Start | Wait for model download (2–15 min); check backend log |
| Poor Finnish / translation | Speak full sentences; verify `large-v3` + `cuda` |
| Compound word errors | Add `ASR_HOTWORDS` / `ASR_INITIAL_PROMPT` to `.env` |
| VRAM OOM | Use `ASR_MODEL_SIZE=medium` or `TRANSLATE_DEVICE=cpu` |
| WebSocket won't connect | Is backend on port 8000? Refresh browser |
| Port 8000 in use (`Errno 10048`) | Backend already running — use it or stop the process |
| `Backend on jo kaynnissa` message | Normal — run `.\start_frontend.ps1` only |
| Terminal parses script output as commands | Paste commands only, not script text |
| Wrong Python / pip | Use `backend\.venv\Scripts\python.exe` only |
| `start.ps1` fails | Run uvicorn manually (see Finnish doc) |

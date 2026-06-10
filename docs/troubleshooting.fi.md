# Vianetsintä

| Ongelma | Ratkaisu |
|---------|----------|
| `transformers is not installed` | Aja `.\setup.ps1` uudelleen; varmista transformers 4.x (ei 5.x) |
| `Translation model load failed` | Aja `.\install_torch_gpu.ps1`; tarkista `.\check_gpu.ps1` |
| NLLB ei lataudu / kaatuu | Normaalia 6 GB VRAM:lla — hybrid käyttää OPUS-fallbackia |
| `cublas64_12.dll` puuttuu | Asenna CUDA Toolkit 12 tai `ASR_DEVICE=cpu` |
| Mitään ei tapahdu Käynnistä-painalluksella | Odota mallien lataus (2–15 min); tarkista backend-loki |
| Käännös / suomi väärin | Puhu kokonaisia lauseita; `ASR_MODEL_SIZE=large-v3` + `ASR_DEVICE=cuda` |
| Yhdyssana väärin | Lisää `ASR_HOTWORDS` / `ASR_INITIAL_PROMPT` → `.env` |
| VRAM loppuu (OOM) | `ASR_MODEL_SIZE=medium` tai `TRANSLATE_DEVICE=cpu` |
| WebSocket ei yhdistä | Backend portissa 8000? F5 selaimessa |
| Portti 8000 varattu (`Errno 10048`) | Backend jo käynnissä — käytä sitä tai sammuta prosessi |
| `start.ps1` sanoo "Backend on jo kaynnissa" | Normaalia — aja `.\start_frontend.ps1` |
| Terminaali: `status:` / `Kayta` ei tunnistu | Kopioit skriptin tulosteen — aja komento, älä tekstiä |
| `pip`/Python sekoittuu | Käytä vain `backend\.venv\Scripts\python.exe` |
| `start.ps1` ei toimi | `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |

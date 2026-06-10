# Arkkitehtuuri

## Datavirta

```
Mikrofoni (sounddevice)
  → Energy VAD (vad.py)
  → ASR Whisper large-v3 (asr.py, ctranslate2)
  → Suomen tekstikorjaus (fi_text.py)
  → Käännös hybrid (translator.py)
  → WebSocket (main.py)
  → React UI (frontend/)
```

## Backend-moduulit

| Moduuli | Vastuu |
|---------|--------|
| `main.py` | FastAPI, `/health`, WebSocket `/ws` |
| `pipeline.py` | Live-silmukka, jonotus, callbacks |
| `audio_capture.py` | Mikrofonin capture |
| `vad.py` | Puhesegmenttien tunnistus |
| `asr.py` | faster-whisper transkriptio |
| `fi_text.py` | ASR-jälkikäsittely, lausejako |
| `translator.py` | OPUS / NLLB / hybrid |
| `devices.py` | GPU-tarkistus |
| `logger.py` | Session JSONL -loki |
| `config.py` | Pydantic-asetukset |

## Frontend

| Tiedosto | Vastuu |
|----------|--------|
| `App.tsx` | UI, fullscreen, asetukset |
| `TranslationDisplay.tsx` | Vierivä tekstilista |
| `websocket.ts` | WebSocket-yhteys |
| `types.ts` | Viestityypit |

## Mallit (ladataan automaattisesti)

| Malli | Tarkoitus |
|-------|-----------|
| `Systran/faster-whisper-large-v3` | Suomi → teksti |
| `Helsinki-NLP/opus-mt-fi-en` | Suomi → englanti |
| `Helsinki-NLP/opus-mt-en-uk` | Englanti → ukraina (fallback) |
| `facebook/nllb-200-distilled-600M` | Suomi → ukraina |

## Riippuvuudet

Katso `backend/requirements.txt`. Torch asennetaan erikseen GPU:ta varten.

## Projektirakenne

```
live-speech-translator-fi/
  backend/app/          Python-lähdekoodi
  backend/models/       Ladatut mallit (gitignored)
  backend/logs/         Session-lokit (gitignored)
  frontend/src/         React UI
  docs/                 Dokumentaatio
  examples/             Esimerkkidata
```

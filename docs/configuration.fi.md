# Konfiguraatio

Kopioi `backend/.env.example` → `backend/.env`:

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

# Oman sanaston lisäys:
# ASR_HOTWORDS=helluntai seurakunta kaupungintalo tapaaminen ...
# ASR_INITIAL_PROMPT=Tama on suomenkielinen puhe. Seurakunta, kokous, ...
```

## Asetukset

| Asetus | Vaikutus |
|--------|----------|
| `ASR_MODEL_SIZE=large-v3` | Paras suomen puheentunnistus (oletus) |
| `ASR_MODEL_SIZE=medium` | Hyvä suomi, vähemmän VRAM |
| `ASR_DEVICE=cuda` | Whisper GPU:lla |
| `ASR_BEAM_SIZE=5` | Tarkin ASR (hitaampi) |
| `ASR_HOTWORDS` | Whisper-hotwords harvinaisille sanoille |
| `ASR_INITIAL_PROMPT` | Kontekstivihje ASR:lle |
| `VAD_SILENCE_DURATION_MS` | Tauko ennen lauseen päättymistä (oletus 1500 ms) |
| `VAD_MIN_SPEECH_DURATION_MS` | Lyhin puhepätkä (oletus 1200 ms) |
| `TRANSLATION_ENGINE=hybrid` | OPUS FI→EN + NLLB/OPUS UK (oletus) |
| `TRANSLATION_ENGINE=opus` | Nopein |
| `TRANSLATION_ENGINE=nllb` | Paras käännös, hitain |

## Suomen ASR-parannukset

| Kerros | Tiedosto | Mitä tekee |
|--------|----------|------------|
| Hotwords + prompt | `app/config.py` / `.env` | Ohjaa Whisperia |
| Tekstikorjaus | `app/fi_text.py` | Korjaa ASR-virheitä (ei sensuuria) |
| Lausejako | `app/pipeline.py` | Kääntää lause kerrallaan |
| Hallusinaatiosuodatus | `app/asr.py` | Hylkää tyhjät segmentit |

Jos sana tunnistuu väärin, lisää se `ASR_HOTWORDS` ja `ASR_INITIAL_PROMPT` `.env`-tiedostoon.

## Hybrid-moottori ja 6 GB VRAM

1. **OPUS FI→EN** (GPU)
2. **NLLB FI→UK** (yrittää ladata)

Jos NLLB ei lataudu, käytetään **OPUS EN→UK** -fallbackia.

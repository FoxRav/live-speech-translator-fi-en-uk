# Asennus

## Laitteistovaatimukset

### Minimi (vain CPU)

| Komponentti | Vaatimus |
|-------------|----------|
| Käyttöjärjestelmä | Windows 11 |
| CPU | 4+ ytintä |
| RAM | **16 GB** (suositus **24 GB**) |
| Levytila | **~8 GB** vapaata |
| Mikrofoni | Headset tai USB-mikrofoni |
| GPU | Ei pakollinen |

CPU-tilassa yhden lauseen käsittely kestää tyypillisesti **15–40 sekuntia**.

### Suositus (NVIDIA GPU)

| Komponentti | Vaatimus |
|-------------|----------|
| GPU | NVIDIA RTX, **6+ GB VRAM** |
| RAM | **24 GB** |
| CUDA | NVIDIA-ajurit + CUDA Toolkit 12 (`cublas64_12.dll`) |

### Levytilan jako (arvio)

| Malli / osa | Koko (noin) |
|-------------|-------------|
| faster-whisper `large-v3` | ~3 GB |
| facebook/nllb-200-distilled-600M | ~1,2 GB |
| OPUS-MT (fi-en + en-uk) | ~1 GB |
| Python `.venv` + pip-paketit | ~4–6 GB |
| PyTorch CUDA (cu124) | ~2,5 GB |
| **Yhteensä** | **~10–14 GB** |

Mallit tallentuvat kansioon `backend/models/`.

## Ohjelmistovaatimukset

| Ohjelma | Versio |
|---------|--------|
| Python | 3.10 tai 3.11 |
| Node.js | 18+ |
| npm | mukana Node-asennuksessa |
| Selain | Chrome, Edge tai Firefox |

## Asennus (vain projektin `.venv`)

**Tärkeää:** Kaikki Python-paketit asennetaan vain kansioon `backend\.venv`. Älä käytä koneen globaalia `pip install` -komentoa.

### Vaihe 1 — Backend-ympäristö

```powershell
cd live-speech-translator-fi
.\setup_backend.ps1
```

Tai `backend`-kansiosta: `.\setup.ps1`

### Vaihe 2 — PyTorch GPU (vain `.venv`)

```powershell
.\install_torch_gpu.ps1
```

Lataa PyTorch 2.5.1+cu124 vain projektin virtuaaliympäristöön. Sulje backend ennen asennusta.

### Vaihe 3 — GPU-tarkistus

```powershell
cd backend
.\check_gpu.ps1
```

### Vaihe 4 — Asetukset (valinnainen)

```powershell
copy .env.example .env
```

### Vaihe 5 — Frontend

```powershell
cd ..\frontend
npm install
```

## Käynnistys

**Terminaali 1 — backend:**

```powershell
cd live-speech-translator-fi\backend
.\start.ps1
```

**Terminaali 2 — frontend:**

```powershell
cd live-speech-translator-fi
.\start_frontend.ps1
```

Avaa selaimessa: **http://localhost:5173**

> Kopioi terminaaliin vain komentorivit, älä skriptin tulostetekstiä.

### Ensimmäinen käynnistys

Ensimmäisellä **Käynnistä**-painalluksella ladataan ML-mallit Hugging Facesta (internet tarvitaan). Tämä voi kestää **2–15 minuuttia**.

## Offline-käyttö

Kun mallit on ladattu kansioon `backend/models/`, ohjelma toimii ilman internetiä.

## Testaus ilman mikrofonia

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.asr_test --input test_audio.wav
```

Testi-WAV: mono, 16 kHz (tai ohjelma resamplaa).

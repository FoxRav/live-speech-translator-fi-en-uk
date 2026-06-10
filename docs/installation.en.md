# Installation

## Hardware requirements

### Minimum (CPU only)

| Component | Requirement |
|-----------|-------------|
| OS | Windows 11 |
| CPU | 4+ cores |
| RAM | 16 GB (24 GB recommended) |
| Disk | ~8 GB free |
| Microphone | Headset or USB mic |
| GPU | Not required |

CPU-only latency is typically **15–40 seconds** per sentence.

### Recommended (NVIDIA GPU)

| Component | Requirement |
|-----------|-------------|
| GPU | NVIDIA RTX, 6+ GB VRAM |
| RAM | 24 GB |
| CUDA | NVIDIA drivers + CUDA Toolkit 12 |

### Disk usage (estimate)

| Component | Size |
|-----------|------|
| faster-whisper `large-v3` | ~3 GB |
| NLLB distilled 600M | ~1.2 GB |
| OPUS-MT fi-en + en-uk | ~1 GB |
| Python `.venv` + packages | ~4–6 GB |
| PyTorch CUDA | ~2.5 GB |
| **Total** | **~10–14 GB** |

Models are cached in `backend/models/`.

## Software requirements

| Tool | Version |
|------|---------|
| Python | 3.10 or 3.11 |
| Node.js | 18+ |
| Browser | Chrome, Edge, or Firefox |

## Setup (project `.venv` only)

Install Python packages **only** into `backend/.venv`.

### Step 1 — Backend

```powershell
cd live-speech-translator-fi
.\setup_backend.ps1
```

Or from `backend/`: `.\setup.ps1`

### Step 2 — PyTorch GPU (optional)

```powershell
.\install_torch_gpu.ps1
```

Installs PyTorch 2.5.1+cu124 into the project venv only.

### Step 3 — GPU check

```powershell
cd backend
.\check_gpu.ps1
```

### Step 4 — Configuration (optional)

```powershell
copy .env.example .env
```

### Step 5 — Frontend

```powershell
cd ..\frontend
npm install
```

## Running

**Terminal 1 — backend:**

```powershell
cd live-speech-translator-fi\backend
.\start.ps1
```

**Terminal 2 — frontend:**

```powershell
cd live-speech-translator-fi
.\start_frontend.ps1
```

Open **http://localhost:5173**

### First run

Models download from Hugging Face on first **Start** click (2–15 minutes, internet required).

## Offline usage

After models are cached in `backend/models/`, the app works without internet.

## Testing without microphone

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.asr_test --input test_audio.wav
```

WAV should be mono 16 kHz (other rates are resampled).

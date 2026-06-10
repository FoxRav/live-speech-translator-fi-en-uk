# Privacy

## Local processing

- All speech recognition and translation runs **on your machine**.
- No OpenAI, Google, DeepL, or other cloud translation APIs at runtime.
- Internet is only needed for the initial model download from Hugging Face.

## Logs

- Session logs are stored in `backend/logs/session_*.jsonl`.
- Logs may contain **spoken text** verbatim.
- Do not share logs publicly without anonymization.
- Logs are gitignored and must not be committed.

## Censorship

- The app **does not censor** recognized speech.
- All ASR output is shown in the UI and may be saved to logs.

## Network

- Backend listens on `127.0.0.1:8000` by default.
- Do not expose the server to the public internet without additional security.

## Custom vocabulary

- Add domain terms via `.env` (`ASR_HOTWORDS`); avoid hardcoding personal data in source code.

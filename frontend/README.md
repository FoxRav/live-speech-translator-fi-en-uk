# Frontend

React + Vite browser UI for Live Speech Translator FI.

## Quick start

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Or from repo root: `.\start_frontend.ps1`

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Development server (port 5173) |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build |

## Backend proxy

`vite.config.ts` proxies `/health` and `/ws` to `http://127.0.0.1:8000` in development.

WebSocket client connects directly to port 8000 in dev mode (`websocket.ts`).

## Source files

| File | Role |
|------|------|
| `src/App.tsx` | Main UI, toolbar, settings, fullscreen |
| `src/TranslationDisplay.tsx` | Scrolling translation feed |
| `src/websocket.ts` | WebSocket client |
| `src/types.ts` | Message types |
| `src/styles.css` | Global styles |

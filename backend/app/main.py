"""FastAPI application with WebSocket endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.devices import get_compute_status
from app.pipeline import TranslationPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

pipeline = TranslationPipeline()


async def _preload_models() -> None:
    """Load ML models at startup so first Käynnistä is fast."""
    try:
        if not pipeline._asr._loaded:
            logger.info("Preloading ASR model...")
            await asyncio.to_thread(pipeline._asr.load)
        if not pipeline._translator.loaded:
            logger.info("Preloading translation models...")
            await asyncio.to_thread(pipeline._translator.load)
        logger.info("Models preloaded and ready")
    except Exception as exc:
        logger.warning("Model preload failed (will retry on start): %s", exc)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Backend starting")
    preload_task = asyncio.create_task(_preload_models())
    yield
    preload_task.cancel()
    if pipeline.state.status != "idle":
        await pipeline.stop()
    logger.info("Backend shutdown")


app = FastAPI(title="Local Live Translator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    state = pipeline.state
    asr_device = getattr(pipeline._asr, "_device", settings.asr_device)
    compute = get_compute_status()
    return {
        "status": "ok",
        "pipeline_status": state.status,
        "message": state.message,
        "session_log": pipeline.session_log_path or "",
        "asr_model": settings.asr_model_size,
        "asr_device": asr_device,
        "translate_device": settings.translate_device,
        "asr_cuda_available": compute.asr_cuda_available,
        "translate_cuda_available": compute.translate_cuda_available,
        "gpu_name": compute.gpu_name or "",
        "vram_gb": compute.vram_gb,
    }


async def _send_json(websocket: WebSocket, payload: dict[str, Any]) -> None:
    await websocket.send_text(json.dumps(payload, ensure_ascii=False))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("WebSocket client connected")

    async def on_status(status: str, message: str) -> None:
        await _send_json(websocket, {"type": "status", "status": status, "message": message})

    async def on_partial(fi_partial: str) -> None:
        await _send_json(websocket, {"type": "partial", "fi_partial": fi_partial})

    async def on_translation(payload: dict[str, object]) -> None:
        await _send_json(websocket, payload)

    async def on_error(message: str) -> None:
        await _send_json(websocket, {"type": "error", "message": message})

    pipeline.set_callbacks(on_status, on_partial, on_translation, on_error)

    state = pipeline.state
    await on_status(state.status, state.message)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await on_error("Invalid JSON message")
                continue

            command = data.get("command", "")
            logger.info("Received command: %s", command)

            if command == "start":
                if pipeline.is_busy:
                    state = pipeline.state
                    await on_status(state.status, state.message)
                else:
                    asyncio.create_task(pipeline.start())
            elif command == "stop":
                await pipeline.stop()
            elif command == "clear":
                await _send_json(websocket, {"type": "cleared"})
            elif command == "ping":
                await _send_json(websocket, {"type": "pong"})
            elif command == "save_log":
                md_path = pipeline.export_session_markdown()
                await _send_json(
                    websocket,
                    {
                        "type": "log_saved",
                        "jsonl_path": pipeline.session_log_path or "",
                        "markdown_path": md_path or "",
                    },
                )
            else:
                await on_error(f"Unknown command: {command}")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected (pipeline keeps running until STOP)")
    except Exception as exc:
        logger.exception("WebSocket error")
        try:
            await on_error(f"WebSocket error: {exc}")
        except Exception:
            pass

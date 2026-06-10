"""Machine translation: FI -> EN -> UK."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from app.config import TranslationEngine, settings
from app.devices import resolve_nllb_device, resolve_torch_device

logger = logging.getLogger(__name__)


def _load_seq2seq_model(model_cls: Any, model_id: str, device: str) -> Any:
    import torch

    dtype = torch.float16 if device == "cuda" else torch.float32
    load_kwargs: dict[str, Any] = {
        "cache_dir": str(settings.models_dir),
        "torch_dtype": dtype,
        "use_safetensors": True,
    }
    if device == "cuda":
        load_kwargs["device_map"] = "cuda"
        model = model_cls.from_pretrained(model_id, **load_kwargs)
        return model.eval()
    load_kwargs["device_map"] = "cpu"
    model = model_cls.from_pretrained(model_id, **load_kwargs)
    return model.eval()


class TranslationModelLoadError(RuntimeError):
    pass


class TranslationError(RuntimeError):
    pass


@dataclass(frozen=True)
class TranslationResult:
    en: str
    uk: str
    en_latency_ms: int
    uk_latency_ms: int


class OpusTranslator:
    def __init__(self, *, fi_en_only: bool = False) -> None:
        self._fi_en_only = fi_en_only
        self._device = resolve_torch_device(settings.translate_device)
        self._fi_en_tokenizer: Any = None
        self._fi_en_model: Any = None
        self._en_uk_tokenizer: Any = None
        self._en_uk_model: Any = None
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return

        try:
            from transformers import MarianMTModel, MarianTokenizer
        except ImportError as exc:
            raise TranslationModelLoadError(f"transformers import failed: {exc}") from exc

        settings.models_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info("Loading OPUS FI->EN model: %s", settings.opus_fi_en_model)
            self._fi_en_tokenizer = MarianTokenizer.from_pretrained(
                settings.opus_fi_en_model,
                cache_dir=str(settings.models_dir),
            )
            self._fi_en_model = _load_seq2seq_model(
                MarianMTModel, settings.opus_fi_en_model, self._device
            )

            if not self._fi_en_only:
                logger.info("Loading OPUS EN->UK model: %s", settings.opus_en_uk_model)
                self._en_uk_tokenizer = MarianTokenizer.from_pretrained(
                    settings.opus_en_uk_model,
                    cache_dir=str(settings.models_dir),
                )
                self._en_uk_model = _load_seq2seq_model(
                    MarianMTModel, settings.opus_en_uk_model, self._device
                )
        except Exception as exc:
            raise TranslationModelLoadError(f"Failed to load OPUS models: {exc}") from exc

        self._loaded = True
        logger.info("OPUS translation models loaded on %s", self._device)

    def _translate(self, text: str, tokenizer: Any, model: Any) -> tuple[str, int]:
        import torch

        start = time.perf_counter()
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
        )
        inputs = {key: value.to(self._device) for key, value in inputs.items()}
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=settings.translate_max_tokens,
                num_beams=settings.translate_num_beams,
            )
        result = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return result, latency_ms

    def translate_fi_en(self, fi_text: str) -> tuple[str, int]:
        if not self._loaded:
            raise TranslationError("OPUS translator is not loaded.")
        return self._translate(fi_text, self._fi_en_tokenizer, self._fi_en_model)

    def translate(self, fi_text: str) -> TranslationResult:
        if not self._loaded:
            raise TranslationError("OPUS translator is not loaded.")

        en_text, en_ms = self.translate_fi_en(fi_text)
        if self._fi_en_only:
            raise TranslationError("OPUS fi-en-only mode cannot translate to UK without hybrid engine.")

        uk_text, uk_ms = self._translate(en_text, self._en_uk_tokenizer, self._en_uk_model)
        return TranslationResult(en=en_text, uk=uk_text, en_latency_ms=en_ms, uk_latency_ms=uk_ms)


class NLLBTranslator:
    def __init__(self) -> None:
        self._device = resolve_nllb_device(settings.translate_device)
        self._tokenizer = None
        self._model = None
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise TranslationModelLoadError(f"transformers import failed: {exc}") from exc

        settings.models_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info("Loading NLLB model: %s", settings.nllb_model)
            self._tokenizer = AutoTokenizer.from_pretrained(
                settings.nllb_model,
                cache_dir=str(settings.models_dir),
            )
            self._model = _load_seq2seq_model(
                AutoModelForSeq2SeqLM, settings.nllb_model, self._device
            )
            logger.info("NLLB translation model loaded on %s", self._device)
        except Exception as exc:
            raise TranslationModelLoadError(f"Failed to load NLLB model: {exc}") from exc

        self._loaded = True

    def _translate_single(self, text: str, src: str, tgt: str) -> tuple[str, int]:
        import torch

        if self._tokenizer is None or self._model is None:
            raise TranslationError("NLLB translator is not loaded.")

        start = time.perf_counter()
        self._tokenizer.src_lang = src
        inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {key: value.to(self._device) for key, value in inputs.items()}
        forced_bos = self._tokenizer.convert_tokens_to_ids(tgt)
        with torch.inference_mode():
            outputs = self._model.generate(
                **inputs,
                forced_bos_token_id=forced_bos,
                max_new_tokens=settings.translate_max_tokens,
                num_beams=settings.translate_num_beams,
            )
        translated = self._tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return translated, latency_ms

    def translate(self, fi_text: str) -> TranslationResult:
        if not self._loaded:
            raise TranslationError("NLLB translator is not loaded.")

        with ThreadPoolExecutor(max_workers=2) as pool:
            en_future = pool.submit(
                self._translate_single, fi_text, settings.nllb_fi_code, settings.nllb_en_code
            )
            uk_future = pool.submit(
                self._translate_single, fi_text, settings.nllb_fi_code, settings.nllb_uk_code
            )
            en_text, en_ms = en_future.result()
            uk_text, uk_ms = uk_future.result()
        return TranslationResult(en=en_text, uk=uk_text, en_latency_ms=en_ms, uk_latency_ms=uk_ms)


class HybridTranslator:
    """OPUS FI->EN + NLLB FI->UK; falls back to OPUS EN->UK if NLLB cannot load."""

    def __init__(self) -> None:
        self._opus = OpusTranslator(fi_en_only=True)
        self._nllb = NLLBTranslator()
        self._opus_uk: OpusTranslator | None = None
        self._use_nllb_uk = True
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        self._opus.load()
        try:
            self._nllb.load()
            logger.info("Hybrid translator: OPUS FI->EN + NLLB FI->UK")
        except TranslationModelLoadError as exc:
            logger.warning("NLLB load failed (%s) — UK via OPUS EN->UK", exc)
            self._use_nllb_uk = False
            self._opus_uk = OpusTranslator()
            self._opus_uk.load()
            logger.info("Hybrid translator: OPUS FI->EN + OPUS EN->UK (fallback)")
        self._loaded = True

    def _translate_uk(self, fi_text: str, en_text: str) -> tuple[str, int]:
        if self._use_nllb_uk:
            return self._nllb._translate_single(
                fi_text, settings.nllb_fi_code, settings.nllb_uk_code
            )
        assert self._opus_uk is not None
        return self._opus_uk._translate(en_text, self._opus_uk._en_uk_tokenizer, self._opus_uk._en_uk_model)

    def translate(self, fi_text: str) -> TranslationResult:
        if not self._loaded:
            raise TranslationError("Hybrid translator is not loaded.")

        en_text, en_ms = self._opus.translate_fi_en(fi_text)
        uk_text, uk_ms = self._translate_uk(fi_text, en_text)
        return TranslationResult(en=en_text, uk=uk_text, en_latency_ms=en_ms, uk_latency_ms=uk_ms)


class Translator:
    """Facade that selects translation engine from config."""

    def __init__(self, engine: TranslationEngine | None = None) -> None:
        engine = engine or settings.translation_engine
        if engine == "opus":
            self._impl: OpusTranslator | NLLBTranslator | HybridTranslator = OpusTranslator()
        elif engine == "nllb":
            self._impl = NLLBTranslator()
        else:
            self._impl = HybridTranslator()
        self.engine = engine

    @property
    def loaded(self) -> bool:
        return getattr(self._impl, "_loaded", False)

    def load(self) -> None:
        self._impl.load()

    def translate(self, fi_text: str) -> TranslationResult:
        return self._impl.translate(fi_text)

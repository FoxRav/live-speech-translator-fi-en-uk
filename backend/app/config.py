"""Application configuration."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

TranslationEngine = Literal["opus", "nllb", "hybrid"]
AsrModelSize = Literal["base", "small", "medium", "large-v3"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ASR — Whisper large-v3 on GPU = best Finnish speech recognition in this stack
    asr_model_size: AsrModelSize = "large-v3"
    asr_language: str = "fi"
    asr_device: str = "cuda"
    asr_compute_type: str = "float16"
    asr_cpu_compute_type: str = "int8"
    asr_beam_size: int = 5
    asr_best_of: int = 5
    asr_cpu_threads: int = 0
    asr_context_chars: int = 350
    asr_context_segments: int = 2
    asr_initial_prompt: str = (
        "Tämä on suomenkielinen puhe. Kirjakieli ja puhekieli. "
        "Kaikki sanat tunnistetaan sellaisenaan. "
        "Tervetuloa, seurakunta, helluntai, helluntaiseurakunta, helluntaiseurakuntaan, "
        "kirkko, Jumala, rukous, kiitos, anteeksi, saarna, jumalanpalvelus, "
        "tänne, eteenpäin, suunnitelma, tapaaminen, työnhaku, keskustelu, "
        "käännös, ymmärtää, puhe, "
        "nyt, sitten, asiat, menevät, hei, varannut, ajan."
    )
    asr_hotwords: str = (
        "suomi suomenkieli ymmärtää tervetuloa seurakunta helluntai "
        "helluntaiseurakunta helluntaiseurakuntaan helluntaiseurakunnassa "
        "kirkko rukous saarna jumalanpalvelus "
        "suunnitelma tapaaminen työnhaku keskustelu eteenpäin "
        "nyt sitten asiat menevät hei varannut ajan käännös miksi miten "
        "tämä tuo minä sinä me te"
    )
    asr_min_avg_logprob: float = -0.9
    asr_publish_min_logprob: float = -0.5
    asr_max_no_speech_prob: float = 0.48
    asr_condition_on_previous: bool = False
    asr_patience: float = 1.5
    asr_compression_ratio_threshold: float = 2.2
    asr_length_penalty: float = 1.0
    asr_whisper_vad_filter: bool = True
    asr_hallucination_silence_threshold: float = 2.0

    # Audio
    sample_rate: int = 16000
    chunk_duration_sec: float = 2.0
    overlap_duration_sec: float = 0.4
    audio_block_size: int = 1024

    # VAD — longer minimum speech = fuller Finnish sentences for ASR
    vad_energy_threshold: float = 0.008
    vad_silence_duration_ms: int = 1500
    vad_min_speech_duration_ms: int = 1200
    vad_max_chunk_duration_sec: float = 8.0

    # Translation (secondary to ASR; hybrid keeps EN fast + UK quality)
    translation_engine: TranslationEngine = "hybrid"
    translate_device: str = "cuda"
    translate_num_beams: int = 4
    translate_max_tokens: int = 128
    opus_fi_en_model: str = "Helsinki-NLP/opus-mt-fi-en"
    opus_en_uk_model: str = "Helsinki-NLP/opus-mt-en-uk"
    nllb_model: str = "facebook/nllb-200-distilled-600M"
    nllb_fi_code: str = "fin_Latn"
    nllb_en_code: str = "eng_Latn"
    nllb_uk_code: str = "ukr_Cyrl"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Timeouts (seconds)
    asr_timeout_sec: float = 120.0
    translate_timeout_sec: float = 120.0

    # Filtering
    min_transcript_length: int = 2
    duplicate_similarity_threshold: float = 0.85

    # Paths
    models_dir: Path = MODELS_DIR
    logs_dir: Path = LOGS_DIR


settings = Settings()

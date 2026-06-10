"""Session logging to JSONL files."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

from app.config import settings


@dataclass(frozen=True)
class TranslationLogEntry:
    timestamp: str
    fi: str
    en: str
    uk: str
    asr_model: str
    translation_engine: str
    latency_ms: int
    asr_ms: int = 0
    translate_en_ms: int = 0
    translate_uk_ms: int = 0


class SessionLogger:
    def __init__(self) -> None:
        self._file: IO[str] | None = None
        self._path: Path | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    def start_session(self) -> Path:
        settings.logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = settings.logs_dir / f"session_{timestamp}.jsonl"
        self._file = self._path.open("a", encoding="utf-8")
        return self._path

    def log_translation(self, entry: TranslationLogEntry) -> None:
        if self._file is None:
            return
        self._file.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def export_markdown(self) -> Path | None:
        if self._path is None or not self._path.exists():
            return None

        md_path = self._path.with_suffix(".md")
        lines = ["# Live Translation Session", ""]
        segment = 1

        with self._path.open("r", encoding="utf-8") as source:
            for raw_line in source:
                data = json.loads(raw_line)
                lines.extend(
                    [
                        f"## Segment {segment}",
                        "",
                        "FI:",
                        data.get("fi", ""),
                        "",
                        "EN:",
                        data.get("en", ""),
                        "",
                        "UK:",
                        data.get("uk", ""),
                        "",
                    ]
                )
                segment += 1

        md_path.write_text("\n".join(lines), encoding="utf-8")
        return md_path


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

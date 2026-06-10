"""Finnish transcript normalization — grammar fixes only, never censorship."""

from __future__ import annotations

import re

# Phrase-level fixes first (Whisper truncates or garbles endings).
_PHRASE_FIXES: tuple[tuple[str, str], ...] = (
    (
        r"\bniin saatanan huono ymmärrä\b",
        "niin saatanan huonoa ymmärtää",
    ),
    (r"\bhuono ymmärrä\b", "huonoa ymmärtää"),
    (r"\bei edes käännä kaikkea\b", "ei edes käännä kaikkea"),
    (r"\bterve tuloa\b", "tervetuloa"),
    (r"\bkäännös on niin\b", "käännös on niin"),
    (r"\bmitä tämä käännös\b", "mitä tämä käännös"),
    (r"\bsuomen kieltä\b", "suomen kieltä"),
    (r"\bsuomen kieli\b", "suomen kieli"),
    (r"\bpuheen tunnistus\b", "puheentunnistus"),
    (r"\blive käännös\b", "livekäännös"),
    (r"\bkäännös työtä\b", "käännöstyötä"),
    (r"\bkäännös työ\b", "käännöstyö"),
    (r"\bgpu-tehot\b", "GPU-tehot"),
    (r"\bgpu tehot\b", "GPU-tehot"),
    (r"\bnopean maksi\b", "nopeammaksi"),
    (r"\btyön haku\b", "työnhaku"),
    (r"\btyon haku\b", "työnhaku"),
    (r"\btapaamis ajan\b", "tapaamisajan"),
    (r"\bsuunnitelman laatimiseen\b", "suunnitelman laatimiseen"),
    (r"\bmenee eteenpäin\b", "menevät eteenpäin"),
    # Whisper splits "helluntaiseurakunta(an)" into "helluun/hellun tai seurakunta(an)"
    (r"\bhelluun tai helluun,? helluun tai\b", "helluntaiseurakuntaan"),
    (r"\bhelluun tai helluun\b", "helluntaiseurakuntaan"),
    (r"\bhellun tai hellun\b", "helluntaiseurakuntaan"),
    (r"\bhelluun tai seurakuntaan\b", "helluntaiseurakuntaan"),
    (r"\bhellun tai seurakuntaan\b", "helluntaiseurakuntaan"),
    (r"\bhelluun tai seurakunta\b", "helluntaiseurakunta"),
    (r"\bhellun tai seurakunta\b", "helluntaiseurakunta"),
    (r"\bkirjoittaa helluun tai seurakuntaan\b", "kirjoittaa helluntaiseurakuntaan"),
    (r"\bkirjoittaa hellun tai seurakuntaan\b", "kirjoittaa helluntaiseurakuntaan"),
    (r"\bmitä ihme helluun\b", "mitä ihme helluntai"),
    (r"\bmitä ihme hellun\b", "mitä ihme helluntai"),
)

# Word-level phonetic and grammar corrections.
_WORD_FIXES: tuple[tuple[str, str], ...] = (
    (r"\bymmärrä\b", "ymmärtää"),
    (r"\bymmarra\b", "ymmärtää"),
    (r"\bymmarrys\b", "ymmärrys"),
    (r"\bymmarta\b", "ymmärtää"),
    (r"\bymmärtä\b", "ymmärtää"),
    (r"\bpuheeta\b", "puheita"),
    (r"\bpuheetta\b", "puhetta"),
    (r"\btanne\b", "tänne"),
    (r"\btanaan\b", "tänään"),
    (r"\btaalla\b", "täällä"),
    (r"\bhyvaa\b", "hyvää"),
    (r"\bpaiva[aä]?\b", "päivä"),
    (r"\bhännös\b", "käännös"),
    (r"\bhannos\b", "käännös"),
    (r"\bpaikuttaa\b", "vaikuttaa"),
    (r"\bpaikutta\b", "vaikuttaa"),
    (r"\bmitäs\b", "mitä"),
    (r"\bmitäs se\b", "mitä se"),
    (r"\bmitäs ne\b", "mitä ne"),
    (r"\bmitenäs\b", "mitenäs"),
    (r"\beiks\b", "eikö"),
    (r"\boon\b", "on"),
    (r"\bkuinka\b", "kuinka"),
    (r"\bkaanta\b", "kääntää"),
    (r"\bkaantaa\b", "kääntää"),
    (r"\bkaannos\b", "käännös"),
    (r"\bkaannetaan\b", "käännetään"),
    (r"\bsuomea\b", "suomea"),
    (r"\bsuomeksi\b", "suomeksi"),
    (r"\bvirittää\b", "virittää"),
    (r"\bjarjestelma\b", "järjestelmä"),
    (r"\bjarjestelman\b", "järjestelmän"),
)

# Join split compound words Whisper often produces.
_COMPOUND_FIXES: tuple[tuple[str, str], ...] = (
    (r"\bpuheen tunnistus\b", "puheentunnistus"),
    (r"\bpuhe tunnistus\b", "puheentunnistus"),
    (r"\bkäännös työ\b", "käännöstyö"),
    (r"\bkäännös työtä\b", "käännöstyö"),
    (r"\blive käännös\b", "livekäännös"),
    (r"\bseura kunta\b", "seurakunta"),
    (r"\bhelluntai seurakuntaan\b", "helluntaiseurakuntaan"),
    (r"\bhelluntai seurakunta\b", "helluntaiseurakunta"),
    (r"\bhelluntais eurakuntaan\b", "helluntaiseurakuntaan"),
    (r"\bhelluntais eurakunta\b", "helluntaiseurakunta"),
    (r"\btyö haku\b", "työnhaku"),
    (r"\btyo haku\b", "työnhaku"),
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")

# Only reject obvious ASR hallucinations — never profanity or emotional speech.
_GARBAGE_PHRASES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^tervetuloa on yhtään mitään\.?$", re.IGNORECASE | re.UNICODE),
    re.compile(r"^on yhtään mitään\.?$", re.IGNORECASE | re.UNICODE),
    re.compile(r"^kiitos kiitos kiitos\.?$", re.IGNORECASE | re.UNICODE),
)

_GARBAGE_WORDS = frozenset(
    {
        "hännös",
        "hannos",
        "maksi",
        "eluntaiseura",
        "dohjelmi",
        "paikuttaa",
    }
)

_FI_CHARS = re.compile(r"[a-zäöåA-ZÄÖÅ]", re.UNICODE)
_SENTENCE_START = re.compile(r"(^|[.!?]\s+)([a-zäöå])", re.UNICODE)
_CONSONANT_CLUSTER = re.compile(r"[^aeiouyäöåAEIOUYÄÖÅ\s]{6,}", re.UNICODE)


def split_finnish_sentences(text: str) -> list[str]:
    """Split transcript into sentences for per-sentence translation."""
    cleaned = text.strip()
    if not cleaned:
        return []
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(cleaned) if part.strip()]
    return parts if parts else [cleaned]


def normalize_finnish_asr(text: str) -> str:
    """Apply Finnish grammar/ASR fixes. Profanity and raw speech are preserved."""
    normalized = text.strip()
    for pattern, replacement in _PHRASE_FIXES:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE | re.UNICODE)
    for pattern, replacement in _COMPOUND_FIXES:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE | re.UNICODE)
    for pattern, replacement in _WORD_FIXES:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE | re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    def _capitalize(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2).upper()}"

    return _SENTENCE_START.sub(_capitalize, normalized)


def is_plausible_finnish(text: str) -> bool:
    cleaned = text.strip()
    if len(cleaned) < 2:
        return False

    for pattern in _GARBAGE_PHRASES:
        if pattern.search(cleaned):
            return False

    if _CONSONANT_CLUSTER.search(cleaned):
        return False

    letters = _FI_CHARS.findall(cleaned)
    if len(letters) < len(cleaned.replace(" ", "")) * 0.4:
        return False

    words = [w.lower() for w in cleaned.split()]
    if not words:
        return False

    if _GARBAGE_WORDS.intersection(words):
        return False

    vowel_words = sum(1 for w in words if re.search(r"[aeiouyäöå]", w))
    if vowel_words < len(words) * 0.5:
        return False

    return True


def should_publish_transcript(text: str, avg_logprob: float, min_logprob: float) -> bool:
    """Reject only hallucinations and empty noise — publish real speech including profanity."""
    if not is_plausible_finnish(text):
        return False
    if avg_logprob < min_logprob:
        return False
    return True

"""Tests for Finnish ASR post-processing."""

from app.fi_text import normalize_finnish_asr, should_publish_transcript, split_finnish_sentences


def test_fixes_ymmarra_grammar() -> None:
    raw = "Miksi tämä käännös on niin saatanan huono ymmärrä"
    fixed = normalize_finnish_asr(raw)
    assert "ymmärtää" in fixed
    assert "saatanan" in fixed


def test_preserves_profanity() -> None:
    raw = "Tämä on vittu huono ja saatanan paska"
    fixed = normalize_finnish_asr(raw)
    assert "vittu" in fixed
    assert "saatanan" in fixed
    assert "paska" in fixed


def test_fixes_puheeta() -> None:
    assert "puheita" in normalize_finnish_asr("mitälaisia puheeta tahansa")


def test_publish_allows_emotional_speech() -> None:
    text = normalize_finnish_asr("Miksi tämä käännös on niin saatanan huonoa ymmärtää")
    assert should_publish_transcript(text, -0.4, -0.52)


def test_split_sentences() -> None:
    parts = split_finnish_sentences(
        "Nyt asiat menevät eteenpäin. Hei, olen varannut sinulle tapaamisajan."
    )
    assert len(parts) == 2
    assert parts[0].startswith("Nyt")
    assert "tapaamisajan" in parts[1]


def test_fixes_helluntaiseurakunta_garble() -> None:
    raw = "Miksi et osaa kirjoittaa hellun tai seurakuntaan?"
    fixed = normalize_finnish_asr(raw)
    assert "helluntaiseurakuntaan" in fixed
    assert "hellun tai" not in fixed


def test_fixes_helluun_tai_repetition() -> None:
    raw = "Tervetuloa helluun tai helluun, helluun tai"
    fixed = normalize_finnish_asr(raw)
    assert "helluntaiseurakuntaan" in fixed

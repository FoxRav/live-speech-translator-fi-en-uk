# Tietosuoja

## Lokaali käsittely

- Kaikki puheentunnistus ja käännös tapahtuu **omalla koneella**.
- Ei OpenAI-, Google-, DeepL- tai muita pilvi-API-kutsuja ajon aikana.
- Internetiä tarvitaan vain mallien ensilataukseen Hugging Facesta.

## Lokit

- Session-lokit tallentuvat `backend/logs/session_*.jsonl`.
- Lokit voivat sisältää **puhuttua tekstiä** sellaisenaan.
- Älä jaa lokit julkisesti ilman anonymisointia.
- Lokit on gitignored — ne eivät kuulu versionhallintaan.

## Sensurointi

- Ohjelma **ei sensuroi** tunnistettua puhetta.
- Kaikki ASR-tulos näytetään UI:ssa ja voi tallentua lokiin.

## Verkko

- Backend kuuntelee oletuksena `127.0.0.1:8000`.
- Älä avaa palvelinta suoraan internetiin ilman lisäsuojausta.

## Oman sanaston asetus

- Lisää domain-kohtaiset sanat `.env`:ään (`ASR_HOTWORDS`), älä kovakoodaa henkilötietoja lähdekoodiin.

import re

from card_downloader.decklist.models import DeckEntry, ParsedDeck
from card_downloader.decklist.normalize import normalize_name

_LINE_RE = re.compile(r"^\s*(?:(\d+)x?\s+)?(.+?)\s*$", re.IGNORECASE)
_SIDEBOARD_MARKERS = {"[sideboard]", "[maybeboard]"}


def parse_line(line: str) -> DeckEntry | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.lower() in _SIDEBOARD_MARKERS:
        return None  # caller handles section stop

    match = _LINE_RE.match(line)
    if not match:
        return None

    qty_str, name = match.groups()
    quantity = int(qty_str) if qty_str else 1
    normalised = normalize_name(name)
    if not normalised:
        return None
    return DeckEntry(quantity=quantity, name=normalised)


def parse_decklist(text: str) -> ParsedDeck:
    entries: list[DeckEntry] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower() in _SIDEBOARD_MARKERS:
            break
        entry = parse_line(line)
        if entry is not None:
            entries.append(entry)
    return ParsedDeck(entries=tuple(entries))

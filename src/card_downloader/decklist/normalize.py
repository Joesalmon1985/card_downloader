import unicodedata

_QUOTE_MAP = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
}


def normalize_name(name: str) -> str:
    """Normalise card name for Scryfall lookup."""
    text = unicodedata.normalize("NFC", name.strip())
    for src, dst in _QUOTE_MAP.items():
        text = text.replace(src, dst)
    while "  " in text:
        text = text.replace("  ", " ")
    return text

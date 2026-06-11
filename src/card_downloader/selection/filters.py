_EXCLUDED_LAYOUTS = frozenset({
    "token",
    "emblem",
    "vanguard",
    "art_series",
    "double_faced_token",
    "planar",
    "scheme",
    "augment",
    "host",
})

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.models import SelectionOptions


def hard_exclude(card: CardPrinting, opts: SelectionOptions) -> bool:
    if card.layout in _EXCLUDED_LAYOUTS:
        return True
    if card.digital and "paper" not in card.games:
        return True
    if card.image_status == "missing":
        return True
    if not card.has_playable_image():
        return True
    if card.primary_image_uri(opts.image_size) is None:
        return True
    return False

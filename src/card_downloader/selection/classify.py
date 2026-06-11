_SPECIAL_FRAME_EFFECTS = frozenset({
    "showcase",
    "extendedart",
    "inverted",
    "etched",
    "companion",
    "shatteredglass",
})

_ACCEPTABLE_FRAME_EFFECTS = frozenset({
    "legendary",
    "snow",
    "sunmoondfc",
    "compasslanddfc",
    "originpwdfc",
    "mooneldrazidfc",
    "waxingandwaningmoondfc",
    "convertdfc",
    "fandfc",
    "upsidedowndfc",
})

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.models import Classification, SelectionOptions


def classify_printing(
    card: CardPrinting,
    ub_ids: set[str],
    opts: SelectionOptions,
) -> Classification:
    border = card.border_color
    if border == "black":
        border_tier = "good"
    elif border in ("white", "borderless"):
        border_tier = "bad"
    else:
        border_tier = "neutral"

    effects = set(card.frame_effects)
    has_special = bool(effects & _SPECIAL_FRAME_EFFECTS) or card.full_art or card.variation
    if effects - _ACCEPTABLE_FRAME_EFFECTS - _SPECIAL_FRAME_EFFECTS:
        has_special = has_special or bool(effects - _ACCEPTABLE_FRAME_EFFECTS)

    return Classification(
        border_tier=border_tier,
        nonfoil_available="nonfoil" in card.finishes,
        is_universes_beyond=card.id in ub_ids,
        has_special_frame=has_special,
        is_promo=card.promo,
        is_english=card.lang == opts.lang,
        has_highres=card.highres_image or card.image_status == "highres_scan",
        has_png=card.primary_image_uri("png") is not None,
    )

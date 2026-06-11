from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.classify import classify_printing
from card_downloader.selection.config import WEIGHTS
from card_downloader.selection.models import Classification, ScoreBreakdown, ScoredCandidate, SelectionOptions


def score_printing(
    card: CardPrinting,
    ub_ids: set[str],
    opts: SelectionOptions,
) -> ScoredCandidate:
    classification = classify_printing(card, ub_ids, opts)
    breakdown = _score_breakdown(card, classification, opts)
    return ScoredCandidate(
        printing=card,
        score=breakdown.total,
        breakdown=breakdown,
        classification=classification,
    )


def _score_breakdown(
    card: CardPrinting,
    c: Classification,
    opts: SelectionOptions,
) -> ScoreBreakdown:
    nonfoil = WEIGHTS["nonfoil"] if c.nonfoil_available else WEIGHTS["foil_only"]

    if card.border_color == "black":
        border = WEIGHTS["border_black"]
    elif card.border_color == "white":
        border = 0.0 if opts.allow_white_border else WEIGHTS["border_white"]
    elif card.border_color == "borderless":
        border = WEIGHTS["border_borderless"]
    else:
        border = 0.0

    if c.is_universes_beyond:
        not_ub = 0.0 if opts.allow_ub else WEIGHTS["ub"]
    else:
        not_ub = WEIGHTS["not_ub"]

    frame = WEIGHTS["frame_normal"] if not c.has_special_frame else 0.0
    for effect in card.frame_effects:
        if effect == "showcase":
            frame += WEIGHTS["showcase"]
        elif effect == "extendedart":
            frame += WEIGHTS["extendedart"]
        elif effect == "etched":
            frame += WEIGHTS["etched_frame"]

    if c.is_promo:
        promo = 0.0 if opts.allow_promo else WEIGHTS["promo"]
    else:
        promo = WEIGHTS["not_promo"]

    if c.is_english:
        english = WEIGHTS["english"]
    else:
        english = WEIGHTS["non_english"] if card.lang != opts.lang else 0.0

    image = 0.0
    if c.has_highres:
        image += WEIGHTS["highres"]
    if card.image_status == "lowres":
        image += WEIGHTS["lowres"]
    if c.has_png:
        image += WEIGHTS["png"]

    paper = WEIGHTS["paper"] if "paper" in card.games else 0.0

    set_type = WEIGHTS["funny_set"] if card.set_type in ("funny", "memorabilia") else 0.0
    if card.variation:
        set_type += WEIGHTS["variation"]

    return ScoreBreakdown(
        nonfoil=nonfoil,
        border=border,
        not_ub=not_ub,
        frame=frame,
        promo=promo,
        english=english,
        image=image,
        paper=paper,
        set_type=set_type,
    )

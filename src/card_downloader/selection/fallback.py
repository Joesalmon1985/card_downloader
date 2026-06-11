from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.classify import classify_printing
from card_downloader.selection.models import ScoredCandidate, SelectionOptions


def fallback_reasons(
    chosen: CardPrinting,
    ub_ids: set[str],
    anchor_set: str,
    was_outlier: bool,
    all_candidates: list[ScoredCandidate],
    opts: SelectionOptions,
) -> list[str]:
    reasons: list[str] = []
    c = classify_printing(chosen, ub_ids, opts)

    if was_outlier and anchor_set:
        reasons.append(f"outlier_from_anchor:{anchor_set}")

    if c.is_universes_beyond and not opts.allow_ub:
        if all(c.classification.is_universes_beyond for c in all_candidates):
            reasons.append("universes_beyond_only")
        else:
            reasons.append("universes_beyond_chosen")

    if not c.nonfoil_available:
        if all(not x.classification.nonfoil_available for x in all_candidates):
            reasons.append("foil_only_printing")
        else:
            reasons.append("foil_finish_only")

    if chosen.border_color == "white" and not opts.allow_white_border:
        if all(x.printing.border_color == "white" for x in all_candidates):
            reasons.append("white_border_unavoidable")
        else:
            reasons.append("white_border_chosen")

    if not c.is_english:
        reasons.append("no_english_printing")

    if chosen.image_status == "lowres":
        if all(x.printing.image_status == "lowres" for x in all_candidates):
            reasons.append("lowres_only")
        else:
            reasons.append("lowres_chosen")

    if c.has_special_frame:
        non_special = [x for x in all_candidates if not x.classification.has_special_frame]
        if not non_special:
            reasons.append("special_frame_required")
        elif c.has_special_frame:
            reasons.append("special_frame_chosen")

    if c.is_promo and not opts.allow_promo:
        if all(x.classification.is_promo for x in all_candidates):
            reasons.append("promo_only_option")

    return reasons

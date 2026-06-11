from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.classify import classify_printing
from card_downloader.selection.config import COHERENCE_WEIGHT, OUTLIER_PENALTY, WEIGHTS
from card_downloader.selection.models import (
    Anchor,
    Assignment,
    CardAssignment,
    ScoredCandidate,
    ScoreBreakdown,
    SelectionOptions,
)
from card_downloader.selection.scoring import score_printing


def best_assignment(
    deck_names: list[str],
    quantities: dict[str, int],
    pools: dict[str, list[ScoredCandidate]],
    anchors: list[Anchor],
    ub_ids_by_name: dict[str, set[str]],
    opts: SelectionOptions,
) -> Assignment:
    if not anchors:
        anchors = _fallback_anchors(pools)

    best: Assignment | None = None
    for anchor in anchors:
        assignment = _evaluate_anchor(
            deck_names, quantities, pools, anchor, ub_ids_by_name, opts
        )
        if best is None or assignment.total_score > best.total_score:
            best = assignment

    if best is None:
        best = _evaluate_anchor(
            deck_names,
            quantities,
            pools,
            Anchor(set_code="", coverage=0),
            ub_ids_by_name,
            opts,
        )
    return best


def _fallback_anchors(pools: dict[str, list[ScoredCandidate]]) -> list[Anchor]:
    from card_downloader.selection.anchors import rank_anchors

    return rank_anchors(pools)


def _evaluate_anchor(
    deck_names: list[str],
    quantities: dict[str, int],
    pools: dict[str, list[ScoredCandidate]],
    anchor: Anchor,
    ub_ids_by_name: dict[str, set[str]],
    opts: SelectionOptions,
) -> Assignment:
    assignments: list[CardAssignment] = []
    in_anchor = 0
    outliers = 0
    total = 0.0

    for name in deck_names:
        candidates = pools.get(name, [])
        if not candidates:
            continue

        in_set = [c for c in candidates if c.printing.set_code == anchor.set_code]
        if in_set:
            chosen = max(in_set, key=lambda c: c.score)
            was_outlier = False
            coherence = COHERENCE_WEIGHT
            in_anchor += 1
        else:
            chosen = max(candidates, key=lambda c: c.score)
            was_outlier = True
            coherence = 0.0
            outliers += 1

        from card_downloader.selection.fallback import fallback_reasons

        reasons = fallback_reasons(
            chosen.printing,
            ub_ids_by_name.get(name, set()),
            anchor.set_code,
            was_outlier,
            pools[name],
            opts,
        )

        card_total = chosen.score + coherence - (OUTLIER_PENALTY if was_outlier else 0.0)
        total += card_total

        breakdown = ScoreBreakdown(
            nonfoil=chosen.breakdown.nonfoil,
            border=chosen.breakdown.border,
            not_ub=chosen.breakdown.not_ub,
            frame=chosen.breakdown.frame,
            promo=chosen.breakdown.promo,
            english=chosen.breakdown.english,
            image=chosen.breakdown.image,
            paper=chosen.breakdown.paper,
            set_type=chosen.breakdown.set_type,
        )

        assignments.append(
            CardAssignment(
                deck_name=name,
                quantity=quantities[name],
                printing=chosen.printing,
                score=card_total,
                breakdown=breakdown,
                fallback_reasons=tuple(reasons),
                was_outlier=was_outlier,
                coherence_bonus=coherence,
            )
        )

    coverage = in_anchor / len(deck_names) if deck_names else 0.0
    return Assignment(
        anchor_set=anchor.set_code,
        assignments=tuple(assignments),
        total_score=total,
        coverage=coverage,
        cards_in_anchor=in_anchor,
        outliers=outliers,
    )


def build_pools(
    printings_by_name: dict[str, list[CardPrinting]],
    ub_ids_by_name: dict[str, set[str]],
    opts: SelectionOptions,
) -> dict[str, list[ScoredCandidate]]:
    from card_downloader.selection.filters import hard_exclude

    pools: dict[str, list[ScoredCandidate]] = {}
    for name, printings in printings_by_name.items():
        ub_ids = ub_ids_by_name.get(name, set())
        scored = []
        for p in printings:
            if hard_exclude(p, opts):
                continue
            scored.append(score_printing(p, ub_ids, opts))
        pools[name] = scored
    return pools

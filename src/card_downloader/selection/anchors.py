from collections import Counter

from card_downloader.selection.config import TOP_ANCHORS
from card_downloader.selection.models import Anchor, ScoredCandidate


def rank_anchors(
    pools: dict[str, list[ScoredCandidate]],
) -> list[Anchor]:
    """Rank set codes by how many deck cards have at least one printing in that set."""
    coverage: Counter[str] = Counter()
    for candidates in pools.values():
        sets_for_card = {c.printing.set_code for c in candidates}
        for set_code in sets_for_card:
            coverage[set_code] += 1

    ranked = sorted(coverage.items(), key=lambda x: (-x[1], x[0]))
    return [Anchor(set_code=code, coverage=count) for code, count in ranked[:TOP_ANCHORS]]

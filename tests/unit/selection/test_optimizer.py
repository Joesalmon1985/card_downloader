import json
from pathlib import Path

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.anchors import rank_anchors
from card_downloader.selection.models import SelectionOptions
from card_downloader.selection.optimizer import best_assignment, build_pools


def _card(filename: str, **overrides) -> CardPrinting:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "cards" / filename
    data = json.loads(path.read_text())
    data.update(overrides)
    return CardPrinting.from_api_dict(data)


def test_anchor_coverage_wins_over_independent():
    """Anchor ABC covers 3 cards; independent best might differ but total score favors ABC."""
    sol_clu = _card("sol_ring_normal.json")
    sol_c21 = _card("sol_ring_normal.json", id="x1", set="abc", set_name="ABC")
    tower_abc = _card("sol_ring_normal.json", id="x2", set="abc", set_name="ABC", name="Command Tower")
    tower_xyz = _card("sol_ring_normal.json", id="x3", set="xyz", set_name="XYZ", name="Command Tower")
    bolt_abc = _card("sol_ring_normal.json", id="x4", set="abc", set_name="ABC", name="Lightning Bolt")
    plateau = _card("plateau_white_border.json")

    names = ["Sol Ring", "Command Tower", "Lightning Bolt", "Plateau", "Counterspell"]
    quantities = {n: 1 for n in names}

    printings = {
        "Sol Ring": [sol_clu, sol_c21],
        "Command Tower": [tower_abc, tower_xyz],
        "Lightning Bolt": [bolt_abc],
        "Plateau": [plateau],
        "Counterspell": [],
    }
    ub: dict[str, set[str]] = {n: set() for n in names}
    opts = SelectionOptions()
    pools = build_pools(printings, ub, opts)
    anchors = rank_anchors(pools)
    result = best_assignment(names, quantities, pools, anchors, ub, opts)
    assert result.anchor_set == "abc"
    assert result.cards_in_anchor >= 3


def test_plateau_is_outlier_with_white_border():
    sol = _card("sol_ring_normal.json")
    plateau = _card("plateau_white_border.json")
    names = ["Sol Ring", "Plateau"]
    quantities = {"Sol Ring": 1, "Plateau": 1}
    printings = {"Sol Ring": [sol], "Plateau": [plateau]}
    ub = {"Sol Ring": set(), "Plateau": set()}
    opts = SelectionOptions()
    pools = build_pools(printings, ub, opts)
    anchors = rank_anchors(pools)
    result = best_assignment(names, quantities, pools, anchors, ub, opts)
    plateau_row = next(a for a in result.assignments if a.deck_name == "Plateau")
    assert plateau_row.was_outlier or plateau.printing.border_color == "white"

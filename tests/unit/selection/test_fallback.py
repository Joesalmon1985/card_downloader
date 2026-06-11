import json
from pathlib import Path

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.fallback import fallback_reasons
from card_downloader.selection.models import SelectionOptions
from card_downloader.selection.optimizer import build_pools


def _card(name: str) -> CardPrinting:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "cards" / name
    return CardPrinting.from_api_dict(json.loads(path.read_text()))


def test_white_border_unavoidable():
    plateau = _card("plateau_white_border.json")
    pools = build_pools({"Plateau": [plateau]}, {"Plateau": set()}, SelectionOptions())
    reasons = fallback_reasons(
        plateau,
        set(),
        "clu",
        True,
        pools["Plateau"],
        SelectionOptions(),
    )
    assert "white_border_unavoidable" in reasons or "outlier_from_anchor:clu" in reasons


def test_outlier_from_anchor():
    sol = _card("sol_ring_normal.json")
    pools = build_pools({"Sol Ring": [sol]}, {"Sol Ring": set()}, SelectionOptions())
    reasons = fallback_reasons(
        sol,
        set(),
        "clu",
        True,
        pools["Sol Ring"],
        SelectionOptions(),
    )
    assert "outlier_from_anchor:clu" in reasons

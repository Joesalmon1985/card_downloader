import json
from pathlib import Path

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.config import WEIGHTS
from card_downloader.selection.fallback import fallback_reasons
from card_downloader.selection.models import SelectionOptions
from card_downloader.selection.scoring import score_printing


def _card(name: str) -> CardPrinting:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "cards" / name
    return CardPrinting.from_api_dict(json.loads(path.read_text()))


def test_normal_beats_showcase_ub_promo():
    normal = score_printing(_card("sol_ring_normal.json"), set(), SelectionOptions())
    showcase = score_printing(_card("showcase_example.json"), set(), SelectionOptions())
    assert normal.score > showcase.score


def test_allow_ub_removes_penalty():
    card = _card("sol_ring_normal.json")
    ub_ids = {card.id}
    strict = score_printing(card, ub_ids, SelectionOptions(allow_ub=False))
    allow = score_printing(card, ub_ids, SelectionOptions(allow_ub=True))
    assert allow.breakdown.not_ub > strict.breakdown.not_ub


def test_breakdown_sums_to_total():
    scored = score_printing(_card("sol_ring_normal.json"), set(), SelectionOptions())
    assert scored.breakdown.total == scored.score

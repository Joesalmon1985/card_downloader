import json
from pathlib import Path

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.classify import classify_printing
from card_downloader.selection.models import SelectionOptions


def _card(name: str) -> CardPrinting:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "cards" / name
    return CardPrinting.from_api_dict(json.loads(path.read_text()))


def test_black_border_good():
    c = classify_printing(_card("sol_ring_normal.json"), set(), SelectionOptions())
    assert c.border_tier == "good"


def test_white_border_bad():
    c = classify_printing(_card("plateau_white_border.json"), set(), SelectionOptions())
    assert c.border_tier == "bad"


def test_showcase_special_frame():
    c = classify_printing(_card("showcase_example.json"), set(), SelectionOptions())
    assert c.has_special_frame is True


def test_nonfoil_available():
    c = classify_printing(_card("sol_ring_normal.json"), set(), SelectionOptions())
    assert c.nonfoil_available is True


def test_ub_id_membership():
    card = _card("sol_ring_normal.json")
    c = classify_printing(card, {card.id}, SelectionOptions())
    assert c.is_universes_beyond is True

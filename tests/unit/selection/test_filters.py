import json
from pathlib import Path

import pytest

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.filters import hard_exclude
from card_downloader.selection.models import SelectionOptions


def _card(name: str) -> CardPrinting:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "cards" / name
    return CardPrinting.from_api_dict(json.loads(path.read_text()))


def test_exclude_digital():
    card = _card("sol_ring_normal.json")
    digital = CardPrinting.from_api_dict({**card.raw, "digital": True, "games": ["arena"]})
    assert hard_exclude(digital, SelectionOptions()) is True


def test_exclude_missing_image():
    card = _card("sol_ring_normal.json")
    no_img = CardPrinting.from_api_dict({**card.raw, "image_uris": None, "image_status": "missing"})
    assert hard_exclude(no_img, SelectionOptions()) is True


def test_exclude_token_layout():
    assert hard_exclude(_card("token_example.json"), SelectionOptions()) is True


def test_keep_normal_playable():
    assert hard_exclude(_card("sol_ring_normal.json"), SelectionOptions()) is False

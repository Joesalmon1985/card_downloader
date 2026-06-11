from pathlib import Path

from card_downloader.download.filenames import image_filename, safe_filename
from card_downloader.scryfall.models import CardPrinting
import json


def _printing(**kwargs) -> CardPrinting:
    base = json.loads(
        (Path(__file__).resolve().parents[2] / "fixtures/cards/sol_ring_normal.json").read_text()
    )
    base.update(kwargs)
    return CardPrinting.from_api_dict(base)


def test_safe_filename_sanitises():
    assert safe_filename('A/B: C?"') == "A_B_ C'"


def test_image_filename_includes_set_and_collector():
    p = _printing(set="clu", collector_number="123")
    assert image_filename(p) == "Sol Ring__clu_123.png"


def test_dfc_front_suffix():
    p = _printing()
    assert image_filename(p, face="front") == "Sol Ring__clu_1__front.png"

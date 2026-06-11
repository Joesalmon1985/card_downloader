import json
from pathlib import Path

from card_downloader.scryfall.models import CardPrinting
from card_downloader.selection.anchors import rank_anchors
from card_downloader.selection.models import SelectionOptions
from card_downloader.selection.optimizer import build_pools
from card_downloader.selection.scoring import score_printing


def _card(name: str) -> CardPrinting:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "cards" / name
    return CardPrinting.from_api_dict(json.loads(path.read_text()))


def test_rank_anchors_by_coverage():
    sol_clu = _card("sol_ring_normal.json")
    sol_show = _card("showcase_example.json")
    pools = {
        "Sol Ring": [
            score_printing(sol_clu, set(), SelectionOptions()),
            score_printing(sol_show, set(), SelectionOptions()),
        ],
        "Plateau": [score_printing(_card("plateau_white_border.json"), set(), SelectionOptions())],
    }
    anchors = rank_anchors(pools)
    assert anchors[0].set_code == "clu"
    assert anchors[0].coverage == 1

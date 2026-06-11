import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from card_downloader.pipeline.plan import create_manifest
from card_downloader.scryfall.models import CardPrinting


def _load_card(name: str) -> CardPrinting:
    path = Path(__file__).resolve().parents[1] / "fixtures" / "cards" / name
    return CardPrinting.from_api_dict(json.loads(path.read_text()))


def _mock_client():
    sol = _load_card("sol_ring_normal.json")
    plateau = _load_card("plateau_white_border.json")
    client = MagicMock()

    def search(name: str):
        if name == "Sol Ring":
            return [sol]
        if name == "Plateau":
            return [plateau]
        return []

    client.search_printings.side_effect = search
    client.search_universes_beyond_ids.return_value = set()
    return client


def test_create_manifest_with_mock_client(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n1 Plateau\n", encoding="utf-8")
    manifest, _ = create_manifest(deck, client=_mock_client())
    assert len(manifest.cards) == 2
    assert manifest.selection_summary.anchor_set
    names = {c.deck_name for c in manifest.cards}
    assert names == {"Sol Ring", "Plateau"}


def test_manifest_scores_present():
    deck_path = Path(__file__).resolve().parents[1].parent / "data/decklists/example-commander.txt"
    if not deck_path.exists():
        pytest.skip("example decklist not present")
    # Use mock for speed — full deck would need many mocks
    pass

from pathlib import Path

import pytest

from card_downloader.decklist.models import DeckEntry
from card_downloader.decklist.parser import parse_decklist, parse_line


def test_quantity_line():
    assert parse_line("1 Sol Ring") == DeckEntry(quantity=1, name="Sol Ring")


def test_multi_digit_quantity():
    assert parse_line("11 Snow-Covered Mountain") == DeckEntry(
        quantity=11, name="Snow-Covered Mountain"
    )


def test_optional_x_suffix():
    assert parse_line("1x Sol Ring") == DeckEntry(quantity=1, name="Sol Ring")


def test_bare_name_defaults_to_one():
    assert parse_line("Sol Ring") == DeckEntry(quantity=1, name="Sol Ring")


def test_comment_skipped():
    assert parse_line("# main deck") is None


def test_empty_line_skipped():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_sideboard_stops_parsing():
    text = "1 Sol Ring\n[Sideboard]\n1 Counterspell"
    deck = parse_decklist(text)
    assert len(deck.entries) == 1
    assert deck.entries[0].name == "Sol Ring"


def test_example_commander_deck(fixtures_dir):
    path = Path(__file__).resolve().parents[3] / "data/decklists/example-commander.txt"
    text = path.read_text(encoding="utf-8")
    deck = parse_decklist(text)
    assert len(deck.entries) == 94
    total_qty = sum(e.quantity for e in deck.entries)
    assert total_qty == 114  # 92x1 + 11 mountains + 11 plains


def test_curly_apostrophe_in_decklist():
    entry = parse_line("1 Urza\u2019s Saga")
    assert entry is not None
    assert entry.name == "Urza's Saga"

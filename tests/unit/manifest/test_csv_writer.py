import csv
from io import StringIO
from pathlib import Path

import pytest

from card_downloader.decklist.models import DeckEntry, ParsedDeck
from card_downloader.manifest.csv_writer import (
    CSV_COLUMNS,
    build_card_choice_rows,
    write_card_choices_csv,
)
from card_downloader.manifest.schema import (
    CardManifestRow,
    ChosenPrintingRecord,
    Manifest,
    SelectionSummary,
    utc_now_iso,
)


def _printing(**kwargs) -> ChosenPrintingRecord:
    defaults = dict(
        id="id1",
        set="clu",
        collector_number="1",
        lang="en",
        border_color="black",
        scryfall_uri="https://example.com",
        image_url="https://example.com/img.png",
        image_paths=["images/sol.png"],
        set_name="Ravnica: Clue Edition",
        released_at="2024-02-23",
        printing_name="Sol Ring",
        promo=False,
        finishes=["nonfoil", "foil"],
        is_universes_beyond=False,
        has_special_frame=False,
    )
    defaults.update(kwargs)
    return ChosenPrintingRecord(**defaults)


def _manifest(
    cards: list[CardManifestRow],
    errors: list[str] | None = None,
    anchor_set: str = "clu",
) -> Manifest:
    return Manifest(
        version=1,
        decklist_path="deck.txt",
        generated_at=utc_now_iso(),
        options={},
        selection_summary=SelectionSummary(
            anchor_set=anchor_set,
            coverage=1.0,
            cards_in_anchor=len(cards),
            outliers=0,
            total_score=80.0,
        ),
        cards=cards,
        errors=errors or [],
    )


def _card_row(name: str, **printing_kwargs) -> CardManifestRow:
    printing_kwargs.setdefault("printing_name", name)
    return CardManifestRow(
        deck_name=name,
        quantity=1,
        oracle_id="oid",
        chosen_printing=_printing(**printing_kwargs),
        score=41.0,
        score_breakdown={"nonfoil": 8},
        fallback_reasons=[],
        was_outlier=False,
    )


def test_build_card_choice_rows_happy_path():
    deck = ParsedDeck(
        entries=(
            DeckEntry(1, "Sol Ring"),
            DeckEntry(1, "Command Tower"),
        )
    )
    manifest = _manifest(
        [
            _card_row("Sol Ring", set="clu"),
            _card_row("Command Tower", set="afc"),
        ]
    )
    rows = build_card_choice_rows(manifest, deck)
    assert len(rows) == 2
    assert rows[0]["deck_order"] == "1"
    assert rows[0]["requested_name"] == "Sol Ring"
    assert rows[0]["status"] == "ok"
    assert rows[0]["in_anchor_set"] == "true"
    assert rows[0]["is_foil_available"] == "true"
    assert rows[0]["is_nonfoil_available"] == "true"
    assert rows[1]["deck_order"] == "2"
    assert rows[1]["in_anchor_set"] == "false"


def test_build_card_choice_rows_error_row():
    deck = ParsedDeck(entries=(DeckEntry(1, "Command Tower"),))
    manifest = _manifest([], errors=["Command Tower: not found"])
    rows = build_card_choice_rows(manifest, deck)
    assert len(rows) == 1
    assert rows[0]["status"] == "error"
    assert rows[0]["error_message"] == "not found"
    assert rows[0]["quantity"] == "0"
    assert rows[0]["resolved_name"] == ""


def test_build_card_choice_rows_fallback_and_flags():
    deck = ParsedDeck(entries=(DeckEntry(1, "Plateau"),))
    manifest = _manifest(
        [
            CardManifestRow(
                deck_name="Plateau",
                quantity=1,
                oracle_id="oid",
                chosen_printing=_printing(
                    printing_name="Plateau",
                    set="leb",
                    border_color="white",
                    promo=True,
                    finishes=["nonfoil"],
                    is_universes_beyond=False,
                    has_special_frame=True,
                ),
                score=20.0,
                score_breakdown={},
                fallback_reasons=["white_border_chosen"],
                was_outlier=True,
            )
        ],
        anchor_set="clu",
    )
    rows = build_card_choice_rows(manifest, deck)
    assert rows[0]["fallback_used"] == "true"
    assert rows[0]["fallback_reason"] == "white_border_chosen"
    assert rows[0]["is_white_border"] == "true"
    assert rows[0]["is_promo"] == "true"
    assert rows[0]["is_special_treatment"] == "true"
    assert rows[0]["is_foil_available"] == "false"
    assert rows[0]["is_nonfoil_available"] == "true"


def test_csv_escaping_commas_quotes_apostrophe_unicode(tmp_path: Path):
    tricky = "Lim-Dûl's \"Vault\", Special"
    deck = ParsedDeck(entries=(DeckEntry(1, tricky),))
    manifest = _manifest([_card_row(tricky)])
    (tmp_path / "deck.txt").write_text(f"1 {tricky}\n", encoding="utf-8")
    path = tmp_path / "card_choices.csv"
    write_card_choices_csv(manifest, path, decklist_path=tmp_path / "deck.txt")

    text = path.read_text(encoding="utf-8")
    assert tricky in text or "Lim-Dûl" in text

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row["requested_name"] == tricky
        assert row["normalised_name"] == tricky
        assert len(row) == len(CSV_COLUMNS)


def test_write_card_choice_csv_round_trip(tmp_path: Path):
    deck = ParsedDeck(entries=(DeckEntry(2, "Sol Ring"),))
    row = _card_row("Sol Ring")
    row = CardManifestRow(
        deck_name=row.deck_name,
        quantity=2,
        oracle_id=row.oracle_id,
        chosen_printing=row.chosen_printing,
        score=row.score,
        score_breakdown=row.score_breakdown,
        fallback_reasons=row.fallback_reasons,
        was_outlier=row.was_outlier,
    )
    manifest = _manifest([row])
    (tmp_path / "deck.txt").write_text("2 Sol Ring\n", encoding="utf-8")
    path = tmp_path / "card_choices.csv"
    write_card_choices_csv(manifest, path, decklist_path=tmp_path / "deck.txt")

    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["quantity"] == "2"
    assert set(rows[0].keys()) == set(CSV_COLUMNS)

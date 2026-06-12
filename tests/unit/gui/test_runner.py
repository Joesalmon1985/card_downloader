from pathlib import Path
from unittest.mock import patch

import pytest

from card_downloader.gui.options import GuiRunOptions
from card_downloader.gui.runner import RunResult, execute_run
from card_downloader.manifest.schema import (
    CardManifestRow,
    ChosenPrintingRecord,
    Manifest,
    SelectionSummary,
    utc_now_iso,
)
from card_downloader.scryfall.errors import ScryfallAPIError


def _manifest(cards: list[CardManifestRow], errors: list[str] | None = None) -> Manifest:
    return Manifest(
        version=1,
        decklist_path="deck.txt",
        generated_at=utc_now_iso(),
        options={},
        selection_summary=SelectionSummary("clu", 1.0, 1, 0, 1.0),
        cards=cards,
        errors=errors or [],
    )


def _card_row(name: str, with_image: bool = True) -> CardManifestRow:
    paths = ["images/x.png"] if with_image else []
    return CardManifestRow(
        deck_name=name,
        quantity=1,
        oracle_id="oid",
        chosen_printing=ChosenPrintingRecord(
            id="id1",
            set="clu",
            collector_number="1",
            lang="en",
            border_color="black",
            scryfall_uri="https://example.com",
            image_url="https://example.com/img.png",
            image_paths=paths,
        ),
        score=1.0,
        score_breakdown={},
        fallback_reasons=[],
        was_outlier=False,
    )


def test_execute_run_fails_on_empty_manifest(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    opts = GuiRunOptions(decklist_path=deck, output_dir=tmp_path / "out")

    with patch("card_downloader.gui.runner.run_download") as mock_run:
        mock_run.return_value = _manifest([], errors=["Sol Ring: error"])
        result = execute_run(opts, cache_dir=tmp_path / "cache")

    assert result.success is False
    assert "no cards" in result.message.lower()


def test_execute_run_success(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    opts = GuiRunOptions(decklist_path=deck, output_dir=out, build_pdf=True)

    with patch("card_downloader.gui.runner.run_download") as mock_run:
        mock_run.return_value = _manifest([_card_row("Sol Ring")])
        (out / "card_choices.csv").write_text("deck_order\n", encoding="utf-8")
        with patch("card_downloader.gui.runner.pdf_path_exists", return_value=True):
            result = execute_run(opts, cache_dir=tmp_path / "cache")

    assert result.success is True
    assert result.manifest_path == out.resolve() / "manifest.json"
    assert result.csv_path == out.resolve() / "card_choices.csv"
    assert result.pdf_path == out.resolve() / "proxies.pdf"


def test_execute_run_scryfall_error(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    opts = GuiRunOptions(decklist_path=deck, output_dir=tmp_path / "out")

    with patch("card_downloader.gui.runner.run_download") as mock_run:
        mock_run.side_effect = ScryfallAPIError(400, "bad request", "https://api.scryfall.com/cards/search")
        result = execute_run(opts, cache_dir=tmp_path / "cache")

    assert result.success is False
    assert "400" in result.message

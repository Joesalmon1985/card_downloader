from pathlib import Path

import pytest

from card_downloader.gui.options import (
    DEFAULT_OUTPUT_DIR,
    GuiRunOptions,
    to_download_kwargs,
    to_selection_options,
    validate,
)


def test_default_output_dir():
    assert DEFAULT_OUTPUT_DIR == Path("data/runs/gui-run")


def test_to_selection_options_maps_checkboxes(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    opts = GuiRunOptions(
        decklist_path=deck,
        allow_ub=True,
        allow_white_border=True,
        allow_promo=True,
        image_size="large",
    )
    sel = to_selection_options(opts)
    assert sel.allow_ub is True
    assert sel.allow_white_border is True
    assert sel.allow_promo is True
    assert sel.image_size == "large"


def test_to_download_kwargs_build_pdf_false(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    out = tmp_path / "out"
    opts = GuiRunOptions(decklist_path=deck, output_dir=out, build_pdf=False, gap_mm=2.0)
    kwargs = to_download_kwargs(opts)
    assert kwargs["build_pdf"] is False
    assert kwargs["gap_mm"] == 2.0
    assert kwargs["out_dir"] == out.resolve()


def test_validate_missing_decklist(tmp_path):
    opts = GuiRunOptions(decklist_path=Path("/nonexistent/deck.txt"), output_dir=tmp_path / "out")
    errors = validate(opts)
    assert any("not found" in e for e in errors)


def test_validate_bad_dpi(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    opts = GuiRunOptions(decklist_path=deck, output_dir=tmp_path / "out", dpi=0)
    errors = validate(opts)
    assert any("DPI" in e for e in errors)


def test_validate_invalid_image_size(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    opts = GuiRunOptions(decklist_path=deck, output_dir=tmp_path / "out", image_size="huge")
    errors = validate(opts)
    assert any("image size" in e.lower() for e in errors)


def test_validate_ok(tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n", encoding="utf-8")
    opts = GuiRunOptions(decklist_path=deck, output_dir=tmp_path / "out")
    assert validate(opts) == []

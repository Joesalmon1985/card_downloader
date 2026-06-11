import sys
from unittest.mock import MagicMock, patch

import pytest

from card_downloader.scryfall.errors import ScryfallAPIError


def test_explain_prints_error_and_exits_nonzero(capsys):
    from card_downloader.cli.main import cmd_explain

    args = MagicMock()
    args.card = "Sol Ring"
    args.top = 5
    args.lang = "en"
    args.allow_ub = False
    args.allow_white_border = False
    args.allow_promo = False
    args.size = "png"
    args.cache_dir = "data/cache"

    err = ScryfallAPIError(400, "Missing User-Agent", "https://api.scryfall.com/cards/search")

    with patch("card_downloader.scryfall.client.ScryfallClient") as mock_cls:
        mock_cls.return_value.search_printings.side_effect = err
        with pytest.raises(SystemExit) as exc_info:
            cmd_explain(args)

    assert exc_info.value.code == 1
    out = capsys.readouterr().err
    assert "Sol Ring" in out
    assert "400" in out


def test_download_exits_nonzero_when_all_cards_fail(tmp_path, capsys):
    from card_downloader.cli.main import cmd_download
    from card_downloader.manifest.schema import Manifest, SelectionSummary, utc_now_iso

    deck = tmp_path / "deck.txt"
    deck.write_text("1 Sol Ring\n1 Command Tower\n", encoding="utf-8")
    out = tmp_path / "out"

    args = MagicMock()
    args.decklist = str(deck)
    args.out = str(out)
    args.lang = "en"
    args.allow_ub = False
    args.allow_white_border = False
    args.allow_promo = False
    args.size = "png"
    args.cache_dir = str(tmp_path / "cache")
    args.no_pdf = True
    args.pdf = "proxies.pdf"
    args.paper = "a4"
    args.dpi = 300
    args.force = False

    empty_manifest = Manifest(
        version=1,
        decklist_path=str(deck),
        generated_at=utc_now_iso(),
        options={},
        selection_summary=SelectionSummary("", 0.0, 0, 0, 0.0),
        cards=[],
        errors=["Sol Ring: error", "Command Tower: error"],
    )

    with patch("card_downloader.cli.main.run_download") as mock_run:
        mock_run.return_value = empty_manifest
        with pytest.raises(SystemExit) as exc_info:
            cmd_download(args)

    assert exc_info.value.code == 1
    assert "Download complete" not in capsys.readouterr().out

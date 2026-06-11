import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from card_downloader.scryfall.models import CardPrinting


def _load_card(name: str) -> CardPrinting:
    path = Path(__file__).resolve().parents[1] / "fixtures" / "cards" / name
    return CardPrinting.from_api_dict(json.loads(path.read_text()))


def _mock_smoke_deck_client() -> MagicMock:
    sol = _load_card("sol_ring_normal.json")
    tower = _load_card("command_tower_normal.json")
    client = MagicMock()

    def search(name: str):
        if name == "Sol Ring":
            return [sol]
        if name == "Command Tower":
            return [tower]
        return []

    client.search_printings.side_effect = search
    client.search_universes_beyond_ids.return_value = set()
    return client


class _PngDownloader:
    def download(self, url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (745, 1040), (128, 128, 128)).save(dest)


def test_cmd_download_default_pdf_enabled(tmp_path: Path, capsys) -> None:
    """CLI download path with PDF enabled (default, no --no-pdf)."""
    from card_downloader.cli.main import cmd_download

    deck = tmp_path / "smoke-deck.txt"
    deck.write_text("1 Sol Ring\n1 Command Tower\n", encoding="utf-8")
    out = tmp_path / "cli-run"

    args = MagicMock()
    args.decklist = str(deck)
    args.out = str(out)
    args.lang = "en"
    args.allow_ub = False
    args.allow_white_border = False
    args.allow_promo = False
    args.size = "png"
    args.cache_dir = str(tmp_path / "cache")
    args.no_pdf = False
    args.pdf = "proxies.pdf"
    args.paper = "a4"
    args.dpi = 300
    args.force = False

    with patch(
        "card_downloader.pipeline.download.RequestsImageDownloader",
        return_value=_PngDownloader(),
    ), patch(
        "card_downloader.pipeline.plan.ScryfallClient",
        return_value=_mock_smoke_deck_client(),
    ):
        cmd_download(args)

    captured = capsys.readouterr()
    assert "Download complete" in captured.out
    assert (out / "manifest.json").is_file()
    assert (out / "selection-report.md").is_file()
    assert (out / "proxies.pdf").is_file()
    assert (out / "proxies.pdf").stat().st_size > 1000

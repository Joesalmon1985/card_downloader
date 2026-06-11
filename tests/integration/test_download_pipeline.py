import csv
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from card_downloader.pipeline.download import run_download
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


@pytest.fixture
def smoke_deck(tmp_path: Path) -> Path:
    deck = tmp_path / "smoke-deck.txt"
    deck.write_text("1 Sol Ring\n1 Command Tower\n", encoding="utf-8")
    return deck


def test_run_download_with_pdf_enabled_builds_proxy_pdf(
    tmp_path: Path, smoke_deck: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: build_pdf bool must not shadow the PDF builder function."""
    out_dir = tmp_path / "run-with-pdf"
    monkeypatch.setattr(
        "card_downloader.pipeline.download.RequestsImageDownloader",
        lambda: _PngDownloader(),
    )

    manifest = run_download(
        smoke_deck,
        out_dir,
        client=_mock_smoke_deck_client(),
        build_pdf=True,
        cache_dir=tmp_path / "cache",
    )

    assert len(manifest.cards) == 2
    assert manifest.outputs.pdf_path == "proxies.pdf"
    assert manifest.outputs.pdf_pages >= 1
    assert manifest.outputs.pdf_cards_placed == 2
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "selection-report.md").is_file()
    assert (out_dir / "proxies.pdf").is_file()
    assert (out_dir / "proxies.pdf").stat().st_size > 1000
    assert (out_dir / "card_choices.csv").is_file()
    with (out_dir / "card_choices.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert {r["requested_name"] for r in rows} == {"Sol Ring", "Command Tower"}
    assert all(r["status"] == "ok" for r in rows)


def test_run_download_with_pdf_disabled_skips_proxy_pdf(
    tmp_path: Path, smoke_deck: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_dir = tmp_path / "run-no-pdf"
    monkeypatch.setattr(
        "card_downloader.pipeline.download.RequestsImageDownloader",
        lambda: _PngDownloader(),
    )

    manifest = run_download(
        smoke_deck,
        out_dir,
        client=_mock_smoke_deck_client(),
        build_pdf=False,
        cache_dir=tmp_path / "cache",
    )

    assert len(manifest.cards) == 2
    assert manifest.outputs.pdf_path == ""
    assert manifest.outputs.pdf_pages == 0
    assert (out_dir / "manifest.json").is_file()
    assert not (out_dir / "proxies.pdf").exists()
    assert all(c.chosen_printing.image_paths for c in manifest.cards)

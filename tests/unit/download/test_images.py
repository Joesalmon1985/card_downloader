from pathlib import Path

from card_downloader.download.images import ImageDownloader, RequestsImageDownloader
from card_downloader.scryfall.models import CardPrinting
import json


class FakeDownloader:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Path]] = []

    def download(self, url: str, dest: Path) -> None:
        self.calls.append((url, dest))
        dest.write_bytes(b"fake-image")


def _printing() -> CardPrinting:
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "fixtures/cards/sol_ring_normal.json").read_text()
    )
    return CardPrinting.from_api_dict(data)


def test_download_writes_file(tmp_path):
    fake = FakeDownloader()
    dl = ImageDownloader(fake)
    paths = dl.download_printing(_printing(), tmp_path)
    assert len(paths) == 1
    assert paths[0].exists()
    assert paths[0].read_bytes() == b"fake-image"


def test_skip_existing_unless_force(tmp_path):
    fake = FakeDownloader()
    dl = ImageDownloader(fake)
    p = _printing()
    dest = tmp_path / "Sol Ring__clu_1.png"
    dest.write_bytes(b"existing")
    paths = dl.download_printing(p, tmp_path)
    assert len(fake.calls) == 0
    assert paths[0].read_bytes() == b"existing"

    dl_force = ImageDownloader(fake, force=True)
    dl_force.download_printing(p, tmp_path)
    assert len(fake.calls) == 1

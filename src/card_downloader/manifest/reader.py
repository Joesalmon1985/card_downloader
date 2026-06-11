from pathlib import Path

from card_downloader.manifest.schema import Manifest


def read_manifest(path: Path) -> Manifest:
    return Manifest.load_json(path)

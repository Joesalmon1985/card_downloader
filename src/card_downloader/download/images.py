from pathlib import Path
from typing import Callable, Protocol

from card_downloader.download.filenames import image_path
from card_downloader.manifest.schema import Manifest
from card_downloader.scryfall.models import CardPrinting


class HttpDownloader(Protocol):
    def download(self, url: str, dest: Path) -> None:
        ...


class ImageDownloader:
    def __init__(
        self,
        downloader: HttpDownloader,
        *,
        image_size: str = "png",
        force: bool = False,
    ) -> None:
        self._downloader = downloader
        self._size = image_size
        self._force = force

    def download_printing(
        self,
        printing: CardPrinting,
        out_dir: Path,
    ) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        saved: list[Path] = []

        if printing.card_faces and printing.layout in {
            "transform",
            "modal_dfc",
            "double_faced_token",
            "split",
            "flip",
        }:
            for idx, face_label in enumerate(("front", "back")):
                if idx >= len(printing.card_faces):
                    break
                face = printing.card_faces[idx]
                uris = face.get("image_uris") or {}
                url = uris.get(self._size)
                if not url:
                    continue
                dest = image_path(out_dir, printing, face=face_label, ext=_ext(url))
                if dest.exists() and not self._force:
                    saved.append(dest)
                    continue
                self._downloader.download(url, dest)
                saved.append(dest)
        else:
            url = printing.primary_image_uri(self._size)
            if not url:
                return saved
            dest = image_path(out_dir, printing, ext=_ext(url))
            if dest.exists() and not self._force:
                saved.append(dest)
                return saved
            self._downloader.download(url, dest)
            saved.append(dest)
        return saved


def download_from_manifest(
    manifest: Manifest,
    printings_by_id: dict[str, CardPrinting],
    out_dir: Path,
    downloader: ImageDownloader,
) -> Manifest:
    """Download images and update manifest card rows with image paths."""
    from dataclasses import replace

    updated_cards = []
    for row in manifest.cards:
        printing = printings_by_id.get(row.chosen_printing.id)
        if printing is None:
            updated_cards.append(row)
            continue
        paths = downloader.download_printing(printing, out_dir)
        rel_paths = [str(p.relative_to(out_dir.parent)) if p.is_relative_to(out_dir.parent) else str(p) for p in paths]
        if not rel_paths:
            rel_paths = [f"images/{p.name}" for p in paths]
        else:
            rel_paths = [f"images/{Path(p).name}" for p in paths]
        cp = replace(row.chosen_printing, image_paths=rel_paths)
        updated_cards.append(replace(row, chosen_printing=cp))
    return replace(manifest, cards=updated_cards)


def _ext(url: str) -> str:
    clean = url.split("?", 1)[0]
    return clean.rsplit(".", 1)[-1]


class RequestsImageDownloader:
    """Stream download via requests."""

    def download(self, url: str, dest: Path) -> None:
        import requests

        dest.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in resp.iter_content(8192):
                    fh.write(chunk)

from pathlib import Path

from card_downloader.scryfall.models import CardPrinting


def safe_filename(name: str) -> str:
    return (
        name.replace("/", "_")
        .replace(":", "_")
        .replace("?", "")
        .replace("\\", "_")
        .replace("*", "_")
        .replace('"', "'")
    )


def image_filename(
    printing: CardPrinting,
    *,
    face: str = "",
    ext: str = "png",
) -> str:
    base = safe_filename(printing.name)
    set_part = printing.set_code
    cn = printing.collector_number.replace("/", "-")
    suffix = f"__{face}" if face else ""
    return f"{base}__{set_part}_{cn}{suffix}.{ext}"


def image_path(out_dir: Path, printing: CardPrinting, *, face: str = "", ext: str = "png") -> Path:
    return out_dir / image_filename(printing, face=face, ext=ext)

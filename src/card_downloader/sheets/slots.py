from dataclasses import dataclass
from pathlib import Path

from card_downloader.decklist.models import ParsedDeck
from card_downloader.manifest.schema import Manifest


@dataclass(frozen=True)
class SheetSlot:
    deck_name: str
    image_path: Path | None
    quantity_index: int = 0


def expand_to_slots(deck: ParsedDeck, manifest: Manifest, run_dir: Path) -> list[SheetSlot]:
    """Expand deck entries by quantity in decklist order."""
    path_by_name: dict[str, Path | None] = {}
    for row in manifest.cards:
        if row.chosen_printing.image_paths:
            rel = row.chosen_printing.image_paths[0]
            path_by_name[row.deck_name] = run_dir / rel
        else:
            path_by_name[row.deck_name] = None

    slots: list[SheetSlot] = []
    for entry in deck.entries:
        img = path_by_name.get(entry.name)
        for i in range(entry.quantity):
            slots.append(SheetSlot(deck_name=entry.name, image_path=img, quantity_index=i))
    return slots

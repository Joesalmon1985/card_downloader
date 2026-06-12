import csv
from pathlib import Path

from card_downloader.decklist.models import ParsedDeck
from card_downloader.decklist.parser import parse_decklist
from card_downloader.manifest.schema import CardManifestRow, Manifest

CSV_COLUMNS = [
    "deck_order",
    "requested_name",
    "normalised_name",
    "quantity",
    "resolved_name",
    "set_code",
    "set_name",
    "collector_number",
    "released_at",
    "lang",
    "border_color",
    "is_foil_available",
    "is_nonfoil_available",
    "is_promo",
    "is_universes_beyond_or_external",
    "is_white_border",
    "is_special_treatment",
    "image_url",
    "local_image_path",
    "score",
    "anchor_set",
    "in_anchor_set",
    "fallback_used",
    "fallback_reason",
    "status",
    "error_message",
]


def _bool_str(value: bool) -> str:
    return "true" if value else "false"


def _parse_error(error: str) -> tuple[str, str]:
    if ": " in error:
        name, message = error.split(": ", 1)
        return name.strip(), message.strip()
    return error.strip(), error.strip()


def _ok_row(
    deck_order: int,
    entry_name: str,
    card: CardManifestRow,
    manifest: Manifest,
) -> dict[str, str]:
    cp = card.chosen_printing
    anchor = manifest.selection_summary.anchor_set
    finishes = cp.finishes or []
    return {
        "deck_order": str(deck_order),
        "requested_name": entry_name,
        "normalised_name": entry_name,
        "quantity": str(card.quantity),
        "resolved_name": cp.printing_name or card.deck_name,
        "set_code": cp.set,
        "set_name": cp.set_name,
        "collector_number": cp.collector_number,
        "released_at": cp.released_at,
        "lang": cp.lang,
        "border_color": cp.border_color,
        "is_foil_available": _bool_str("foil" in finishes),
        "is_nonfoil_available": _bool_str("nonfoil" in finishes),
        "is_promo": _bool_str(cp.promo),
        "is_universes_beyond_or_external": _bool_str(cp.is_universes_beyond),
        "is_white_border": _bool_str(cp.border_color == "white"),
        "is_special_treatment": _bool_str(cp.has_special_frame),
        "image_url": cp.image_url,
        "local_image_path": cp.image_paths[0] if cp.image_paths else "",
        "score": f"{card.score:.1f}",
        "anchor_set": anchor,
        "in_anchor_set": _bool_str(cp.set == anchor),
        "fallback_used": _bool_str(bool(card.fallback_reasons)),
        "fallback_reason": "; ".join(card.fallback_reasons),
        "status": "ok",
        "error_message": "",
    }


def _error_row(
    deck_order: int,
    entry_name: str,
    quantity: int,
    manifest: Manifest,
    error_message: str,
) -> dict[str, str]:
    anchor = manifest.selection_summary.anchor_set
    return {
        "deck_order": str(deck_order),
        "requested_name": entry_name,
        "normalised_name": entry_name,
        "quantity": "0",
        "resolved_name": "",
        "set_code": "",
        "set_name": "",
        "collector_number": "",
        "released_at": "",
        "lang": "",
        "border_color": "",
        "is_foil_available": "false",
        "is_nonfoil_available": "false",
        "is_promo": "false",
        "is_universes_beyond_or_external": "false",
        "is_white_border": "false",
        "is_special_treatment": "false",
        "image_url": "",
        "local_image_path": "",
        "score": "",
        "anchor_set": anchor,
        "in_anchor_set": "false",
        "fallback_used": "false",
        "fallback_reason": "",
        "status": "error",
        "error_message": error_message,
    }


def build_card_choice_rows(manifest: Manifest, deck: ParsedDeck) -> list[dict[str, str]]:
    cards_by_name = {c.deck_name: c for c in manifest.cards}
    errors_by_name: dict[str, str] = {}
    for err in manifest.errors:
        name, message = _parse_error(err)
        errors_by_name.setdefault(name, message)

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, entry in enumerate(deck.entries, start=1):
        if entry.name in seen:
            continue
        seen.add(entry.name)

        if entry.name in cards_by_name:
            rows.append(_ok_row(index, entry.name, cards_by_name[entry.name], manifest))
        elif entry.name in errors_by_name:
            rows.append(
                _error_row(
                    index,
                    entry.name,
                    entry.quantity,
                    manifest,
                    errors_by_name[entry.name],
                )
            )

    return rows


def write_card_choices_csv(
    manifest: Manifest,
    path: Path,
    *,
    decklist_path: Path | None = None,
) -> None:
    source = decklist_path or Path(manifest.decklist_path)
    if not source.is_absolute() and decklist_path is None:
        candidate = path.parent / source
        if candidate.exists():
            source = candidate
    deck = parse_decklist(source.read_text(encoding="utf-8"))
    rows = build_card_choice_rows(manifest, deck)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

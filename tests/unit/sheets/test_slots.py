from pathlib import Path

from card_downloader.decklist.models import DeckEntry, ParsedDeck
from card_downloader.manifest.schema import (
    CardManifestRow,
    ChosenPrintingRecord,
    Manifest,
    SelectionSummary,
    utc_now_iso,
)
from card_downloader.sheets.slots import expand_to_slots


def _manifest_for(deck: ParsedDeck, run_dir: Path) -> Manifest:
    cards = []
    for e in deck.entries:
        rel = f"images/{e.name.replace(' ', '_')}.png"
        (run_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        cards.append(
            CardManifestRow(
                deck_name=e.name,
                quantity=e.quantity,
                oracle_id="oid",
                chosen_printing=ChosenPrintingRecord(
                    id="id",
                    set="clu",
                    collector_number="1",
                    lang="en",
                    border_color="black",
                    scryfall_uri="https://example.com",
                    image_url="https://example.com/img.png",
                    image_paths=[rel],
                ),
                score=1.0,
                score_breakdown={},
                fallback_reasons=[],
                was_outlier=False,
            )
        )
    return Manifest(
        version=1,
        decklist_path="deck.txt",
        generated_at=utc_now_iso(),
        options={},
        selection_summary=SelectionSummary("clu", 1.0, 1, 0, 1.0),
        cards=cards,
    )


def test_quantity_expansion(tmp_path):
    deck = ParsedDeck(entries=(DeckEntry(11, "Snow-Covered Mountain"), DeckEntry(1, "Sol Ring")))
    manifest = _manifest_for(deck, tmp_path)
    slots = expand_to_slots(deck, manifest, tmp_path)
    assert len(slots) == 12
    assert sum(1 for s in slots if s.deck_name == "Snow-Covered Mountain") == 11


def test_deck_order_preserved(tmp_path):
    deck = ParsedDeck(entries=(DeckEntry(1, "Alpha"), DeckEntry(1, "Beta")))
    manifest = _manifest_for(deck, tmp_path)
    slots = expand_to_slots(deck, manifest, tmp_path)
    assert [s.deck_name for s in slots] == ["Alpha", "Beta"]

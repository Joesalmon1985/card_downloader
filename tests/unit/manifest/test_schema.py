from card_downloader.manifest.schema import (
    CardManifestRow,
    ChosenPrintingRecord,
    Manifest,
    OutputSummary,
    PdfOptions,
    SelectionSummary,
    utc_now_iso,
)


def test_manifest_round_trip():
    manifest = Manifest(
        version=1,
        decklist_path="deck.txt",
        generated_at=utc_now_iso(),
        options={"lang": "en"},
        selection_summary=SelectionSummary(
            anchor_set="clu",
            coverage=0.5,
            cards_in_anchor=1,
            outliers=1,
            total_score=100.0,
        ),
        cards=[
            CardManifestRow(
                deck_name="Sol Ring",
                quantity=1,
                oracle_id="oid",
                chosen_printing=ChosenPrintingRecord(
                    id="id1",
                    set="clu",
                    collector_number="1",
                    lang="en",
                    border_color="black",
                    scryfall_uri="https://scryfall.com/card/clu/1/sol-ring",
                    image_url="https://example.com/sol.png",
                    image_paths=["images/sol.png"],
                ),
                score=41.0,
                score_breakdown={"nonfoil": 8, "border": 6},
                fallback_reasons=[],
                was_outlier=False,
            )
        ],
        outputs=OutputSummary(
            pdf_path="proxies.pdf",
            pdf_pages=1,
            pdf_cards_placed=1,
            pdf_options=PdfOptions(),
        ),
    )
    d = manifest.to_dict()
    restored = Manifest.from_dict(d)
    assert restored.selection_summary.anchor_set == "clu"
    assert restored.cards[0].deck_name == "Sol Ring"
    assert restored.outputs.pdf_pages == 1

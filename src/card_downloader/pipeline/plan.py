from dataclasses import replace
from pathlib import Path

from card_downloader.decklist.parser import parse_decklist
from card_downloader.manifest.schema import (
    CardManifestRow,
    ChosenPrintingRecord,
    Manifest,
    SelectionSummary,
    utc_now_iso,
)
from card_downloader.manifest.csv_writer import write_card_choices_csv
from card_downloader.manifest.writer import write_manifest, write_selection_report
from card_downloader.scryfall.client import ScryfallClient
from card_downloader.scryfall.errors import ScryfallAPIError
from card_downloader.selection.anchors import rank_anchors
from card_downloader.selection.classify import classify_printing
from card_downloader.selection.models import SelectionOptions
from card_downloader.selection.optimizer import best_assignment, build_pools


def create_manifest(
    decklist_path: Path,
    *,
    client: ScryfallClient | None = None,
    opts: SelectionOptions | None = None,
    cache_dir: Path | None = None,
) -> tuple[Manifest, dict[str, object]]:
    """Resolve printings and build manifest without downloading images."""
    opts = opts or SelectionOptions()
    text = decklist_path.read_text(encoding="utf-8")
    deck = parse_decklist(text)

    unique_names = list(dict.fromkeys(e.name for e in deck.entries))
    quantities = {e.name: e.quantity for e in deck.entries}

    scryfall = client or ScryfallClient(cache_dir=cache_dir)

    printings_by_name: dict[str, list] = {}
    ub_ids_by_name: dict[str, set[str]] = {}
    errors: list[str] = []
    printings_by_id: dict[str, object] = {}

    for name in unique_names:
        try:
            printings = scryfall.search_printings(name)
            printings_by_name[name] = printings
            ub_ids_by_name[name] = scryfall.search_universes_beyond_ids(name)
            for p in printings:
                printings_by_id[p.id] = p
        except ScryfallAPIError as exc:
            errors.append(f"{name}: {exc}")
            printings_by_name[name] = []
            ub_ids_by_name[name] = set()
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            printings_by_name[name] = []
            ub_ids_by_name[name] = set()

    pools = build_pools(printings_by_name, ub_ids_by_name, opts)
    anchors = rank_anchors(pools)
    assignment = best_assignment(unique_names, quantities, pools, anchors, ub_ids_by_name, opts)

    cards: list[CardManifestRow] = []
    for a in assignment.assignments:
        p = a.printing
        classification = classify_printing(
            p,
            ub_ids_by_name.get(a.deck_name, set()),
            opts,
        )
        breakdown = {
            "nonfoil": a.breakdown.nonfoil,
            "border": a.breakdown.border,
            "not_ub": a.breakdown.not_ub,
            "frame": a.breakdown.frame,
            "promo": a.breakdown.promo,
            "english": a.breakdown.english,
            "image": a.breakdown.image,
            "paper": a.breakdown.paper,
            "set_type": a.breakdown.set_type,
            "coherence_bonus": a.coherence_bonus,
        }
        cards.append(
            CardManifestRow(
                deck_name=a.deck_name,
                quantity=a.quantity,
                oracle_id=p.oracle_id,
                chosen_printing=ChosenPrintingRecord(
                    id=p.id,
                    set=p.set_code,
                    collector_number=p.collector_number,
                    lang=p.lang,
                    border_color=p.border_color,
                    scryfall_uri=p.scryfall_uri,
                    image_url=p.primary_image_uri(opts.image_size) or "",
                    image_paths=[],
                    set_name=p.set_name,
                    released_at=p.released_at,
                    printing_name=p.name,
                    promo=classification.is_promo,
                    finishes=list(p.finishes),
                    is_universes_beyond=classification.is_universes_beyond,
                    has_special_frame=classification.has_special_frame,
                ),
                score=a.score,
                score_breakdown=breakdown,
                fallback_reasons=list(a.fallback_reasons),
                was_outlier=a.was_outlier,
            )
        )

    manifest = Manifest(
        version=1,
        decklist_path=str(decklist_path),
        generated_at=utc_now_iso(),
        options={
            "lang": opts.lang,
            "image_size": opts.image_size,
            "allow_ub": opts.allow_ub,
            "allow_white_border": opts.allow_white_border,
            "allow_promo": opts.allow_promo,
        },
        selection_summary=SelectionSummary(
            anchor_set=assignment.anchor_set,
            coverage=assignment.coverage,
            cards_in_anchor=assignment.cards_in_anchor,
            outliers=assignment.outliers,
            total_score=assignment.total_score,
        ),
        cards=cards,
        errors=errors,
    )
    return manifest, printings_by_id


def run_plan(
    decklist_path: Path,
    out_dir: Path,
    *,
    client: ScryfallClient | None = None,
    opts: SelectionOptions | None = None,
    cache_dir: Path | None = None,
) -> Manifest:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, _ = create_manifest(
        decklist_path,
        client=client,
        opts=opts,
        cache_dir=cache_dir,
    )
    manifest_path = out_dir / "manifest.json"
    write_manifest(manifest, manifest_path)
    write_selection_report(manifest, out_dir / "selection-report.md")
    write_card_choices_csv(
        manifest,
        out_dir / "card_choices.csv",
        decklist_path=decklist_path,
    )
    return manifest

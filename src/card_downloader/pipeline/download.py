from dataclasses import replace
from pathlib import Path

from card_downloader.decklist.parser import parse_decklist
from card_downloader.download.images import ImageDownloader, RequestsImageDownloader
from card_downloader.manifest.reader import read_manifest
from card_downloader.manifest.schema import Manifest, OutputSummary, PdfOptions
from card_downloader.manifest.csv_writer import write_card_choices_csv
from card_downloader.manifest.writer import write_manifest, write_selection_report
from card_downloader.pipeline.plan import create_manifest, run_plan
from card_downloader.scryfall.client import ScryfallClient
from card_downloader.selection.models import SelectionOptions
from card_downloader.sheets.builder import PdfBuildOptions, build_pdf as build_proxy_pdf
from card_downloader.sheets.slots import expand_to_slots


def run_download(
    decklist_path: Path,
    out_dir: Path,
    *,
    client: ScryfallClient | None = None,
    opts: SelectionOptions | None = None,
    cache_dir: Path | None = None,
    build_pdf: bool = True,
    pdf_name: str = "proxies.pdf",
    paper: str = "a4",
    dpi: int = 300,
    gap_mm: float = 1.0,
    force: bool = False,
) -> Manifest:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, printings_by_id = create_manifest(
        decklist_path,
        client=client,
        opts=opts,
        cache_dir=cache_dir,
    )

    images_dir = out_dir / "images"
    downloader = ImageDownloader(
        RequestsImageDownloader(),
        image_size=(opts or SelectionOptions()).image_size,
        force=force,
    )

    updated_cards = []
    for row in manifest.cards:
        printing = printings_by_id.get(row.chosen_printing.id)
        if printing is None:
            updated_cards.append(row)
            continue
        paths = downloader.download_printing(printing, images_dir)
        rel_paths = [f"images/{p.name}" for p in paths]
        cp = replace(row.chosen_printing, image_paths=rel_paths)
        updated_cards.append(replace(row, chosen_printing=cp))

    pdf_pages = 0
    pdf_cards = 0
    pdf_path = pdf_name

    if build_pdf:
        deck = parse_decklist(decklist_path.read_text(encoding="utf-8"))
        manifest = replace(manifest, cards=updated_cards)
        slots = expand_to_slots(deck, manifest, out_dir)
        pdf_result = build_proxy_pdf(
            slots,
            out_dir / pdf_name,
            PdfBuildOptions(paper=paper, dpi=dpi, gap_mm=gap_mm),
        )
        pdf_pages = pdf_result.pages
        pdf_cards = pdf_result.cards_placed
    else:
        manifest = replace(manifest, cards=updated_cards)

    manifest = replace(
        manifest,
        outputs=OutputSummary(
            images_dir="images/",
            pdf_path=pdf_path if build_pdf else "",
            pdf_pages=pdf_pages,
            pdf_cards_placed=pdf_cards,
            pdf_options=PdfOptions(paper=paper, dpi=dpi, gap_mm=gap_mm),
            csv_path="card_choices.csv",
        ),
    )

    write_manifest(manifest, out_dir / "manifest.json")
    write_selection_report(manifest, out_dir / "selection-report.md")
    write_card_choices_csv(
        manifest,
        out_dir / "card_choices.csv",
        decklist_path=decklist_path,
    )
    return manifest


def run_sheets_from_manifest(
    manifest_path: Path,
    out_pdf: Path,
    *,
    paper: str = "a4",
    dpi: int = 300,
) -> None:
    manifest = read_manifest(manifest_path)
    run_dir = manifest_path.parent
    deck_path = Path(manifest.decklist_path)
    if not deck_path.is_absolute():
        deck_path = run_dir / deck_path
        if not deck_path.exists():
            deck_path = Path(manifest.decklist_path)
    deck = parse_decklist(deck_path.read_text(encoding="utf-8"))
    slots = expand_to_slots(deck, manifest, run_dir)
    result = build_proxy_pdf(slots, out_pdf, PdfBuildOptions(paper=paper, dpi=dpi))
    manifest = replace(
        manifest,
        outputs=replace(
            manifest.outputs,
            pdf_path=str(out_pdf.name),
            pdf_pages=result.pages,
            pdf_cards_placed=result.cards_placed,
            pdf_options=PdfOptions(paper=paper, dpi=dpi),
        ),
    )
    write_manifest(manifest, manifest_path)

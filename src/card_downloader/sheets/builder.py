import math
import tempfile
from dataclasses import dataclass
from pathlib import Path

import img2pdf
from PIL import Image

from card_downloader.sheets.constants import CARDS_PER_PAGE, PAPER_SIZES_IN
from card_downloader.sheets.geometry import page_size_px, slot_position
from card_downloader.sheets.image_prep import prepare_image
from card_downloader.sheets.slots import SheetSlot


@dataclass(frozen=True)
class PdfBuildOptions:
    paper: str = "a4"
    dpi: int = 300
    gap_mm: float = 1.0


@dataclass(frozen=True)
class PdfBuildResult:
    path: Path
    pages: int
    cards_placed: int


def build_pdf(
    slots: list[SheetSlot],
    output_path: Path,
    opts: PdfBuildOptions | None = None,
) -> PdfBuildResult:
    opts = opts or PdfBuildOptions()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_w, page_h = page_size_px(opts.paper, opts.dpi)
    paper_w_in, paper_h_in = PAPER_SIZES_IN[opts.paper]
    total_pages = math.ceil(len(slots) / CARDS_PER_PAGE) if slots else 0
    cards_placed = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        page_paths: list[Path] = []

        for page_idx in range(max(total_pages, 1) if slots else 0):
            sheet = Image.new("RGB", (page_w, page_h), "black")
            start = page_idx * CARDS_PER_PAGE
            page_slots = slots[start : start + CARDS_PER_PAGE]

            for i, slot in enumerate(page_slots):
                pos = slot_position(i, paper=opts.paper, dpi=opts.dpi, gap_mm=opts.gap_mm)
                size = (pos.width, pos.height)
                img_path = str(slot.image_path) if slot.image_path and slot.image_path.exists() else None
                prepared = prepare_image(img_path, size)
                sheet.paste(prepared, (pos.x, pos.y))
                if img_path:
                    cards_placed += 1

            page_path = tmp / f"sheet_{page_idx:03d}.png"
            sheet.save(page_path, "PNG", optimize=True)
            page_paths.append(page_path)

        if not page_paths:
            # empty deck — one blank page
            sheet = Image.new("RGB", (page_w, page_h), "black")
            page_path = tmp / "sheet_000.png"
            sheet.save(page_path, "PNG")
            page_paths = [page_path]
            total_pages = 0

        layout_fun = img2pdf.get_layout_fun(
            pagesize=(img2pdf.in_to_pt(paper_w_in), img2pdf.in_to_pt(paper_h_in))
        )
        with output_path.open("wb") as fh:
            fh.write(img2pdf.convert([str(p) for p in page_paths], layout_fun=layout_fun))

    return PdfBuildResult(path=output_path, pages=total_pages or len(page_paths), cards_placed=cards_placed)

#!/usr/bin/env python3
"""
make_proxy_sheets.py

Build printable 3x3 sheets of Magic card images on a BLACK background.

Features:
- Standard Magic card size: 2.5" x 3.5"
- 3 columns x 3 rows per page
- 1 mm gap between cards
- A4 by default (good for UK printers), optional Letter
- Accepts PNG / JPG / JPEG / WEBP images
- Outputs a single PDF

Usage:
    python3 make_proxy_sheets.py /path/to/card_images -o proxies_black.pdf

Optional:
    python3 make_proxy_sheets.py /path/to/card_images -o proxies_black.pdf --paper letter
    python3 make_proxy_sheets.py /path/to/card_images -o proxies_black.pdf --dpi 300
"""

import argparse
import math
import pathlib
import tempfile
from typing import List, Tuple

import img2pdf
from PIL import Image

# ----------------------------- Defaults ------------------------------------ #

DEFAULT_DPI = 300
CARD_W_IN = 2.5
CARD_H_IN = 3.5
GAP_MM = 1.0
COLS = 3
ROWS = 3

PAPER_SIZES_IN = {
    "a4": (8.27, 11.69),
    "letter": (8.5, 11.0),
}

VALID_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


# ----------------------------- Helpers ------------------------------------- #

def inches_to_px(inches: float, dpi: int) -> int:
    return int(round(inches * dpi))


def mm_to_px(mm: float, dpi: int) -> int:
    return inches_to_px(mm / 25.4, dpi)


def collect_images(folder: pathlib.Path) -> List[pathlib.Path]:
    if not folder.exists():
        raise FileNotFoundError(f"Image folder does not exist: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder}")

    images = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTS
    )

    if not images:
        raise FileNotFoundError(
            f"No supported images found in {folder} "
            f"(supported: {', '.join(sorted(VALID_EXTS))})"
        )

    return images


def open_and_prepare_image(path: pathlib.Path, size: Tuple[int, int]) -> Image.Image:
    """
    Open image, flatten transparency onto black, convert to RGB, resize to card size.
    """
    with Image.open(path) as im:
        im = im.convert("RGBA")

        # Flatten transparency onto black background
        black_bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(black_bg, im)

        im = im.convert("RGB")
        im = im.resize(size, Image.LANCZOS)
        return im


# ----------------------------- Main ---------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lay out Magic card images as 3x3 printable PDF sheets on a black background."
    )
    parser.add_argument(
        "image_folder",
        help="Folder containing card images (PNG/JPG/JPEG/WEBP)."
    )
    parser.add_argument(
        "-o", "--output",
        default="cards_proxy_sheets_black.pdf",
        help="Output PDF filename."
    )
    parser.add_argument(
        "--paper",
        choices=sorted(PAPER_SIZES_IN.keys()),
        default="a4",
        help="Paper size."
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help="Render DPI for sheet generation."
    )
    parser.add_argument(
        "--gap-mm",
        type=float,
        default=GAP_MM,
        help="Gap between cards in millimetres."
    )

    args = parser.parse_args()

    src_dir = pathlib.Path(args.image_folder).expanduser().resolve()
    out_pdf = pathlib.Path(args.output).expanduser().resolve()
    dpi = args.dpi
    gap_mm = args.gap_mm

    images = collect_images(src_dir)

    paper_w_in, paper_h_in = PAPER_SIZES_IN[args.paper]
    page_w_px = inches_to_px(paper_w_in, dpi)
    page_h_px = inches_to_px(paper_h_in, dpi)
    card_w_px = inches_to_px(CARD_W_IN, dpi)
    card_h_px = inches_to_px(CARD_H_IN, dpi)
    gap_px = mm_to_px(gap_mm, dpi)

    grid_w_px = COLS * card_w_px + (COLS + 1) * gap_px
    grid_h_px = ROWS * card_h_px + (ROWS + 1) * gap_px

    if grid_w_px > page_w_px or grid_h_px > page_h_px:
        raise ValueError(
            "Card grid does not fit on the selected paper size. "
            "Try smaller cards, smaller gaps, or a larger paper size."
        )

    left_margin = (page_w_px - grid_w_px) // 2
    top_margin = (page_h_px - grid_h_px) // 2

    cards_per_page = COLS * ROWS
    total_pages = math.ceil(len(images) / cards_per_page)

    print(f"Found {len(images)} image(s).")
    print(f"Building {total_pages} page(s) on {args.paper.upper()} with black background...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = pathlib.Path(tmpdir)
        page_images = []

        current_sheet = Image.new("RGB", (page_w_px, page_h_px), "black")
        sheet_index = 0

        for i, img_path in enumerate(images):
            prepared = open_and_prepare_image(img_path, (card_w_px, card_h_px))

            slot = i % cards_per_page
            col = slot % COLS
            row = slot // COLS

            x = left_margin + gap_px + col * (card_w_px + gap_px)
            y = top_margin + gap_px + row * (card_h_px + gap_px)

            current_sheet.paste(prepared, (x, y))

            is_page_end = (slot == cards_per_page - 1)
            is_last_image = (i == len(images) - 1)

            if is_page_end or is_last_image:
                page_path = tmpdir_path / f"sheet_{sheet_index:03d}.png"
                current_sheet.save(page_path, "PNG", optimize=True)
                page_images.append(page_path)
                sheet_index += 1

                if not is_last_image:
                    current_sheet = Image.new("RGB", (page_w_px, page_h_px), "black")

        layout_fun = img2pdf.get_layout_fun(
            pagesize=(img2pdf.in_to_pt(paper_w_in), img2pdf.in_to_pt(paper_h_in))
        )

        with out_pdf.open("wb") as f:
            f.write(
                img2pdf.convert(
                    [str(p) for p in page_images],
                    layout_fun=layout_fun
                )
            )

    print(f"Done: {out_pdf}")


if __name__ == "__main__":
    main()

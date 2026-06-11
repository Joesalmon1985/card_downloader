import math
from dataclasses import dataclass

from card_downloader.sheets.constants import (
    CARD_H_IN,
    CARD_W_IN,
    CARDS_PER_PAGE,
    COLS,
    DEFAULT_DPI,
    GAP_MM,
    PAPER_SIZES_IN,
    ROWS,
)


def inches_to_px(inches: float, dpi: int) -> int:
    return int(round(inches * dpi))


def mm_to_px(mm: float, dpi: int) -> int:
    return inches_to_px(mm / 25.4, dpi)


def page_count(total_slots: int) -> int:
    if total_slots <= 0:
        return 0
    return math.ceil(total_slots / CARDS_PER_PAGE)


def grid_fits_paper(paper: str = "a4", dpi: int = DEFAULT_DPI, gap_mm: float = GAP_MM) -> bool:
    paper_w_in, paper_h_in = PAPER_SIZES_IN[paper]
    page_w = inches_to_px(paper_w_in, dpi)
    page_h = inches_to_px(paper_h_in, dpi)
    card_w = inches_to_px(CARD_W_IN, dpi)
    card_h = inches_to_px(CARD_H_IN, dpi)
    gap = mm_to_px(gap_mm, dpi)
    grid_w = COLS * card_w + (COLS + 1) * gap
    grid_h = ROWS * card_h + (ROWS + 1) * gap
    return grid_w <= page_w and grid_h <= page_h


@dataclass(frozen=True)
class SlotPosition:
    x: int
    y: int
    width: int
    height: int


def slot_position(slot_index: int, paper: str = "a4", dpi: int = DEFAULT_DPI, gap_mm: float = GAP_MM) -> SlotPosition:
    paper_w_in, paper_h_in = PAPER_SIZES_IN[paper]
    page_w = inches_to_px(paper_w_in, dpi)
    page_h = inches_to_px(paper_h_in, dpi)
    card_w = inches_to_px(CARD_W_IN, dpi)
    card_h = inches_to_px(CARD_H_IN, dpi)
    gap = mm_to_px(gap_mm, dpi)
    grid_w = COLS * card_w + (COLS + 1) * gap
    grid_h = ROWS * card_h + (ROWS + 1) * gap
    left_margin = (page_w - grid_w) // 2
    top_margin = (page_h - grid_h) // 2

    slot_on_page = slot_index % CARDS_PER_PAGE
    col = slot_on_page % COLS
    row = slot_on_page // COLS
    x = left_margin + gap + col * (card_w + gap)
    y = top_margin + gap + row * (card_h + gap)
    return SlotPosition(x=x, y=y, width=card_w, height=card_h)


def page_size_px(paper: str = "a4", dpi: int = DEFAULT_DPI) -> tuple[int, int]:
    w_in, h_in = PAPER_SIZES_IN[paper]
    return inches_to_px(w_in, dpi), inches_to_px(h_in, dpi)

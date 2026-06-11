from card_downloader.sheets.constants import CARDS_PER_PAGE
from card_downloader.sheets.geometry import grid_fits_paper, page_count, slot_position


def test_page_count_106():
    assert page_count(106) == 12


def test_page_count_zero():
    assert page_count(0) == 0


def test_grid_fits_a4():
    assert grid_fits_paper("a4", dpi=300) is True


def test_slot_zero_coords():
    pos = slot_position(0, paper="a4", dpi=300)
    assert pos.width > 0
    assert pos.height > 0
    assert pos.x >= 0
    assert pos.y >= 0


def test_ninth_slot_on_same_page():
    pos8 = slot_position(8, paper="a4", dpi=300)
    pos9 = slot_position(9, paper="a4", dpi=300)
    # slot 9 starts new page — y resets to top row
    assert pos9.y <= pos8.y

from pathlib import Path

from PIL import Image

from card_downloader.sheets.builder import PdfBuildOptions, build_pdf
from card_downloader.sheets.slots import SheetSlot


def test_build_pdf_from_fixtures(tmp_path):
    img = tmp_path / "card.png"
    Image.new("RGB", (745, 1040), (128, 128, 128)).save(img)
    slots = [SheetSlot("Sol Ring", img) for _ in range(10)]
    out = tmp_path / "proxies.pdf"
    result = build_pdf(slots, out, PdfBuildOptions())
    assert out.exists()
    assert out.stat().st_size > 1000
    assert result.pages == 2
    assert result.cards_placed == 10

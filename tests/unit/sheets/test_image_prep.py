from pathlib import Path

from PIL import Image

from card_downloader.sheets.geometry import slot_position
from card_downloader.sheets.image_prep import prepare_image


def test_transparent_flattens_to_black(tmp_path):
    path = tmp_path / "transparent.png"
    img = Image.new("RGBA", (100, 140), (0, 0, 0, 0))
    img.save(path)
    pos = slot_position(0, dpi=300)
    result = prepare_image(str(path), (pos.width, pos.height))
    assert result.size == (pos.width, pos.height)
    assert result.getpixel((0, 0)) == (0, 0, 0)


def test_blank_when_no_path():
    pos = slot_position(0, dpi=300)
    result = prepare_image(None, (pos.width, pos.height))
    assert result.getpixel((0, 0)) == (0, 0, 0)

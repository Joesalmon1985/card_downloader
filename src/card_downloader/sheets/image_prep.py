from PIL import Image


def prepare_image(path: str | None, size: tuple[int, int]) -> Image.Image:
    """Open image, flatten transparency onto black, resize to card size."""
    if path is None:
        return _blank_card(size)
    with Image.open(path) as im:
        im = im.convert("RGBA")
        black_bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(black_bg, im)
        im = im.convert("RGB")
        return im.resize(size, Image.LANCZOS)


def _blank_card(size: tuple[int, int]) -> Image.Image:
    return Image.new("RGB", size, (0, 0, 0))

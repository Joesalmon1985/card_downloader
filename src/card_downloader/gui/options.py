from dataclasses import dataclass
from pathlib import Path

from card_downloader.selection.models import SelectionOptions

DEFAULT_OUTPUT_DIR = Path("data/runs/gui-run")
VALID_IMAGE_SIZES = frozenset({"png", "large", "normal"})
VALID_PAPER = frozenset({"a4", "letter"})


@dataclass(frozen=True)
class GuiRunOptions:
    decklist_path: Path
    output_dir: Path = DEFAULT_OUTPUT_DIR
    image_size: str = "png"
    paper: str = "a4"
    dpi: int = 300
    gap_mm: float = 1.0
    build_pdf: bool = True
    allow_ub: bool = False
    allow_white_border: bool = False
    allow_promo: bool = False


def to_selection_options(opts: GuiRunOptions) -> SelectionOptions:
    return SelectionOptions(
        lang="en",
        allow_ub=opts.allow_ub,
        allow_white_border=opts.allow_white_border,
        allow_promo=opts.allow_promo,
        image_size=opts.image_size,
    )


def to_download_kwargs(opts: GuiRunOptions) -> dict:
    return {
        "decklist_path": opts.decklist_path.expanduser().resolve(),
        "out_dir": opts.output_dir.expanduser().resolve(),
        "opts": to_selection_options(opts),
        "build_pdf": opts.build_pdf,
        "paper": opts.paper,
        "dpi": opts.dpi,
        "gap_mm": opts.gap_mm,
    }


def validate(opts: GuiRunOptions) -> list[str]:
    errors: list[str] = []
    decklist = opts.decklist_path.expanduser()
    if not str(decklist).strip():
        errors.append("Decklist path is required.")
    elif not decklist.is_file():
        errors.append(f"Decklist file not found: {decklist}")

    if opts.image_size not in VALID_IMAGE_SIZES:
        errors.append(f"Invalid image size: {opts.image_size!r}")

    if opts.paper not in VALID_PAPER:
        errors.append(f"Invalid paper size: {opts.paper!r}")

    if opts.dpi <= 0:
        errors.append("DPI must be a positive integer.")

    if opts.gap_mm <= 0:
        errors.append("Gap (mm) must be a positive number.")

    out = opts.output_dir.expanduser()
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        errors.append(f"Cannot create output directory: {exc}")

    return errors

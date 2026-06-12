import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from card_downloader.gui.options import GuiRunOptions, to_download_kwargs, validate
from card_downloader.pipeline.download import run_download
from card_downloader.scryfall.errors import ScryfallAPIError


@dataclass
class RunResult:
    success: bool
    message: str
    out_dir: Path | None = None
    manifest_path: Path | None = None
    report_path: Path | None = None
    csv_path: Path | None = None
    pdf_path: Path | None = None
    log_lines: list[str] = field(default_factory=list)


def _log(on_log: Callable[[str], None] | None, line: str, lines: list[str]) -> None:
    lines.append(line)
    if on_log:
        on_log(line)


def execute_run(
    opts: GuiRunOptions,
    *,
    cache_dir: Path | None = None,
    on_log: Callable[[str], None] | None = None,
) -> RunResult:
    log_lines: list[str] = []
    errors = validate(opts)
    if errors:
        for err in errors:
            _log(on_log, f"Error: {err}", log_lines)
        return RunResult(
            success=False,
            message="Validation failed.",
            log_lines=log_lines,
        )

    kwargs = to_download_kwargs(opts)
    out_dir: Path = kwargs["out_dir"]
    build_pdf: bool = kwargs["build_pdf"]

    _log(on_log, f"Starting download for {kwargs['decklist_path'].name}…", log_lines)
    _log(on_log, f"Output folder: {out_dir}", log_lines)

    try:
        manifest = run_download(
            **kwargs,
            cache_dir=cache_dir or Path("data/cache"),
        )
    except ScryfallAPIError as exc:
        _log(on_log, str(exc), log_lines)
        return RunResult(
            success=False,
            message=str(exc),
            out_dir=out_dir,
            log_lines=log_lines,
        )
    except Exception as exc:
        _log(on_log, f"Unexpected error: {exc}", log_lines)
        for line in traceback.format_exc().splitlines():
            _log(on_log, line, log_lines)
        return RunResult(
            success=False,
            message=str(exc),
            out_dir=out_dir,
            log_lines=log_lines,
        )

    if not manifest.cards:
        _log(on_log, "Download failed — no cards were resolved.", log_lines)
        for err in manifest.errors:
            _log(on_log, f"  {err}", log_lines)
        return RunResult(
            success=False,
            message="No cards were resolved.",
            out_dir=out_dir,
            manifest_path=out_dir / "manifest.json",
            report_path=out_dir / "selection-report.md",
            log_lines=log_lines,
        )

    images_ok = sum(1 for c in manifest.cards if c.chosen_printing.image_paths)
    if images_ok == 0 and build_pdf:
        _log(on_log, "Download failed — no card images were saved.", log_lines)
        for err in manifest.errors:
            _log(on_log, f"  {err}", log_lines)
        return RunResult(
            success=False,
            message="No card images were saved.",
            out_dir=out_dir,
            manifest_path=out_dir / "manifest.json",
            report_path=out_dir / "selection-report.md",
            log_lines=log_lines,
        )

    manifest_path = out_dir / "manifest.json"
    report_path = out_dir / "selection-report.md"
    csv_path = out_dir / "card_choices.csv" if (out_dir / "card_choices.csv").is_file() else None
    pdf_path = out_dir / "proxies.pdf" if build_pdf and pdf_path_exists(out_dir) else None

    _log(on_log, f"Done: {len(manifest.cards)} card(s), {images_ok} image(s).", log_lines)
    _log(on_log, f"Manifest: {manifest_path}", log_lines)
    _log(on_log, f"Report: {report_path}", log_lines)
    if csv_path:
        _log(on_log, f"CSV: {csv_path}", log_lines)
    if pdf_path:
        _log(on_log, f"PDF: {pdf_path}", log_lines)
    if manifest.errors:
        _log(on_log, f"Warning: {len(manifest.errors)} card(s) could not be resolved.", log_lines)

    return RunResult(
        success=True,
        message=f"Download complete ({len(manifest.cards)} card(s)).",
        out_dir=out_dir,
        manifest_path=manifest_path,
        report_path=report_path,
        csv_path=csv_path,
        pdf_path=pdf_path,
        log_lines=log_lines,
    )


def pdf_path_exists(out_dir: Path) -> bool:
    return (out_dir / "proxies.pdf").is_file()

import argparse
import sys
from pathlib import Path

from card_downloader.pipeline.download import run_download, run_sheets_from_manifest
from card_downloader.pipeline.plan import run_plan
from card_downloader.scryfall.errors import ScryfallAPIError
from card_downloader.selection.models import SelectionOptions


def _selection_options(args: argparse.Namespace) -> SelectionOptions:
    return SelectionOptions(
        lang=args.lang,
        allow_ub=args.allow_ub,
        allow_white_border=args.allow_white_border,
        allow_promo=args.allow_promo,
        image_size=args.size,
    )


def _print_scryfall_error(context: str, exc: ScryfallAPIError) -> None:
    print(f"Error: {context}", file=sys.stderr)
    print(str(exc), file=sys.stderr)


def _validate_manifest_success(manifest, *, action: str) -> None:
    if manifest.cards:
        return
    print(f"Error: {action} failed — no cards were resolved.", file=sys.stderr)
    for err in manifest.errors:
        print(f"  {err}", file=sys.stderr)
    raise SystemExit(1)


def cmd_manifest(args: argparse.Namespace) -> None:
    out = Path(args.out).expanduser().resolve()
    try:
        manifest = run_plan(
            Path(args.decklist).expanduser(),
            out,
            opts=_selection_options(args),
            cache_dir=Path(args.cache_dir).expanduser() if args.cache_dir else Path("data/cache"),
        )
    except ScryfallAPIError as exc:
        _print_scryfall_error("manifest request failed", exc)
        raise SystemExit(1) from exc

    if manifest.errors and not manifest.cards:
        _validate_manifest_success(manifest, action="Manifest")
    print(f"Manifest written to {out / 'manifest.json'}")
    if manifest.errors:
        print(f"Warning: {len(manifest.errors)} card(s) could not be resolved.", file=sys.stderr)


def cmd_download(args: argparse.Namespace) -> None:
    out = Path(args.out).expanduser().resolve()
    try:
        manifest = run_download(
            Path(args.decklist).expanduser(),
            out,
            opts=_selection_options(args),
            cache_dir=Path(args.cache_dir).expanduser() if args.cache_dir else Path("data/cache"),
            build_pdf=not args.no_pdf,
            pdf_name=args.pdf or "proxies.pdf",
            paper=args.paper,
            dpi=args.dpi,
            force=args.force,
        )
    except ScryfallAPIError as exc:
        _print_scryfall_error("download request failed", exc)
        raise SystemExit(1) from exc

    if not manifest.cards:
        _validate_manifest_success(manifest, action="Download")

    images_ok = sum(1 for c in manifest.cards if c.chosen_printing.image_paths)
    if images_ok == 0 and not args.no_pdf:
        print("Error: Download failed — no card images were saved.", file=sys.stderr)
        for err in manifest.errors:
            print(f"  {err}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Download complete: {out} ({len(manifest.cards)} card(s), {images_ok} image(s))")
    if manifest.errors:
        print(f"Warning: {len(manifest.errors)} card(s) could not be resolved.", file=sys.stderr)


def cmd_sheets(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest).expanduser().resolve()
    out_pdf = Path(args.out).expanduser().resolve()
    run_sheets_from_manifest(manifest_path, out_pdf, paper=args.paper, dpi=args.dpi)
    print(f"PDF written to {out_pdf}")


def cmd_explain(args: argparse.Namespace) -> None:
    from card_downloader.scryfall.client import ScryfallClient
    from card_downloader.selection.optimizer import build_pools

    opts = _selection_options(args)
    client = ScryfallClient(cache_dir=Path(args.cache_dir or "data/cache"))
    name = args.card
    try:
        printings = client.search_printings(name)
        ub_ids = client.search_universes_beyond_ids(name)
    except ScryfallAPIError as exc:
        _print_scryfall_error(f'could not fetch printings for "{name}"', exc)
        raise SystemExit(1) from exc

    pools = build_pools({name: printings}, {name: ub_ids}, opts)
    candidates = pools.get(name, [])
    if not candidates:
        print(f'No usable printings found for "{name}".', file=sys.stderr)
        raise SystemExit(1)

    top = sorted(candidates, key=lambda c: c.score, reverse=True)[: args.top]
    print(f"Top {len(top)} printings for {name!r}:\n")
    for i, c in enumerate(top, 1):
        p = c.printing
        print(f"{i}. [{p.set_code}] {p.set_name} #{p.collector_number} score={c.score:.1f}")
        print(f"   {p.scryfall_uri}")
        print(f"   breakdown: {c.breakdown}")


def cmd_cache(args: argparse.Namespace) -> None:
    cache_dir = Path(args.cache_dir or "data/cache").expanduser()
    if args.action == "clear":
        import shutil

        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        print(f"Cleared {cache_dir}")
    else:
        count = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
        print(f"Cache entries: {count} in {cache_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="card-downloader")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--allow-ub", action="store_true")
    parser.add_argument("--allow-white-border", action="store_true")
    parser.add_argument("--allow-promo", action="store_true")
    parser.add_argument("--cache-dir", default="data/cache")
    sub = parser.add_subparsers(dest="command", required=True)

    p_manifest = sub.add_parser("manifest", help="Resolve printings and write manifest")
    p_manifest.add_argument("decklist")
    p_manifest.add_argument("--out", required=True)
    p_manifest.add_argument("--size", default="png")
    p_manifest.set_defaults(func=cmd_manifest)

    p_dl = sub.add_parser("download", help="Full pipeline: manifest + images + PDF")
    p_dl.add_argument("decklist")
    p_dl.add_argument("--out", required=True)
    p_dl.add_argument("--size", default="png")
    p_dl.add_argument("--no-pdf", action="store_true")
    p_dl.add_argument("--pdf", default="proxies.pdf")
    p_dl.add_argument("--paper", choices=["a4", "letter"], default="a4")
    p_dl.add_argument("--dpi", type=int, default=300)
    p_dl.add_argument("--force", action="store_true")
    p_dl.set_defaults(func=cmd_download)

    p_sheets = sub.add_parser("sheets", help="Rebuild PDF from manifest")
    p_sheets.add_argument("manifest", help="Path to manifest.json")
    p_sheets.add_argument("--out", required=True)
    p_sheets.add_argument("--paper", choices=["a4", "letter"], default="a4")
    p_sheets.add_argument("--dpi", type=int, default=300)
    p_sheets.set_defaults(func=cmd_sheets)

    p_explain = sub.add_parser("explain", help="Show top printings for one card")
    p_explain.add_argument("card")
    p_explain.add_argument("--top", type=int, default=5)
    p_explain.add_argument("--size", default="png")
    p_explain.set_defaults(func=cmd_explain)

    p_cache = sub.add_parser("cache", help="Manage Scryfall cache")
    p_cache.add_argument("action", choices=["clear", "stats"])
    p_cache.set_defaults(func=cmd_cache)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

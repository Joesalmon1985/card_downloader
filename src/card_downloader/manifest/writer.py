from pathlib import Path

from card_downloader.manifest.schema import Manifest


def write_manifest(manifest: Manifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest.save_json(path)


def write_selection_report(manifest: Manifest, path: Path) -> None:
    lines = [
        "# Selection Report",
        "",
        f"**Decklist:** `{manifest.decklist_path}`",
        f"**Generated:** {manifest.generated_at}",
        "",
        "## Anchor",
        "",
        f"- Set: `{manifest.selection_summary.anchor_set}`",
        f"- Coverage: {manifest.selection_summary.coverage:.0%}",
        f"- In anchor: {manifest.selection_summary.cards_in_anchor}",
        f"- Outliers: {manifest.selection_summary.outliers}",
        f"- Total score: {manifest.selection_summary.total_score:.1f}",
        "",
        "## Outliers",
        "",
    ]
    outliers = [c for c in manifest.cards if c.was_outlier]
    if outliers:
        for c in outliers:
            lines.append(f"- **{c.deck_name}** → `{c.chosen_printing.set}` ({', '.join(c.fallback_reasons) or 'none'})")
    else:
        lines.append("- None")

    lines.extend(["", "## Fallbacks", ""])
    with_fallbacks = [c for c in manifest.cards if c.fallback_reasons]
    if with_fallbacks:
        for c in with_fallbacks:
            lines.append(f"- **{c.deck_name}**: {', '.join(c.fallback_reasons)}")
    else:
        lines.append("- None")

    if manifest.outputs.pdf_path:
        lines.extend([
            "",
            "## PDF",
            "",
            f"- Path: `{manifest.outputs.pdf_path}`",
            f"- Pages: {manifest.outputs.pdf_pages}",
            f"- Cards placed: {manifest.outputs.pdf_cards_placed}",
        ])

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

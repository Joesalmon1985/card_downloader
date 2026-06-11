from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass
class ChosenPrintingRecord:
    id: str
    set: str
    collector_number: str
    lang: str
    border_color: str
    scryfall_uri: str
    image_url: str
    image_paths: list[str] = field(default_factory=list)


@dataclass
class CardManifestRow:
    deck_name: str
    quantity: int
    oracle_id: str
    chosen_printing: ChosenPrintingRecord
    score: float
    score_breakdown: dict[str, float]
    fallback_reasons: list[str]
    was_outlier: bool


@dataclass
class SelectionSummary:
    anchor_set: str
    coverage: float
    cards_in_anchor: int
    outliers: int
    total_score: float


@dataclass
class PdfOptions:
    paper: str = "a4"
    dpi: int = 300
    gap_mm: float = 1.0


@dataclass
class OutputSummary:
    images_dir: str = "images/"
    pdf_path: str = "proxies.pdf"
    pdf_pages: int = 0
    pdf_cards_placed: int = 0
    pdf_options: PdfOptions = field(default_factory=PdfOptions)


@dataclass
class Manifest:
    version: int
    decklist_path: str
    generated_at: str
    options: dict[str, Any]
    selection_summary: SelectionSummary
    cards: list[CardManifestRow]
    errors: list[str] = field(default_factory=list)
    outputs: OutputSummary = field(default_factory=OutputSummary)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["outputs"]["pdf_options"] = asdict(self.outputs.pdf_options)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Manifest":
        pdf_opts = data.get("outputs", {}).get("pdf_options", {})
        outputs = data.get("outputs", {})
        return cls(
            version=data["version"],
            decklist_path=data["decklist_path"],
            generated_at=data["generated_at"],
            options=data.get("options", {}),
            selection_summary=SelectionSummary(**data["selection_summary"]),
            cards=[
                CardManifestRow(
                    deck_name=c["deck_name"],
                    quantity=c["quantity"],
                    oracle_id=c["oracle_id"],
                    chosen_printing=ChosenPrintingRecord(**c["chosen_printing"]),
                    score=c["score"],
                    score_breakdown=c["score_breakdown"],
                    fallback_reasons=c["fallback_reasons"],
                    was_outlier=c["was_outlier"],
                )
                for c in data["cards"]
            ],
            errors=data.get("errors", []),
            outputs=OutputSummary(
                images_dir=outputs.get("images_dir", "images/"),
                pdf_path=outputs.get("pdf_path", "proxies.pdf"),
                pdf_pages=outputs.get("pdf_pages", 0),
                pdf_cards_placed=outputs.get("pdf_cards_placed", 0),
                pdf_options=PdfOptions(**pdf_opts) if pdf_opts else PdfOptions(),
            ),
        )

    def save_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, path: Path) -> "Manifest":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

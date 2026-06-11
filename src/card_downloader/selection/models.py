from dataclasses import dataclass, field


@dataclass(frozen=True)
class SelectionOptions:
    lang: str = "en"
    allow_ub: bool = False
    allow_white_border: bool = False
    allow_promo: bool = False
    image_size: str = "png"


@dataclass(frozen=True)
class Classification:
    border_tier: str  # good, bad, neutral
    nonfoil_available: bool
    is_universes_beyond: bool
    has_special_frame: bool
    is_promo: bool
    is_english: bool
    has_highres: bool
    has_png: bool


@dataclass(frozen=True)
class ScoreBreakdown:
    nonfoil: float = 0.0
    border: float = 0.0
    not_ub: float = 0.0
    frame: float = 0.0
    promo: float = 0.0
    english: float = 0.0
    image: float = 0.0
    paper: float = 0.0
    set_type: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.nonfoil
            + self.border
            + self.not_ub
            + self.frame
            + self.promo
            + self.english
            + self.image
            + self.paper
            + self.set_type
        )


@dataclass(frozen=True)
class ScoredCandidate:
    printing: object
    score: float
    breakdown: ScoreBreakdown
    classification: Classification


@dataclass(frozen=True)
class Anchor:
    set_code: str
    coverage: int


@dataclass(frozen=True)
class CardAssignment:
    deck_name: str
    quantity: int
    printing: object
    score: float
    breakdown: ScoreBreakdown
    fallback_reasons: tuple[str, ...]
    was_outlier: bool
    coherence_bonus: float = 0.0


@dataclass(frozen=True)
class Assignment:
    anchor_set: str
    assignments: tuple[CardAssignment, ...]
    total_score: float
    coverage: float
    cards_in_anchor: int
    outliers: int

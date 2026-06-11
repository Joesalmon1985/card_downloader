"""Default scoring weights from docs/selection-rules.md."""

COHERENCE_WEIGHT = 12.0
OUTLIER_PENALTY = 15.0
TOP_ANCHORS = 10

WEIGHTS = {
    "nonfoil": 8.0,
    "foil_only": -20.0,
    "border_black": 6.0,
    "border_white": -12.0,
    "border_borderless": -8.0,
    "not_ub": 6.0,
    "ub": -15.0,
    "frame_normal": 5.0,
    "showcase": -10.0,
    "extendedart": -10.0,
    "etched_frame": -8.0,
    "promo": -8.0,
    "not_promo": 4.0,
    "english": 10.0,
    "non_english": -25.0,
    "highres": 8.0,
    "lowres": -5.0,
    "png": 3.0,
    "paper": 3.0,
    "funny_set": -6.0,
    "variation": -5.0,
}

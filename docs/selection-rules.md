# Card Printing Selection Rules

This document describes how Card Downloader chooses which Scryfall printing to download for each card in a decklist. It is written in plain English for humans; the implementation lives in `card_downloader/selection/`.

---

## Overview

Given a decklist, the tool:

1. Parses and normalises card names.
2. Fetches **every available printing** of each unique card from Scryfall.
3. Removes printings that are unusable for proxy images (hard filters).
4. Scores each remaining printing against our preferences (soft scoring).
5. Picks a **primary set or set group** that maximises how many deck cards can come from the same place.
6. Assigns the best printing per card within that strategy, allowing outliers where necessary.
7. Records **why** any compromise was made in the manifest.

The key insight: we do **not** pick the best printing for each card independently. That would give every card its individually nicest printing but from dozens of different sets. Instead, we optimise for **deck-wide coherence** first, then quality.

---

## Step-by-step algorithm

### Step 1 — Parse the deck

Input lines like:

```
1 Sol Ring
11 Snow-Covered Mountain
1 Urza's Saga
```

Become structured entries: `(quantity=1, name="Sol Ring")`, etc. Names are normalised (curly apostrophes → straight, Unicode normalised, trimmed).

Sideboard sections (`[Sideboard]`) and `#` comments are ignored unless we add sideboard support later.

### Step 2 — Gather all printings

For each **unique** card name, query Scryfall:

```
!"Card Name" unique=prints
```

Paginate until all printings are collected. English only by default (`include_multilingual=false`).

Selection happens once per unique name. Quantities affect PDF layout later, not which printing is chosen.

### Step 3 — Hard filters (remove unusable printings)

A printing is **excluded entirely** if any of these apply:

| Rule | Why |
|------|-----|
| No downloadable image (`image_uris` missing, or `image_status == "missing"`) | Nothing to print |
| Digital-only (`digital: true`, or not available on paper) | Not a physical proxy |
| Wrong object type (token, emblem, art series, vanguard) | Not a deck card |
| Required face image missing (double-faced card without front URI) | Incomplete proxy |

Hard filters are not overridden by preferences. If every printing is filtered out, the card is recorded in `manifest.errors`.

### Step 4 — Soft scoring (grade each surviving printing)

Each printing receives a numeric score and a **breakdown** by category. Higher is better.

See [Proposed scoring model](#proposed-scoring-model) below.

### Step 5 — Find the best anchor set or group

An **anchor** is a Magic set code (e.g. `clu`) or a **set group** (e.g. `g:clu`, which includes related commander products).

For each candidate anchor:

1. Count how many deck cards have **at least one** scored printing in that anchor.
2. For cards in the anchor: pick the **highest-scoring printing within the anchor**.
3. For cards **not** in the anchor (outliers): pick the **highest-scoring printing globally**, minus an outlier penalty.

The winning anchor maximises:

```
total = (coherence_weight × cards_in_anchor)
      + sum(per_card_printing_scores)
      - (outlier_penalty × number_of_outliers)
```

Tie-breakers: higher mean image quality → fewer promos → more recent `released_at`.

### Step 6 — Explain fallbacks

For each chosen printing, compare against the “ideal” thresholds. If the chosen printing fails a preference that **could** have been satisfied by another printing (possibly in a different set), record a fallback reason.

If the preference was impossible for this card (e.g. Plateau has no black-border printing), record `white_border_unavoidable` instead of treating it as a mistake.

---

## Hard filters vs soft preferences

| Type | Effect | Examples |
|------|--------|----------|
| **Hard filter** | Printing removed from candidate pool | No image, digital-only, token layout |
| **Soft preference** | Adjusts score; best available wins | Black border, nonfoil, not UB, normal frame |

CLI flags like `--allow-ub` **disable soft penalties** for that category. They do not bypass hard filters.

---

## Proposed scoring model

Default weights (tunable in `selection/config.py`):

| Factor | Condition | Points |
|--------|-----------|--------|
| Nonfoil available | `"nonfoil" in finishes` | +8 |
| Foil-only printing | `"nonfoil" not in finishes` | −20 |
| Black border | `border_color == "black"` | +6 |
| White border | `border_color == "white"` | −12 |
| Borderless | `border_color == "borderless"` | −8 |
| Not Universes Beyond | not in UB id set | +6 |
| Universes Beyond | in UB id set | −15 |
| Normal frame | no penalised `frame_effects`; not `full_art` | +5 |
| Showcase | `"showcase" in frame_effects` | −10 |
| Extended art | `"extendedart" in frame_effects` | −10 |
| Etched frame effect | `"etched" in frame_effects` | −8 |
| Promo | `promo == true` | −8 |
| Non-promo | `promo == false` | +4 |
| English | `lang == "en"` | +10 |
| Non-English | other | −25 (unless `--lang` set) |
| High-res image | `highres_image` or `image_status == "highres_scan"` | +8 |
| Low-res only | `image_status == "lowres"` | −5 |
| PNG available | `"png" in image_uris` | +3 |
| Paper game | `"paper" in games` | +3 |
| Funny/memorabilia set | `set_type in ("funny", "memorabilia")` | −6 |
| Variation / alt art | `variation == true` | −5 |

**Coherence bonus** (applied at assignment level, not per printing): `+coherence_weight` per card matched to anchor set.

**Outlier penalty:** −15 per card that could not use the anchor set.

---

## How same-set optimisation works

### Why it matters

Proxy decks look cohesive when most cards share a set symbol and frame era. A Commander deck where 70 cards are from `CLU` and 24 are outliers looks intentional; a deck with 94 different set symbols does not.

### Anchor discovery

1. Collect all set codes appearing in any candidate pool.
2. Rank sets by **coverage**: how many unique deck card names have a printing in that set.
3. Also consider **set groups** (`g:{code}`) for products tied to the same release (main set + commander decks).
4. Evaluate the top M anchors (e.g. M = 10) with the full assignment algorithm.

### Outliers are expected

Cards like `Plateau`, `Wheel of Fortune`, or `Urza's Saga` may not exist in a modern commander precon set. The optimizer assigns them the best global printing and marks `was_outlier: true` in the manifest.

### Example coverage table (imaginary 5-card deck)

| Card | In set `ABC`? | In set `XYZ`? |
|------|---------------|---------------|
| Sol Ring | yes | yes |
| Command Tower | yes | yes |
| Plateau | no | no |
| Lightning Bolt | yes | no |
| Counterspell | no | yes |

- Anchor `ABC`: coverage 3/5 (Sol Ring, Command Tower, Lightning Bolt)
- Anchor `XYZ`: coverage 3/5 (Sol Ring, Command Tower, Counterspell)

The optimizer scores both fully (including outlier handling for Plateau) and picks the higher total. If tied, tie-breakers apply.

---

## How fallback decisions are explained

Each manifest card entry may include `fallback_reasons: []` — a list of human-readable strings.

| Reason code | Meaning |
|-------------|---------|
| `foil_only_printing` | No nonfoil finish available; chose foil-only SKU |
| `universes_beyond_only` | All reasonable printings are UB; none avoided |
| `white_border_unavoidable` | Card has no black-border printing (e.g. Revised dual) |
| `no_english_printing` | No English printing with acceptable image |
| `lowres_only` | Best available image is low resolution |
| `special_frame_required` | Only special-frame printings had images / passed filters |
| `promo_only_option` | Non-promo printings excluded or unavailable |
| `outlier_from_anchor:{set}` | Card not in anchor set; best global printing used |
| `digital_excluded_alternatives` | Better-looking options were digital-only and filtered |

Reasons are **explanatory**, not errors. The tool still downloads the best available proxy.

---

## Worked examples (imaginary candidates)

### Example A — Sol Ring in anchor set `CLU`

Candidates (simplified):

| ID | Set | Border | UB | Frame | Nonfoil | Lang | Hi-res | Score |
|----|-----|--------|----|-------|---------|------|--------|-------|
| A | clu | black | no | normal | yes | en | yes | **high** |
| B | c14 | black | no | normal | yes | en | yes | high |
| C | pf19 | black | no | promo | yes | en | yes | medium |

Deck anchor is `CLU` with 68/94 coverage. **Chosen: A** — in anchor, highest score, no fallback reasons.

---

### Example B — Plateau (white border unavoidable)

All printings have `border_color: white` (Limited Edition Alpha/Beta/Unlimited/Revised).

| ID | Set | Border | Score note |
|----|-----|--------|------------|
| X | leb | white | −12 border, but only option |
| Y | 2ed | white | same |

**Chosen: X** (oldest high-res scan, or highest overall). Fallback: `["white_border_unavoidable"]`. Not marked as an optimizer mistake — no black-border printing exists.

---

### Example C — Urza's Saga (frame treatment)

| ID | Set | Frame effects | Score |
|----|-----|---------------|-------|
| P | mh2 | normal | +5 frame |
| Q | mh2 | showcase | −10 frame |
| R | bro | normal | +5 frame |

If anchor set is `MH2` and both P and Q are in `mh2`: **Chosen: P** (normal frame). If only Q were in anchor: **Chosen: Q** with `["special_frame_required"]` if P exists only as outlier with lower total assignment score.

---

### Example D — Peter Parker's Camera (UB-only)

Suppose all printings are tagged Universes Beyond:

| ID | Set | UB | Score |
|----|-----|----|-------|
| U1 | spm | yes | −15 UB penalty |
| U2 | spm | yes | −15 (foil-only: −20 more) |

**Chosen: U1** (nonfoil if available). Fallback: `["universes_beyond_only"]`.

---

### Example E — Snow-Covered Mountain ×11

One printing selected (e.g. normal frame, black border, from anchor set). Manifest:

```json
{
  "deck_name": "Snow-Covered Mountain",
  "quantity": 11,
  "chosen_printing": { "set": "clu", "...": "..." },
  "fallback_reasons": []
}
```

PDF step places **11 slots** with the same PNG. Selection runs once.

---

### Example F — Outlier from anchor

Deck anchor: `CLU`. `Wheel of Fortune` has no `clu` printing.

Best global candidate: `2ed` printing, white border, high-res.

```json
{
  "deck_name": "Wheel of Fortune",
  "was_outlier": true,
  "fallback_reasons": ["outlier_from_anchor:clu", "white_border_unavoidable"]
}
```

---

## Relationship to Scryfall search syntax

Selection scoring uses **card object fields** from API responses. Search syntax (`is:nonfoil`, `not:universesbeyond`, etc.) is used for:

- Fetching printings (`!"name" unique=prints`)
- UB id tagging (`!"name" is:universesbeyond unique=prints`)
- Optional validation in `explain` command

We deliberately **do not** pre-filter all preferences in search queries, because over-filtering causes empty results and hides valid fallbacks.

---

## Future improvements (not v1)

- User-supplied banlist/allowlist of set codes
- `--prefer-set` soft bias toward a specific set
- Include card backs on PDF (`--include-backs`)
- Sideboard parsing and separate selection policy
- Cached UB set list from bulk data instead of per-card UB queries

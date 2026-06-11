# Card Downloader — Project Plan

A Python command-line tool that takes a Magic: The Gathering decklist, resolves card printings via Scryfall, downloads selected images, assembles printer-ready 3×3 PDF proxy sheets, and emits an auditable manifest explaining every choice.

---

## 1. Summary of Existing Files

The repository is **early-stage**: scaffolding directories exist, but only `old_Python/` contains working code.

| Path | Status | Purpose |
|------|--------|---------|
| [`README.md`](../README.md) | Active | High-level goals and intended layout (`src/`, `data/`, `tests/`, `docs/`) |
| [`requirements.txt`](../requirements.txt) | Empty placeholder | No pinned dependencies yet |
| [`.env.example`](../.env.example) | Empty placeholder | No environment variables defined |
| [`src/main.py`](../src/main.py) | Empty placeholder | Intended future entry point |
| [`tests/`](../tests/) | Empty directory | No tests yet |
| [`docs/project-notes.md`](project-notes.md) | Empty placeholder | Superseded by this plan |
| [`data/.gitkeep`](../data/.gitkeep) | Placeholder | Output directory; `.gitignore` ignores `data/*` except this file |
| [`.gitignore`](../.gitignore) | Active | Ignores venv, `.env`, and local outputs under `data/` |

### Legacy scripts (`old_Python/`)

#### `download_scryfall_images backup.py`

Downloads the **default (newest named)** printing for each line in a text file.

- **API:** `GET https://api.scryfall.com/cards/named?exact={name}`
- **Output:** One image per card; `_front` / `_back` suffixes for double-faced cards
- **Rate limit:** 0.12 s sleep between cards (~10 req/s courtesy limit)
- **Image sizes:** `png`, `large`, `normal`, `small`, `art_crop`, `border_crop`
- **Reusable patterns:** `safe_filename`, streamed download, per-card error isolation

**Limitation:** Reads each line as a raw card name. Does not parse `1 Card Name` quantity prefixes.

#### `download_oldest_printings.py`

Downloads the **earliest** printing of each card.

- **API:** `GET /cards/search?q=!"{name}"&unique=prints&order=released&dir=asc` — takes first result
- Same image handling and helpers as above

#### `make_proxy_sheets.py`

Post-processing step — **no Scryfall usage**. Lays out a folder of images into printable PDF proxy sheets.

| Setting | Value |
|---------|-------|
| Grid | 3 columns × 3 rows (9 cards per page) |
| Card size | 2.5″ × 3.5″ |
| Gap | 1 mm |
| Background | Black (alpha flattened onto black) |
| Paper | A4 default; letter optional |
| DPI | 300 |
| Libraries | Pillow, img2pdf |

**Limitation:** Sorts images alphabetically; one file per folder entry (no quantity expansion, no deck order).

#### `decklist.txt`

Sample **94-line Commander deck** in `quantity name` format (e.g. `11 Snow-Covered Mountain`). Lines 87–90 use **curly apostrophes** (`Urza's Saga`, `Magewright's Stone`). Includes old-border staples (Plateau, Wheel of Fortune) and externally licensed cards (LotR/Marvel-adjacent names).

### Key gaps

- No decklist parser (quantity prefix breaks Scryfall lookups)
- No intelligent printing selection
- No manifest or audit trail
- No unified CLI; duplicated helpers across scripts
- PDF step is manual and disconnected from download/selection

---

## 2. Proposed Target Architecture

### Package layout

Source lives under `src/card_downloader/`. Tests mirror this layout under `tests/`.

```
src/card_downloader/
  decklist/
    models.py          # DeckEntry, ParsedDeck (frozen dataclasses)
    normalize.py       # pure: normalize_name(str) -> str
    parser.py          # pure: parse_line, parse_decklist(text) -> ParsedDeck
  scryfall/
    models.py          # CardPrinting from API JSON
    protocols.py       # HttpClient, CacheStore protocols
    rate_limit.py      # injectable RateLimiter
    pagination.py      # pure: merge paginated List responses
    cache.py           # FileCache implements CacheStore
    client.py          # ScryfallClient: search_printings(name) -> list[CardPrinting]
  selection/
    models.py          # Candidate, ScoreBreakdown, Anchor, Assignment, SelectionOptions
    filters.py         # pure: hard_exclude(card, opts) -> bool
    classify.py        # pure: border/frame/finish/UB classification
    scoring.py         # pure: score_printing(candidate, opts) -> ScoreBreakdown
    anchors.py         # pure: rank_anchors(pools) -> list[Anchor]
    optimizer.py       # pure: best_assignment(pools, anchors, opts) -> Assignment
    fallback.py        # pure: fallback_reasons(chosen, opts) -> list[str]
    config.py          # default weights / SelectionOptions
  download/
    filenames.py       # pure: safe_filename, image_filename(printing)
    images.py          # ImageDownloader (uses HttpClient)
  manifest/
    schema.py          # Manifest dataclasses + JSON serialisation
    writer.py          # manifest.json + selection-report.md
    reader.py          # load manifest for resume / sheets rebuild
  sheets/
    constants.py       # CARD_W_IN, GAP_MM, COLS, ROWS, etc.
    geometry.py        # pure: page_count, slot_coords, grid_fits_paper
    slots.py           # pure: expand_to_slots(deck, manifest) -> list[Slot]
    image_prep.py      # flatten_on_black, resize (PIL)
    builder.py         # build_pdf(slots, paths, opts) -> Path
  pipeline/
    plan.py            # orchestration: fetch → filter → score → optimize → manifest
    download.py        # orchestration: manifest → images → PDF
  cli/
    main.py            # argparse root
    commands/          # plan, download, explain, sheets, cache (thin wrappers)
```

### Dependency direction

```
cli → pipeline → {decklist, scryfall, selection, manifest, download, sheets}
selection → scryfall (models only)
download, sheets → manifest
sheets → decklist
```

No circular imports. Business logic never imports from `cli/` or `pipeline/`.

### Data flow

```
decklist.txt
  → parse + normalize
  → fetch all printings per unique name (Scryfall, paginated, cached)
  → hard-filter candidates
  → classify + soft-score each printing
  → global optimizer (anchor set/group)
  → manifest.json + selection-report.md
  → download PNGs
  → expand quantities → 3×3 PDF (black background)
```

### Run directory layout

```
data/runs/{timestamp}/
  manifest.json
  selection-report.md
  images/           # one PNG per unique printing
  proxies.pdf       # printer-ready 3×3 sheets
```

### Design principles

- **Test-first (TDD)** is the default: failing tests before implementation.
- **Pure logic separated from I/O** — scoring, parsing, geometry are pure functions.
- **Scryfall behind protocols** — `HttpClient`, `CacheStore` injected in tests.
- **No live Scryfall in CI** — fixture JSON + HTTP mocking (`responses`).
- **Manifests central** — every run is reproducible and explainable.
- **CLI and pipeline last** — wired only after modules have unit tests.
- **PDF is core output** — `download` produces `proxies.pdf` by default (not a manual post-step).

---

## 3. Proposed CLI Commands

Entry point: `card-downloader` (via `[project.scripts]` in `pyproject.toml`).

| Command | Purpose |
|---------|---------|
| `plan DECKLIST [-o MANIFEST] [--lang en] [--anchor SET]` | Resolve printings and write manifest **without** downloading images |
| `download DECKLIST -o DIR [--size png] [--pdf PATH] [--paper a4] [--dpi 300] [--no-pdf]` | Full pipeline: plan → download images → build 3×3 PDF |
| `explain "Card Name" [--deck DECKLIST]` | Debug one card: top N candidates with score breakdown |
| `sheets [--manifest PATH \| IMAGE_DIR] -o out.pdf [--paper a4] [--dpi 300]` | Re-build PDF from existing manifest or image folder |
| `cache clear\|stats` | Manage local Scryfall response cache |

**Global flags:** `--verbose`, `--no-cache`, `--max-outliers N`, `--prefer-set SET`, `--lang LANG`, `--allow-ub`, `--allow-white-border`, `--allow-promo`, `--force`.

Default image size: **`png`** (745×1040, print-suitable per Scryfall).

---

## 4. Scryfall Metadata / API Feasibility Analysis

Scryfall does not expose a single “proxy quality score.” Selection must combine **card object fields**, **search syntax**, and **documented limitations**. The table below maps each project requirement to what is realistically available.

### Requirement → Scryfall support

| Requirement | Primary source | Search syntax (validation) | Notes / limitations |
|-------------|----------------|---------------------------|---------------------|
| **All printings of a named card** | `GET /cards/search?q=!"{name}"&unique=prints` | `!"Exact Name"` | Paginated (175/page); rate limit 2 req/s. Use `include_multilingual=false` by default. |
| **Set code** | `set` (string, 3–6 letters) | `e:{code}` or `s:{code}` | Authoritative per printing. |
| **Set type** | `set_type` on card object | `st:commander`, `st:core`, `st:promo`, etc. | Values include `expansion`, `commander`, `masters`, `funny`, `promo`, `token`, … See [Set types docs](https://scryfall.com/docs/api/sets). |
| **Collector number** | `collector_number` (string) | `cn:{n} s:{code}` | Needed for disambiguation and manifest audit. |
| **Language** | `lang` (ISO code, e.g. `en`, `ja`) | `lang:en` | Default API search omits other languages unless `include_multilingual=true`. |
| **Image URIs** | `image_uris` (single-face) or `card_faces[].image_uris` (multi-face) | — | Keys: `png`, `large`, `normal`, `small`, `art_crop`, `border_crop`. PNG ≈ 745×1040. |
| **Border colour** | `border_color` | `border:black`, `border:white`, `border:borderless` | Values: `black`, `white`, `borderless`, `silver`, `gold`, `yellow`. |
| **Foil / nonfoil availability** | `finishes` array | `is:nonfoil`, `is:foil`, `is:etched` | Values: `"foil"`, `"nonfoil"`, `"etched"`. Indicates **product finishes**, not whether the scan looks holographic. Scryfall PNGs are non-shiny. Set object also has `foil_only` / `nonfoil_only`. |
| **Promo / special status** | `promo` (bool), `promo_types` (array) | `is:promo`, `is:prerelease`, `is:set_promo`, … | `promo_types` is open-ended; treat `promo: true` as primary signal. |
| **Frame edition** | `frame` | `frame:2015`, `frame:1993`, … | Values: `1993`, `1997`, `2003`, `2015`, `future`. |
| **Frame effects / special treatments** | `frame_effects` array, `full_art` bool | `is:default`, `is:atypical`, `frame:showcase`, … | Penalize: `showcase`, `extendedart`, `inverted`, `etched` (in frame_effects). Allow: `legendary`, `snow`, DFC transform marks when unavoidable. |
| **Variation status** | `variation` (bool), `variation_of` (UUID) | — | Identifies alt-art variants within a set; usually penalize for “normal” proxies. |
| **Image quality** | `highres_image` (bool), `image_status` | `is:hires` | `image_status`: `missing`, `placeholder`, `lowres`, `highres_scan`. Hard-exclude `missing`. |
| **Paper vs digital** | `digital` (bool), `games` array | `game:paper`, `is:digital` | Hard-exclude digital-only where possible. |
| **Universes Beyond / licensed** | **No direct card field** | `is:universesbeyond`, `not:universesbeyond` | Search operators only. v1: auxiliary query per card `!"name" is:universesbeyond unique=prints` → cache `scryfall_id` set; tag candidates by membership. |
| **Coherent set groups** | Set relationships via search | `g:{code}` | Groups parent/sibling/child sets (main set + commander precons). Useful for anchor selection. |
| **Set metadata enrichment** | `GET` set object via `set_uri` | — | `parent_set_code`, `digital`, `foil_only`, `nonfoil_only`. |

### Recommended fetch strategy (v1)

1. **Primary query per card:** `!"{normalized_name}" unique=prints include_multilingual=false` — paginate all results.
2. **UB tagging query (cached):** `!"{name}" is:universesbeyond unique=prints` — collect IDs into a lookup set.
3. **Classify and score in Python** using card object fields — do not over-filter in search (risk of empty result sets).
4. **Cache** all raw JSON responses under `data/cache/` keyed by query hash.

### What will not be perfect in v1

- **UB detection** relies on search operator + ID tagging, not a boolean on the card object.
- **“Nonfoil appearance”** — we score on `finishes` availability; image files are standard scans.
- **White border** — some cards (e.g. Plateau) may require white-border printings; soft penalty only.
- **Default frame** — inferred from `frame_effects` emptiness / allowlist, not a single API boolean (search `is:default` is for queries, not returned on objects).
- **Same-set coverage** — not every card exists in every set; optimizer must allow outliers with documented reasons.

---

## 5. Staged TDD Roadmap

See [`docs/tdd-roadmap.md`](tdd-roadmap.md) for the full stage-by-stage breakdown with test files, definition of done, and red-green-refactor cycle per module.

Summary:

| Stage | Focus |
|-------|-------|
| 0 | Scaffolding: `pyproject.toml`, pytest, empty module tree, fixtures layout |
| 1 | Decklist: `normalize`, `parser`, `models` |
| 2 | Scryfall: `pagination`, `cache`, `client` (mocked HTTP) |
| 3 | Selection: `filters`, `classify` |
| 4 | Selection: `scoring`, `anchors`, `optimizer`, `fallback`; manifest `schema` |
| 5 | Download: `filenames`, `images` |
| 6 | Sheets: `geometry`, `slots`, `image_prep`, `builder` |
| 7 | Pipeline + CLI (thin wiring), integration tests |

**Rule:** Each stage completes tests + implementation before the next begins. CLI is Stage 7 only.

---

## 6. Testing Strategy

### Methodology

Every module follows: **write failing tests → red → implement minimal code → green → refactor**.

### Test pyramid

| Layer | Location | Scope |
|-------|----------|-------|
| Unit | `tests/unit/` | Pure functions, dataclass serialisation, single-module behaviour |
| Integration | `tests/integration/` | Mocked HTTP, pipeline slices, PDF builder with fixture images |
| Manual | Stage 7 | Full 94-card deck; optional physical print size check |

### Tooling

- **`pytest`** — test runner (`testpaths = ["tests"]` in `pyproject.toml`)
- **`pytest-cov`** — optional coverage gate on `decklist/` and `selection/`
- **`responses`** — mock `requests` for Scryfall client tests
- **Fixtures** — `tests/fixtures/cards/`, `tests/fixtures/scryfall/`, `tests/fixtures/decklists/`, `tests/fixtures/images/`

### Conventions

- One test module per source module.
- No network in CI.
- Card JSON fixtures trimmed from real Scryfall responses.
- Golden manifest snapshots for integration tests (small decks only).

### Key test cases (inventory)

- Curly apostrophe normalisation (decklist lines 87–90)
- Parse `11 Snow-Covered Mountain`; skip `[Sideboard]` and `#` comments
- Hard-exclude digital-only, missing images, token layouts
- Score Plateau: white-border penalty but not excluded
- Optimizer: 3/5 coverage anchor beats independent per-card best
- PDF slots: 11× basic + 83 singletons → 106 slots, 12 pages
- Geometry: grid fits A4 at 300 DPI

---

## 7. Manifest / Output Design

### `manifest.json`

```json
{
  "version": 1,
  "decklist_path": "data/decklists/example-commander.txt",
  "generated_at": "2026-06-11T12:00:00Z",
  "options": {
    "lang": "en",
    "image_size": "png",
    "allow_ub": false,
    "allow_white_border": false
  },
  "selection_summary": {
    "anchor_set": "clu",
    "anchor_group": "g:clu",
    "coverage": 0.72,
    "cards_in_anchor": 68,
    "outliers": 26,
    "total_score": 1842.5,
    "runner_up_anchors": ["c21", "dmr"]
  },
  "cards": [
    {
      "deck_name": "Sol Ring",
      "quantity": 1,
      "oracle_id": "uuid",
      "chosen_printing": {
        "id": "uuid",
        "set": "clu",
        "collector_number": "123",
        "lang": "en",
        "border_color": "black",
        "scryfall_uri": "https://scryfall.com/card/...",
        "image_paths": ["images/Sol_Ring__clu_123.png"]
      },
      "score": 41.0,
      "score_breakdown": {
        "nonfoil": 8,
        "border": 6,
        "not_ub": 6,
        "frame": 5,
        "english": 10,
        "image": 8,
        "coherence_bonus": 12
      },
      "fallback_reasons": [],
      "was_outlier": false
    }
  ],
  "errors": [],
  "outputs": {
    "images_dir": "images/",
    "pdf_path": "proxies.pdf",
    "pdf_pages": 12,
    "pdf_cards_placed": 106,
    "pdf_options": { "paper": "a4", "dpi": 300, "gap_mm": 1.0 }
  }
}
```

### `selection-report.md`

Human-readable companion: anchor choice rationale, outlier list, cards with unavoidable compromises (white border, UB-only, foil-only, lowres), Scryfall links, PDF summary.

### Image naming

`{safe_name}__{set}_{collector_number}.png` — DFC playable face only on v1 PDF (`__front` / `__back` stored if downloaded).

### PDF behaviour (vs legacy script)

- **Deck order** preserved (legacy sorted alphabetically).
- **Quantities expanded** — `11 Snow-Covered Mountain` → 11 grid slots, same PNG reused.
- **Partial last page** — empty slots remain black.
- **Card backs excluded** from v1 PDF (front/playable face only).

---

## 8. Risks and Edge Cases

| Risk | Handling |
|------|----------|
| Card name not found | Normalise name → fuzzy `/cards/named?fuzzy=` → record in `errors[]` |
| Quantity prefix breaks lookup | Parser strips quantity before any Scryfall call |
| Curly/smart quotes | `normalize.py` maps to ASCII apostrophe before lookup |
| Only UB / foil / white-border printings exist | Pick best available; record all failed preferences in `fallback_reasons` |
| DFC / split / adventure layouts | Require playable face image; store both faces if downloaded |
| Basic lands at ×11 | Select printing once; manifest `quantity: 11`; PDF expands slots |
| Scryfall rate limits | Cache responses; 500 ms between search calls; resumable download |
| Empty search (API strictness) | Retry with relaxed query; never auto-`include:extras` silently without logging |
| Ambiguous card name | Lock `oracle_id` from first successful match; warn on subsequent ambiguity |
| Large candidate pools (basic lands) | Score in Python; optional early anchor pruning for performance |
| Reproducibility | Manifest stores `id`, `set`, `collector_number`, `scryfall_uri`, scores, options |

---

## 9. Definition of Done (per stage)

### Stage 0 — Scaffolding

- [ ] `pyproject.toml` with package metadata, runtime + dev deps, pytest config, console script entry
- [ ] Empty `src/card_downloader/` module tree matching architecture above
- [ ] Mirrored `tests/unit/` and `tests/integration/` directories
- [ ] `tests/conftest.py` with fixture path helpers
- [ ] `data/decklists/example-commander.txt` copied from `old_Python/decklist.txt`
- [ ] `.gitignore` covers cache, runs, PDFs, images (verify)
- [ ] `pytest` runs successfully (smoke test or zero tests)

### Stage 1 — Decklist

- [ ] `tests/unit/decklist/test_normalize.py` — all green
- [ ] `tests/unit/decklist/test_parser.py` — all green
- [ ] `normalize.py`, `parser.py`, `models.py` implemented
- [ ] Parses full example decklist: 94 entries, correct quantities, normalised apostrophes

### Stage 2 — Scryfall

- [ ] Unit tests for pagination and cache — green
- [ ] Integration test for client with mocked HTTP — green
- [ ] No live network required for `pytest`

### Stage 3 — Filtering & classification

- [ ] `test_filters.py`, `test_classify.py` — green
- [ ] Hard exclusions and UB/border/frame tagging work on fixture cards

### Stage 4 — Scoring, optimizer, manifest

- [ ] `test_scoring.py`, `test_anchors.py`, `test_optimizer.py`, `test_fallback.py`, `test_schema.py` — green
- [ ] Synthetic deck produces stable manifest JSON round-trip

### Stage 5 — Download

- [ ] `test_filenames.py` — green
- [ ] Integration test downloads mock bytes to disk with correct names

### Stage 6 — PDF sheets

- [ ] `test_geometry.py`, `test_slots.py`, `test_image_prep.py` — green
- [ ] Integration test produces valid PDF with expected page count
- [ ] Layout matches legacy script dimensions (2.5″×3.5″, 3×3, 1 mm gap, black bg, 300 DPI, A4)

### Stage 7 — Pipeline & CLI

- [ ] `integration/test_pipeline_with_fixtures.py` — green
- [ ] `plan` and `download` commands work end-to-end with fixtures
- [ ] README documents usage
- [ ] Manual smoke test on example decklist (optional live Scryfall)

---

## 10. Minimal Scaffolding Recommendations (Stage 0)

When executing Stage 0, create:

**`pyproject.toml`** — package name `card-downloader`, Python ≥3.11, `[project.scripts] card-downloader = "card_downloader.cli.main:main"`, dependencies `requests`, `Pillow`, `img2pdf`; optional dev group with `pytest`, `pytest-cov`, `responses`.

**Directory placeholders** — `__init__.py` in each package; no business logic yet.

**`tests/conftest.py`** — `FIXTURES = Path(__file__).parent / "fixtures"` helper.

**Do not create yet:** Scryfall client, scorer, or CLI commands — those are Stage 1+.

Legacy scripts in `old_Python/` remain untouched until Stage 7 validates replacement behaviour.

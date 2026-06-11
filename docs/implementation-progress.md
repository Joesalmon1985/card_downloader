# Implementation Progress

## Status: Complete (Stages 0–7)

| Stage | Status | Commit message |
|-------|--------|----------------|
| 0 | done | Stage 0 scaffold project |
| 1 | done | Stage 1 implement decklist parsing |
| 2 | done | Stage 2 implement Scryfall client |
| 3 | done | Stage 3 implement candidate classification |
| 4 | done | Stage 4 implement printing optimiser and manifest schema |
| 5 | done | Stage 5 implement image downloading |
| 6 | done | Stage 6 implement proxy PDF builder |
| 7 | done | Stage 7 implement CLI pipeline |

### Test count

Run `pytest` — 58+ tests, no live Scryfall in CI.

### Commands verified

- `pytest`
- `card-downloader --help`
- `card-downloader manifest` / `download` / `sheets` / `explain`

### Notes

- Python >=3.10 (system 3.10.12)
- Manifest format: JSON (`manifest.json`), not CSV
- Live Scryfall required for real deck runs; tests use fixtures + `responses`

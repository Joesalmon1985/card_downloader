# Implementation Progress

## Status: Complete (Stages 0–7) + GUI + PDF regression fix

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
| GUI | done | Add simple Tkinter GUI |
| PDF fix | done | Fix PDF-enabled pipeline regression test coverage |
| CSV report | done | Add CSV card choice report |
| Windows installer | done | Add Windows installer packaging setup |

### Windows installer packaging (Phase B)

**Goal:** PyInstaller + Inno Setup for GUI; real `.exe` built on GitHub Actions `windows-latest` (not on Ubuntu).

**Deliverables:** `packaging/pyinstaller/CardDownloader.spec`, `packaging/windows/CardDownloader.iss`, `scripts/build_windows.ps1`, `scripts/build_linux.sh`, `.github/workflows/windows-installer.yml`, `docs/packaging.md`.

**Tests:** `tests/unit/packaging/test_packaging_config.py`.

### CSV card choice report (Phase A)

**Current outputs:** `manifest.json` (authoritative JSON), `selection-report.md` (human markdown).

**New output:** `card_choices.csv` — spreadsheet-friendly report, one row per unique decklist card (with `quantity`), plus error rows for failed lookups.

**Row model:** Walk parsed decklist in order; first occurrence sets `deck_order` (1-based). `requested_name` and `normalised_name` both use the parsed deck entry name (parser normalises on read; raw pre-normalisation text is not stored).

**Module:** `src/card_downloader/manifest/csv_writer.py` — pure `build_card_choice_rows()` + `write_card_choices_csv()` using stdlib `csv`.

**Pipeline wiring:** `run_download()` and `run_plan()` write `card_choices.csv` alongside existing outputs. GUI logs CSV path on success.

**Manifest extension (backwards-compatible):** optional fields on `ChosenPrintingRecord` — `set_name`, `released_at`, `printing_name`, `promo`, `finishes`, `is_universes_beyond`, `has_special_frame`.

**Tests to add:**

- `tests/unit/manifest/test_csv_writer.py` — rows, escaping, errors
- extend `tests/integration/test_download_pipeline.py` — CSV written on download
- extend `tests/unit/manifest/test_schema.py` — old manifest JSON loads

### Test count

Run `pytest` — 90 tests after Windows packaging config tests (84 before).

### PDF regression (red phase — recorded before fix)

**Missing coverage:** No test exercised `run_download(..., build_pdf=True)` end-to-end. The suite mocked PDF paths or used `--no-pdf`, so a name collision between the `build_pdf` boolean parameter and the imported `build_pdf()` function in `pipeline/download.py` went undetected.

**Red tests added:**

- `tests/integration/test_download_pipeline.py::test_run_download_with_pdf_enabled_builds_proxy_pdf`
- `tests/integration/test_download_pipeline.py::test_run_download_with_pdf_disabled_skips_proxy_pdf`
- `tests/integration/test_cli_download.py::test_cmd_download_default_pdf_enabled`

**Red result (pre-fix):**

```
FAILED test_run_download_with_pdf_enabled_builds_proxy_pdf
FAILED test_cmd_download_default_pdf_enabled
PASSED test_run_download_with_pdf_disabled_skips_proxy_pdf

TypeError: 'bool' object is not callable
  at pipeline/download.py:64 — pdf_result = build_pdf(...)
```

**Implementation fix:** Aliased the imported PDF builder as `build_proxy_pdf` in `pipeline/download.py` so the `build_pdf: bool` parameter no longer shadows the function. Updated both `run_download()` and `run_sheets_from_manifest()` call sites. GUI runner now logs full tracebacks on unexpected errors.

**Green result (post-fix):** `pytest -q` — 78 passed.

**Live smoke tests:**

```bash
card-downloader download input/smoke-deck.txt --out data/runs/cli-smoke-check
# → manifest.json, selection-report.md, images/, proxies.pdf

card-downloader sheets data/runs/cli-smoke-check/manifest.json --out data/runs/cli-smoke-check/proxies-rebuilt.pdf
# → proxies-rebuilt.pdf

# GUI backend (execute_run, PDF enabled, smoke-deck.txt)
# → success, proxies.pdf written to data/runs/gui-smoke-check
```

### Commands verified

- `pytest`
- `card-downloader --help`
- `card-downloader manifest` / `download` / `sheets` / `explain`
- `card-downloader-gui`

### Notes

- Python >=3.10 (system 3.10.12)
- Manifest format: JSON (`manifest.json`), not CSV
- Live Scryfall required for real deck runs; tests use fixtures + mocks

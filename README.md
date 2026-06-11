# Card Downloader

Download Magic: The Gathering card printings from Scryfall, choose printings intelligently for proxy decks, and build printer-ready 3×3 PDF sheets.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

### Full download (manifest + images + PDF)

```bash
card-downloader download data/decklists/example-commander.txt --out data/runs/my-run
```

### Manifest only (no images)

```bash
card-downloader manifest data/decklists/example-commander.txt --out data/runs/my-run
```

### Download without PDF

```bash
card-downloader download data/decklists/example-commander.txt --out data/runs/my-run --no-pdf
```

### Rebuild PDF from existing manifest

```bash
card-downloader sheets data/runs/my-run/manifest.json --out data/runs/my-run/proxies.pdf
```

### Explain printing choices for one card

```bash
card-downloader explain "Sol Ring" --top 5
```

## GUI

For a simple desktop interface (no terminal required):

```bash
card-downloader-gui
```

Pick a decklist and output folder, adjust options, and click **Download & Build Proxies**. See [`docs/gui.md`](docs/gui.md) for details.

## Output layout

```
data/runs/my-run/
  manifest.json
  selection-report.md
  images/
  proxies.pdf
```

## Tests

```bash
pytest
```

See `docs/project-plan.md`, `docs/selection-rules.md`, `docs/tdd-roadmap.md`, and `docs/gui.md` for design details.

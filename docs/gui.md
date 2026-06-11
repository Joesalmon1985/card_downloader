# Card Downloader — GUI

A simple desktop interface for running the card download and proxy PDF pipeline without using the terminal.

## Launch

After installing the package:

```bash
pip install -e ".[dev]"
card-downloader-gui
```

Alternative:

```bash
python -m card_downloader.gui.main
```

On Linux, if you see `ModuleNotFoundError: No module named '_tkinter'`, install the Tk package for your Python version (e.g. `sudo apt install python3-tk`).

## How to use

1. Click **Browse…** next to **Decklist** and select a `.txt` decklist file (quantity-prefixed lines such as `1 Sol Ring`).
2. Choose an **Output folder** (default: `data/runs/gui-run`).
3. Adjust options if needed (see below).
4. Click **Download & Build Proxies**.
5. Watch the log area for progress. When finished, use **Open output folder** or **Open PDF** to view results.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| Image size | `png` | Scryfall image quality: `png` (best for printing), `large`, or `normal`. |
| Paper | `a4` | PDF page size: A4 or US Letter. |
| DPI | `300` | Render resolution for proxy sheets. |
| Gap (mm) | `1.0` | Space between cards on the PDF grid. |
| Build PDF | on | When enabled, creates `proxies.pdf` after downloading images. |
| Allow Universes Beyond | off | Prefer non-UB printings; enable to allow UB sets. |
| Allow white border | off | Prefer black borders; enable to allow white-bordered printings. |
| Allow promo / special | off | Prefer normal printings; enable to allow promos and special treatments. |

Selection rules match the CLI and are documented in [`selection-rules.md`](selection-rules.md).

## Output files

A successful run creates:

```
output-folder/
  manifest.json           # auditable record of chosen printings
  selection-report.md     # human-readable summary
  images/                 # downloaded card PNGs
  proxies.pdf             # 3×3 printer-ready sheets (if Build PDF enabled)
```

## Known limitations

- **English only** — there is no language picker in the GUI (same as CLI default).
- **Download mode only** — no manifest-only, explain, cache, or rebuild-PDF-from-manifest flows in the GUI (use the CLI for those).
- **Network required** — the tool queries Scryfall; large decks may take several minutes.
- **Run button disabled while working** — the window stays responsive, but you cannot start a second run until the current one finishes.
- **No progress bar** — status is shown in the log text area only.
- **Tkinter** — appearance follows your system theme; not custom-styled.

## CLI equivalent

The GUI runs the same pipeline as:

```bash
card-downloader download DECKLIST.txt --out OUTPUT_DIR \
  --size png --paper a4 --dpi 300 --no-pdf   # omit --no-pdf when Build PDF is checked
```

Optional flags map to the Allow checkboxes: `--allow-ub`, `--allow-white-border`, `--allow-promo`.

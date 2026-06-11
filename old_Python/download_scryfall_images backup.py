#!/usr/bin/env python3
"""
download_scryfall_images.py
Download Magic: The Gathering card images from Scryfall.

----------------------------------------------------------
Usage examples
----------------------------------------------------------
# 1. Full-resolution PNGs into ./card_images
python download_scryfall_images.py decklist.txt -o card_images --size png

# 2. Smaller “large” JPEGs into a specific folder
python download_scryfall_images.py decklist.txt -o "D:/mtg/large" --size large
----------------------------------------------------------

Supported --size values  (Scryfall image_uris keys)
    png          ≈ 745×1040 PNG (default, print-quality)
    large        ≈ 488×680  JPG
    normal       ≈ 312×445  JPG
    small        ≈ 146×204  JPG
    art_crop     480×680    JPG (art only)
    border_crop  480×680    JPG (full art, crop to edge)
"""

import argparse
import pathlib
import sys
import time
from typing import Dict, List

import requests

API_NAMED = "https://api.scryfall.com/cards/named"
# Scryfall’s courtesy limit: ~10 requests / second
DELAY_BETWEEN_CALLS_SEC = 0.12


# ───────────────────── Helper functions ──────────────────────────────────── #

def read_card_list(txt_path: pathlib.Path) -> List[str]:
    """Return a list of non-empty, stripped lines."""
    return [
        line.strip()
        for line in txt_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def fetch_card_meta(name: str, tries: int = 3) -> Dict:
    """GET /cards/named?exact=…  with basic retry logic."""
    params = {"exact": name}
    for attempt in range(1, tries + 1):
        resp = requests.get(API_NAMED, params=params, timeout=15)
        if resp.ok:
            return resp.json()
        if attempt == tries:
            raise RuntimeError(f"Scryfall error {resp.status_code} for “{name}”")
        time.sleep(0.5)  # back-off then retry


def download_to_file(url: str, dest: pathlib.Path) -> None:
    """Stream an image from *url* directly into *dest* on disk."""
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in r.iter_content(8192):
                fh.write(chunk)


def safe_filename(base: str) -> str:
    """Turn a card name into a filesystem-safe stub."""
    return (
        base.replace("/", "_")
        .replace(":", "_")
        .replace("?", "")
        .replace("\\", "_")
        .replace("*", "_")
        .replace("\"", "'")
    )


# ───────────────────────────── Main script ───────────────────────────────── #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download MTG card images from Scryfall.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("card_list", help="Path to text file with card names")
    parser.add_argument(
        "-o",
        "--out",
        default="images",
        help="Destination folder (created if missing)",
    )
    parser.add_argument(
        "--size",
        default="png",
        choices=["png", "large", "normal", "small", "art_crop", "border_crop"],
        help="Image size / variant to fetch",
    )
    args = parser.parse_args()

    txt_path = pathlib.Path(args.card_list).expanduser()
    out_dir  = pathlib.Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    cards = read_card_list(txt_path)
    if not cards:
        sys.exit("✘ No card names found – check your list file.")

    print(f"Downloading {len(cards)} card(s) to {out_dir.resolve()} …")

    for idx, card in enumerate(cards, 1):
        try:
            meta = fetch_card_meta(card)
        except Exception as err:
            print(f"⚠️  {err}", file=sys.stderr)
            continue

        def save_face(img_url: str, label: str = "") -> None:
            # Strip cache-buster (the ?123456 part) before determining extension
            clean_url = img_url.split("?", 1)[0]
            ext = clean_url.split(".")[-1]
            dest_name = f"{safe_filename(card)}{label}.{ext}"
            download_to_file(img_url, out_dir / dest_name)

        # Handle double-faced / split cards
        if "card_faces" in meta:
            faces = meta["card_faces"]
            save_face(faces[0]["image_uris"][args.size], "_front")
            save_face(faces[1]["image_uris"][args.size], "_back")
        else:
            save_face(meta["image_uris"][args.size])

        print(f"  {idx:>3}/{len(cards)}  ✔  {card}")
        time.sleep(DELAY_BETWEEN_CALLS_SEC)

    print("✅  All done!")


if __name__ == "__main__":
    main()

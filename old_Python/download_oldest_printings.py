#!/usr/bin/env python3
"""
download_oldest_printings.py
Download **the earliest printing** of each card in a text list from Scryfall.

Usage
-----
python download_oldest_printings.py cards.txt -o ./oldest_png --size png

Dependencies
------------
pip install requests
"""

import argparse
import pathlib
import sys
import time
from typing import Dict, List

import requests
from requests.utils import quote

SEARCH_API = "https://api.scryfall.com/cards/search"
DELAY_SEC  = 0.12          # stay under Scryfall’s 10-req/s courtesy limit


# ────────── helpers ──────────────────────────────────────────────────────── #

def read_names(path: pathlib.Path) -> List[str]:
    return [
        ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]


def earliest_printing(name: str) -> Dict:
    """
    Return the card-object for the *oldest* printing of `name`.
    """
    q = f'!"{name}"'
    url = (
        f"{SEARCH_API}"
        f"?unique=prints&order=released&dir=asc&q={quote(q)}"
    )
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()["data"]
    if not data:
        raise ValueError(f"No card found named “{name}”.")
    return data[0]                 # first = oldest


def dl(url: str, dest: pathlib.Path) -> None:
    """Stream `url` into `dest`."""
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)


def safe(name: str) -> str:
    return (
        name.replace("/", "_")
        .replace(":", "_")
        .replace("?", "")
        .replace("\\", "_")
        .replace("*", "_")
        .replace('"', "'")
    )


# ────────── main ─────────────────────────────────────────────────────────── #

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Download the oldest printed version of each card.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("card_list", help="Text file – one exact card name per line")
    ap.add_argument(
        "-o", "--out", default="oldest_prints",
        help="Destination folder (created if missing)",
    )
    ap.add_argument(
        "--size",
        default="png",
        choices=["png", "large", "normal", "small", "art_crop", "border_crop"],
        help="Image size / variant to fetch",
    )
    args = ap.parse_args()

    names = read_names(pathlib.Path(args.card_list).expanduser())
    if not names:
        sys.exit("✘ No card names found – check your list.")

    out_dir = pathlib.Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(names)} oldest print(s) to {out_dir} …")

    for idx, name in enumerate(names, 1):
        try:
            meta = earliest_printing(name)
        except Exception as e:
            print(f"⚠️  {e}", file=sys.stderr)
            continue

        def save(img_url: str, tag: str = "") -> None:
            clean = img_url.split("?", 1)[0]          # drop cache-buster
            ext   = clean.split(".")[-1]
            fname = f"{safe(name)}{tag}.{ext}"
            dl(img_url, out_dir / fname)

        if "card_faces" in meta:                      # double-faced, etc.
            faces = meta["card_faces"]
            save(faces[0]["image_uris"][args.size], "_front")
            save(faces[1]["image_uris"][args.size], "_back")
        else:
            save(meta["image_uris"][args.size])

        print(f"  {idx:>3}/{len(names)} ✔ {name}")
        time.sleep(DELAY_SEC)

    print("✅  Finished!")


if __name__ == "__main__":
    main()

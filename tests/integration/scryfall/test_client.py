import json
from pathlib import Path

import pytest
import responses

from card_downloader.scryfall.client import ScryfallClient
from card_downloader.scryfall.rate_limit import RateLimiter


def _load(name: str) -> dict:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "scryfall" / name
    return json.loads(path.read_text())


@responses.activate
def test_client_returns_printings(tmp_path):
    page1 = _load("search_sol_ring_page1.json")
    page2 = _load("search_sol_ring_page2.json")

    responses.add(
        responses.GET,
        "https://api.scryfall.com/cards/search",
        json=page1,
        match=[responses.matchers.query_param_matcher({"q": '!"Sol Ring"', "unique": "prints", "include_multilingual": "false"})],
    )
    responses.add(responses.GET, page1["next_page"], json=page2)

    sleeps: list[float] = []
    client = ScryfallClient(
        cache_dir=tmp_path,
        rate_limiter=RateLimiter(min_interval=0.0, sleep_fn=sleeps.append),
    )
    printings = client.search_printings("Sol Ring")
    assert len(printings) == 2
    assert printings[0].set_code == "clu"
    assert printings[1].set_code == "c21"


@responses.activate
def test_client_uses_cache(tmp_path):
    page = _load("search_sol_ring_page2.json")
    page_single = {**page, "has_more": False}

    responses.add(responses.GET, "https://api.scryfall.com/cards/search", json=page_single)

    client = ScryfallClient(cache_dir=tmp_path, rate_limiter=RateLimiter(0.0))
    first = client.search_printings("Sol Ring")
    second = client.search_printings("Sol Ring")
    assert len(first) == 1
    assert len(second) == 1
    assert len(responses.calls) == 1

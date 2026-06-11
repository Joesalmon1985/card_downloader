import json
from pathlib import Path

import pytest

from card_downloader.scryfall.pagination import collect_all_data


def _load(name: str) -> dict:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "scryfall" / name
    return json.loads(path.read_text())


def test_merge_two_pages():
    page1 = _load("search_sol_ring_page1.json")
    page2 = _load("search_sol_ring_page2.json")
    pages = [page1, page2]

    def fetch_page(url: str) -> dict:
        assert "page=2" in url
        return page2

    result = collect_all_data(page1, fetch_page)
    assert len(result) == 2
    assert result[0]["set"] == "clu"
    assert result[1]["set"] == "c21"


def test_stops_when_has_more_false():
    page = _load("search_sol_ring_page2.json")

    def fetch_page(url: str) -> dict:
        raise AssertionError("should not fetch")

    result = collect_all_data(page, fetch_page)
    assert len(result) == 1


def test_empty_first_page():
    empty = {"object": "list", "has_more": False, "data": []}

    def fetch_page(url: str) -> dict:
        raise AssertionError("should not fetch")

    assert collect_all_data(empty, fetch_page) == []

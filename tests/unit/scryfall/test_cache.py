import json
from pathlib import Path

import pytest

from card_downloader.scryfall.cache import FileCache


def test_cache_miss_then_hit(tmp_path):
    cache = FileCache(tmp_path)
    key = "test-query"
    assert cache.get(key) is None

    payload = {"object": "list", "data": []}
    cache.set(key, payload)
    assert cache.get(key) == payload


def test_stable_cache_key():
    cache = FileCache(Path("/tmp/unused"))
    k1 = cache.make_key("search", {"q": '!"Sol Ring"', "unique": "prints"})
    k2 = cache.make_key("search", {"unique": "prints", "q": '!"Sol Ring"'})
    assert k1 == k2


def test_cache_dir_created(tmp_path):
    cache_dir = tmp_path / "nested" / "cache"
    cache = FileCache(cache_dir)
    cache.set("k", {"x": 1})
    assert cache_dir.exists()

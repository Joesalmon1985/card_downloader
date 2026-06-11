from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from card_downloader.scryfall.cache import FileCache
from card_downloader.scryfall.models import CardPrinting
from card_downloader.scryfall.pagination import collect_all_data
from card_downloader.scryfall.rate_limit import RateLimiter

SEARCH_URL = "https://api.scryfall.com/cards/search"


class RequestsHttpClient:
    def get(self, url: str, *, params: dict[str, Any] | None = None, timeout: float = 30) -> requests.Response:
        return requests.get(url, params=params, timeout=timeout)


class ScryfallClient:
    def __init__(
        self,
        cache_dir: Path | None = None,
        http: RequestsHttpClient | None = None,
        rate_limiter: RateLimiter | None = None,
        use_cache: bool = True,
    ) -> None:
        self._http = http or RequestsHttpClient()
        self._rate = rate_limiter or RateLimiter()
        self._cache = FileCache(cache_dir) if cache_dir else None
        self._use_cache = use_cache and cache_dir is not None

    def search_printings(self, name: str, *, include_multilingual: bool = False) -> list[CardPrinting]:
        params = {
            "q": f'!"{name}"',
            "unique": "prints",
            "include_multilingual": str(include_multilingual).lower(),
        }
        cache_key = None
        if self._cache is not None:
            cache_key = self._cache.make_key("search", params)

        if self._use_cache and cache_key and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return [CardPrinting.from_api_dict(c) for c in cached]

        self._rate.wait()
        resp = self._http.get(SEARCH_URL, params=params)
        resp.raise_for_status()
        first = resp.json()

        def fetch_page(url: str) -> dict[str, Any]:
            self._rate.wait()
            r = self._http.get(url)
            r.raise_for_status()
            return r.json()

        raw_cards = collect_all_data(first, fetch_page)
        if self._use_cache and cache_key and self._cache:
            self._cache.set(cache_key, raw_cards)

        return [CardPrinting.from_api_dict(c) for c in raw_cards]

    def search_universes_beyond_ids(self, name: str) -> set[str]:
        params = {
            "q": f'!"{name}" is:universesbeyond',
            "unique": "prints",
            "include_multilingual": "false",
        }
        cache_key = None
        if self._cache is not None:
            cache_key = self._cache.make_key("ub", params)

        if self._use_cache and cache_key and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return set(cached)

        self._rate.wait()
        resp = self._http.get(SEARCH_URL, params=params)
        if resp.status_code == 404:
            ids: set[str] = set()
        else:
            resp.raise_for_status()
            first = resp.json()

            def fetch_page(url: str) -> dict[str, Any]:
                self._rate.wait()
                r = self._http.get(url)
                r.raise_for_status()
                return r.json()

            raw = collect_all_data(first, fetch_page)
            ids = {c["id"] for c in raw}

        if self._use_cache and cache_key and self._cache:
            self._cache.set(cache_key, sorted(ids))
        return ids

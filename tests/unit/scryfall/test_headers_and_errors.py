import json

import pytest
import requests
import responses

from card_downloader import __version__
from card_downloader.scryfall.client import RequestsHttpClient, ScryfallClient
from card_downloader.scryfall.errors import ScryfallAPIError, check_response
from card_downloader.scryfall.headers import SCRYFALL_HEADERS
from card_downloader.scryfall.rate_limit import RateLimiter


def test_default_headers_include_user_agent_and_accept():
    assert "User-Agent" in SCRYFALL_HEADERS
    assert "Accept" in SCRYFALL_HEADERS
    assert SCRYFALL_HEADERS["Accept"] == "application/json"
    assert __version__ in SCRYFALL_HEADERS["User-Agent"]


@responses.activate
def test_search_request_sends_scryfall_headers(tmp_path):
    body = {"object": "list", "has_more": False, "data": []}
    responses.add(responses.GET, "https://api.scryfall.com/cards/search", json=body)

    client = ScryfallClient(cache_dir=tmp_path, rate_limiter=RateLimiter(0.0))
    client.search_printings("Sol Ring")

    req = responses.calls[0].request
    assert req.headers["User-Agent"] == SCRYFALL_HEADERS["User-Agent"]
    assert req.headers["Accept"] == "application/json"


@responses.activate
def test_pagination_request_sends_scryfall_headers(tmp_path):
    page1 = {
        "object": "list",
        "has_more": True,
        "next_page": "https://api.scryfall.com/cards/search?page=2",
        "data": [{"object": "card", "id": "1", "name": "Sol Ring", "lang": "en", "layout": "normal",
                  "set": "clu", "set_name": "X", "set_type": "commander", "collector_number": "1",
                  "digital": False, "games": ["paper"], "border_color": "black", "frame": "2015",
                  "finishes": ["nonfoil"], "highres_image": True, "image_status": "highres_scan",
                  "image_uris": {"png": "https://example.com/a.png"}, "scryfall_uri": "https://example.com",
                  "released_at": "2024-01-01", "reprint": True}],
    }
    page2 = {"object": "list", "has_more": False, "data": []}
    responses.add(responses.GET, "https://api.scryfall.com/cards/search", json=page1)
    responses.add(responses.GET, page1["next_page"], json=page2)

    client = ScryfallClient(cache_dir=tmp_path, rate_limiter=RateLimiter(0.0))
    client.search_printings("Sol Ring")

    assert len(responses.calls) == 2
    for call in responses.calls:
        assert call.request.headers["User-Agent"] == SCRYFALL_HEADERS["User-Agent"]
        assert call.request.headers["Accept"] == "application/json"


def test_check_response_raises_with_details():
    resp = requests.models.Response()
    resp.status_code = 400
    resp.url = "https://api.scryfall.com/cards/search?q=test"
    resp._content = json.dumps(
        {"object": "error", "code": "bad_request", "details": "Missing headers", "status": 400}
    ).encode()

    with pytest.raises(ScryfallAPIError) as exc_info:
        check_response(resp)

    err = exc_info.value
    assert err.status_code == 400
    assert "Missing headers" in str(err)
    assert "search" in err.url


def test_scryfall_api_error_str_includes_status_and_body():
    err = ScryfallAPIError(400, "bad request: need User-Agent", "https://api.scryfall.com/cards/search")
    text = str(err)
    assert "400" in text
    assert "User-Agent" in text
    assert "api.scryfall.com" in text

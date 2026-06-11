from __future__ import annotations

import json
from typing import Any

import requests


class ScryfallAPIError(Exception):
    """Raised when the Scryfall API returns an error response."""

    def __init__(self, status_code: int, detail: str, url: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.url = url
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        return f"Scryfall API error {self.status_code} for {self.url}: {self.detail}"


def extract_error_detail(response: requests.Response) -> str:
    try:
        data: dict[str, Any] = response.json()
        if data.get("object") == "error":
            parts = [data.get("code") or "error"]
            if data.get("details"):
                parts.append(str(data["details"]))
            return ": ".join(parts)
        return response.text[:500] if response.text else response.reason
    except (json.JSONDecodeError, ValueError):
        text = (response.text or "").strip()
        return text[:500] if text else response.reason or "Unknown error"


def check_response(response: requests.Response) -> None:
    if response.ok:
        return
    raise ScryfallAPIError(
        response.status_code,
        extract_error_detail(response),
        str(response.url),
    )

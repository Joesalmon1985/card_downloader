from typing import Any, Callable


def collect_all_data(
    first_page: dict[str, Any],
    fetch_page: Callable[[str], dict[str, Any]],
) -> list[dict[str, Any]]:
    items = list(first_page.get("data") or [])
    page = first_page
    while page.get("has_more") and page.get("next_page"):
        page = fetch_page(page["next_page"])
        items.extend(page.get("data") or [])
    return items

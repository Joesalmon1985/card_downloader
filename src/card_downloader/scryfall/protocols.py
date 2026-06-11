from typing import Any, Protocol


class HttpClient(Protocol):
    def get(self, url: str, *, params: dict[str, Any] | None = None, timeout: float = 30) -> Any:
        ...


class CacheStore(Protocol):
    def get(self, key: str) -> dict[str, Any] | None:
        ...

    def set(self, key: str, value: dict[str, Any]) -> None:
        ...

    def make_key(self, namespace: str, params: dict[str, Any]) -> str:
        ...

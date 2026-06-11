import hashlib
import json
from pathlib import Path
from typing import Any


class FileCache:
    def __init__(self, directory: Path) -> None:
        self._dir = directory

    def make_key(self, namespace: str, params: dict[str, Any]) -> str:
        canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(f"{namespace}:{canonical}".encode()).hexdigest()
        return digest

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path(key).write_text(json.dumps(value), encoding="utf-8")

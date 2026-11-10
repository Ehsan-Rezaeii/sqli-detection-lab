"""Small canonical JSON and provenance helpers."""

import hashlib
import json
from pathlib import Path


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: str | Path) -> str:
    return digest_bytes(Path(path).read_bytes())


def write_json(path: str | Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def read_json(path: str | Path):
    return json.loads(Path(path).read_text())

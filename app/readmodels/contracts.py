from __future__ import annotations

from pathlib import Path
import json
from typing import TypedDict


class JsonDict(TypedDict, total=False):
    pass


def write_canonical_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
        encoding="utf-8",
    )

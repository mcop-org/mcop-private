from __future__ import annotations

import json

from app.service.config import get_service_paths


def load_readmodel(name: str) -> dict[str, object]:
    paths = get_service_paths()
    path = paths.readmodels_dir / f"{name}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

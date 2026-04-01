from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    status_code: int
    payload: dict[str, object]

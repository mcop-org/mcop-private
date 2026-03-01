from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


SEVERITY_ORDER: Dict[str, int] = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


@dataclass(frozen=True)
class Action:
    id: str
    type: str
    severity: str
    message: str
    owner: str
    due_in_days: int
    triggered_by: List[str]


def action_to_dict(a: Action) -> Dict[str, Any]:
    d = asdict(a)
    # Determinism: ensure triggered_by is sorted
    d["triggered_by"] = sorted(d["triggered_by"])
    return d

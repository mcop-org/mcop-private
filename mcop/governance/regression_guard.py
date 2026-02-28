
import json
from pathlib import Path
from typing import Any, Dict, List

def _len(x) -> int:
    try:
        return len(x)
    except Exception:
        return 0

def _get(d: Dict[str, Any], path: List[str], default=None):
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def build_struct_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    top_payables = payload.get("top_payables_60", [])
    top_receivables = payload.get("top_receivables_60", [])
    at_risk = _get(payload, ["container_exposure", "top_at_risk_incoming"], []) or []

    return {
        "top_payables_60_count": _len(top_payables),
        "top_receivables_60_count": _len(top_receivables),
        "top_at_risk_incoming_count": _len(at_risk),
        "has_container_exposure": isinstance(payload.get("container_exposure"), dict),
    }

def compare_struct(old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
    issues: List[str] = []

    # Hard regressions: data vanished or collapsed
    if old.get("top_payables_60_count", 0) > 0 and new.get("top_payables_60_count", 0) == 0:
        issues.append("top_payables_60 disappeared or became empty")
    if old.get("top_receivables_60_count", 0) > 0 and new.get("top_receivables_60_count", 0) == 0:
        issues.append("top_receivables_60 disappeared or became empty")
    if old.get("has_container_exposure", False) and not new.get("has_container_exposure", False):
        issues.append("container_exposure disappeared")

    # Soft warning: big drop (e.g., 5 -> 1)
    if old.get("top_payables_60_count", 0) >= 4 and new.get("top_payables_60_count", 0) <= 2:
        issues.append(f"top_payables_60 shrank {old.get('top_payables_60_count')}→{new.get('top_payables_60_count')}")
    if old.get("top_receivables_60_count", 0) >= 4 and new.get("top_receivables_60_count", 0) <= 2:
        issues.append(f"top_receivables_60 shrank {old.get('top_receivables_60_count')}→{new.get('top_receivables_60_count')}")

    return issues

def run_regression_guard(out_dir: Path, payload: Dict[str, Any]) -> List[str]:
    snap_path = out_dir / "data_snapshot.json"
    new_snap = build_struct_snapshot(payload)

    if snap_path.exists():
        old_snap = json.loads(snap_path.read_text(encoding="utf-8"))
        issues = compare_struct(old_snap, new_snap)
    else:
        issues = []

    snap_path.write_text(json.dumps(new_snap, indent=2), encoding="utf-8")
    return issues

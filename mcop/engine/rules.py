from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcop.engine.actions import Action, SEVERITY_ORDER, action_to_dict


@dataclass(frozen=True)
class Rule:
    id: str
    priority: int
    conditions: Dict[str, Any]
    action: Dict[str, Any]


def default_rules_path() -> Path:
    # mcop/engine/rules.py -> repo_root/policy/rules.json
    return Path(__file__).resolve().parents[2] / "policy" / "rules.json"


def load_rules(path: Optional[str | Path] = None) -> List[Rule]:
    p = Path(path) if path is not None else default_rules_path()
    raw = json.loads(p.read_text(encoding="utf-8"))

    if not isinstance(raw, list):
        raise ValueError("rules file must be a JSON list of rule objects")

    rules: List[Rule] = []
    for r in raw:
        if not isinstance(r, dict):
            raise ValueError("each rule must be an object")
        rid = r.get("id")
        prio = r.get("priority")
        cond = r.get("conditions")
        act = r.get("action")

        if not isinstance(rid, str) or not rid:
            raise ValueError("rule.id must be a non-empty string")
        if not isinstance(prio, int):
            raise ValueError(f"rule {rid}: priority must be an int")
        if not isinstance(cond, dict):
            raise ValueError(f"rule {rid}: conditions must be an object")
        if not isinstance(act, dict):
            raise ValueError(f"rule {rid}: action must be an object")

        # Determinism + safety: only allow equality checks against JSON scalar values
        for k, v in cond.items():
            if not isinstance(k, str) or not k:
                raise ValueError(f"rule {rid}: condition keys must be non-empty strings")
            if not isinstance(v, (str, int, float, bool)) and v is not None:
                raise ValueError(f"rule {rid}: condition values must be JSON scalars")

        rules.append(Rule(id=rid, priority=prio, conditions=dict(cond), action=dict(act)))

    # Deterministic base ordering (id)
    return sorted(rules, key=lambda x: x.id)


def _matches(rule: Rule, payload: Dict[str, Any]) -> bool:
    # AND-only + equality-only
    for k, expected in rule.conditions.items():
        if k not in payload:
            return False
        if payload[k] != expected:
            return False
    return True


def _action_from_rule(rule: Rule) -> Action:
    a = rule.action
    typ = str(a.get("type") or "").strip()
    sev = str(a.get("severity") or "").strip().upper()
    msg = str(a.get("message") or "").strip()
    owner = str(a.get("owner") or "").strip()
    due = a.get("due_in_days")

    if typ == "":
        raise ValueError(f"rule {rule.id}: action.type missing")
    if sev not in SEVERITY_ORDER:
        raise ValueError(f"rule {rule.id}: action.severity invalid")
    if owner == "":
        raise ValueError(f"rule {rule.id}: action.owner missing")
    if not isinstance(due, int):
        raise ValueError(f"rule {rule.id}: action.due_in_days must be int")

    return Action(
        id=rule.id,
        type=typ,
        severity=sev,
        message=msg,
        owner=owner,
        due_in_days=due,
        triggered_by=[rule.id],
    )


def evaluate_rules(payload: dict, rules_path: Optional[str | Path] = None) -> List[Dict[str, Any]]:
    """
    Evaluate all rules deterministically, returning a list of structured actions.
    Sorting: priority desc, then severity (CRITICAL>HIGH>MEDIUM>LOW), then id.
    Dedup: by action.type (keep highest priority).
    """
    if not isinstance(payload, dict):
        payload = {}

    rules = load_rules(rules_path)

    matched: List[Rule] = [r for r in rules if _matches(r, payload)]

    matched_sorted = sorted(
        matched,
        key=lambda r: (-r.priority, -SEVERITY_ORDER.get(str(r.action.get("severity", "")).upper(), 0), r.id),
    )

    actions: List[Action] = [_action_from_rule(r) for r in matched_sorted]

    # Deduplicate by action.type, keeping first (highest ranked)
    seen_types = set()
    deduped: List[Action] = []
    for a in actions:
        if a.type in seen_types:
            continue
        seen_types.add(a.type)
        deduped.append(a)

    # Deterministic output order already ensured; convert to dicts
    return [action_to_dict(a) for a in deduped]

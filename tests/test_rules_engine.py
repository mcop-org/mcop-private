from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcop.engine.rules import evaluate_rules, load_rules


def test_rules_load() -> None:
    rules = load_rules()
    assert isinstance(rules, list)
    assert len(rules) >= 5
    ids = {r.id for r in rules}
    assert "BLOCK_IF_SCORE_RED" in ids


def test_missing_keys_do_not_match() -> None:
    out = evaluate_rules({"score_band": "RED"})  # missing pinch flags/exposure may still match score rule
    assert any(a["type"] == "BLOCK" for a in out)

    out2 = evaluate_rules({"pinch_14d": True})  # should match pause buying
    assert any(a["type"] == "PAUSE_BUYING" for a in out2)

    out3 = evaluate_rules({"pinch_14d": True, "exposure_flag": "OK"})
    # should NOT match BLOCK_IF_PINCH_14D_AND_EXPOSURE
    assert not any(a["id"] == "BLOCK_IF_PINCH_14D_AND_EXPOSURE" for a in out3)


def test_sorting_and_dedupe() -> None:
    payload = {"pinch_14d": True, "pinch_30d": True, "exposure_flag": "BLOCK", "score_band": "RED"}
    out = evaluate_rules(payload)

    # Dedup by action type: BLOCK appears once even if multiple rules generate BLOCK
    blocks = [a for a in out if a["type"] == "BLOCK"]
    assert len(blocks) == 1

    # Highest priority should be first
    assert out[0]["id"] == "BLOCK_IF_PINCH_14D_AND_EXPOSURE"


def test_determinism_same_input_same_output() -> None:
    payload = {"pinch_14d": True, "pinch_30d": True, "exposure_flag": "BLOCK", "score_band": "AMBER"}
    out1 = evaluate_rules(payload)
    out2 = evaluate_rules(payload)
    assert json.dumps(out1, sort_keys=True) == json.dumps(out2, sort_keys=True)


def test_can_load_custom_rules_file(tmp_path: Path) -> None:
    rules = [
        {
            "id": "R1",
            "priority": 1,
            "conditions": {"x": 1},
            "action": {"type": "TIGHTEN_SPEND", "severity": "LOW", "message": "m", "owner": "COO", "due_in_days": 1},
        }
    ]
    p = tmp_path / "rules.json"
    p.write_text(json.dumps(rules), encoding="utf-8")

    loaded = load_rules(p)
    assert len(loaded) == 1

    out = evaluate_rules({"x": 1}, rules_path=p)
    assert out[0]["type"] == "TIGHTEN_SPEND"

from __future__ import annotations

import math

from mcop.engine.score import compute_cash_risk_score


def test_score_is_int_and_clamped() -> None:
    out = compute_cash_risk_score({"runway_days": 45, "pinch_14d": False, "pinch_30d": False, "exposure_flag": "OK", "trading_health_score": 80})
    assert isinstance(out["cash_risk_score"], int)
    assert 0 <= out["cash_risk_score"] <= 100
    assert out["score_band"] in {"GREEN", "AMBER", "RED"}


def test_band_thresholds() -> None:
    # Force very low risk
    out_g = compute_cash_risk_score({"runway_days": 200, "pinch_14d": False, "pinch_30d": False, "exposure_flag": "OK", "trading_health_score": 100,
                                    "runway_days_base": 200, "runway_days_stress": 200})
    assert out_g["score_band"] == "GREEN"

    # Force very high risk
    out_r = compute_cash_risk_score({"runway_days": 0, "pinch_14d": True, "pinch_30d": True, "exposure_flag": "BLOCK", "trading_health_score": 0,
                                    "runway_days_base": 60, "runway_days_stress": 0})
    assert out_r["score_band"] == "RED"


def test_breakdown_shape() -> None:
    out = compute_cash_risk_score({"runway_days": 60, "pinch_14d": False, "pinch_30d": True, "exposure_flag": "OK", "trading_health_score": 60,
                                   "runway_days_base": 60, "runway_days_stress": 50})
    bd = out["score_breakdown"]
    assert "components" in bd
    assert "top_drivers" in bd
    assert len(bd["top_drivers"]) == 3
    for k in ["runway", "pinch", "exposure", "stress", "trading_health"]:
        assert k in bd["components"]
        c = bd["components"][k]
        assert set(c.keys()) == {"value", "weight", "contribution", "notes"}


def test_monotonic_runway_lower_not_reduce_risk() -> None:
    base = {"pinch_14d": False, "pinch_30d": False, "exposure_flag": "OK", "trading_health_score": 80,
            "runway_days_base": 60, "runway_days_stress": 60}
    s1 = compute_cash_risk_score({**base, "runway_days": 120})["cash_risk_score"]
    s2 = compute_cash_risk_score({**base, "runway_days": 10})["cash_risk_score"]
    assert s2 >= s1


def test_monotonic_pinch14_true_not_reduce_risk() -> None:
    base = {"runway_days": 60, "pinch_30d": False, "exposure_flag": "OK", "trading_health_score": 80,
            "runway_days_base": 60, "runway_days_stress": 60}
    s0 = compute_cash_risk_score({**base, "pinch_14d": False})["cash_risk_score"]
    s1 = compute_cash_risk_score({**base, "pinch_14d": True})["cash_risk_score"]
    assert s1 >= s0


def test_stress_component_falls_back_for_infinite_runway_inputs() -> None:
    out = compute_cash_risk_score(
        {
            "runway_days": 45,
            "pinch_14d": False,
            "pinch_30d": False,
            "exposure_flag": "OK",
            "trading_health_score": 8,
            "runway_days_base": math.inf,
            "runway_days_stress": math.inf,
        }
    )
    stress = out["score_breakdown"]["components"]["stress"]
    assert out["cash_risk_score"] == 25
    assert stress["value"] == 40
    assert stress["notes"] == "missing stress runway"


def test_non_finite_trading_health_uses_existing_fallback() -> None:
    out = compute_cash_risk_score(
        {
            "runway_days": 45,
            "pinch_14d": False,
            "pinch_30d": False,
            "exposure_flag": "OK",
            "trading_health_score": math.inf,
            "runway_days_base": 60,
            "runway_days_stress": 45,
        }
    )
    trading_health = out["score_breakdown"]["components"]["trading_health"]
    assert isinstance(out["cash_risk_score"], int)
    assert trading_health["value"] == 50
    assert trading_health["notes"] == "missing trading health"

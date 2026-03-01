from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import math

# =========================================================
# Week 3 Cash Risk Score (0–100)
# Deterministic, pure, no side effects.
# =========================================================

# Weights (sum = 1.00) — MUST MATCH SPEC
WEIGHTS: Dict[str, float] = {
    "runway": 0.35,
    "pinch": 0.25,
    "exposure": 0.20,
    "stress": 0.15,
    "trading_health": 0.05,
}

# Band thresholds — MUST MATCH SPEC
BAND_GREEN_MAX = 33
BAND_AMBER_MAX = 66

SCORE_MIN = 0
SCORE_MAX = 100


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def _safe_float(x: Any) -> float | None:
    try:
        v = float(x)
        if math.isnan(v):
            return None
        return v
    except Exception:
        return None


def _linear_map(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    # Deterministic linear interpolation with guard
    if x1 == x0:
        return y0
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def _runway_risk(runway_days: Any) -> Tuple[int, str]:
    rd = _safe_float(runway_days)
    if rd is None:
        return 50, "missing runway"

    # Spec mapping (risk 0..100)
    if rd <= 14:
        return 100, f"runway_days={rd:.0f} (<=14)"
    if 15 <= rd <= 30:
        r = _linear_map(rd, 15, 30, 85, 65)
        return int(round(_clamp(r))), f"runway_days={rd:.0f} (15..30)"
    if 31 <= rd <= 60:
        r = _linear_map(rd, 31, 60, 65, 35)
        return int(round(_clamp(r))), f"runway_days={rd:.0f} (31..60)"
    if 61 <= rd <= 120:
        r = _linear_map(rd, 61, 120, 35, 10)
        return int(round(_clamp(r))), f"runway_days={rd:.0f} (61..120)"
    return 5, f"runway_days={rd:.0f} (>120)"


def _pinch_risk(payload: Dict[str, Any]) -> Tuple[int, str]:
    # Spec expects booleans. We accept either:
    # - boolean-like payload["pinch_14d"] / payload["pinch_30d"]
    # - OR existing dicts (current MCOP) where cash_alert != GREEN implies pinch risk.
    def _boolish(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            s = v.strip().upper()
            if s in ("TRUE", "T", "YES", "Y", "1"):
                return True
            if s in ("FALSE", "F", "NO", "N", "0", ""):
                return False
            if s in ("AMBER", "RED"):
                return True
            if s in ("GREEN",):
                return False
        return False

    p14 = payload.get("pinch_14d", None)
    p30 = payload.get("pinch_30d", None)

    # If dict, interpret cash_alert (GREEN => False, AMBER/RED => True)
    if isinstance(p14, dict):
        p14_flag = _boolish(p14.get("cash_alert"))
    else:
        p14_flag = _boolish(p14)

    if isinstance(p30, dict):
        p30_flag = _boolish(p30.get("cash_alert"))
    else:
        p30_flag = _boolish(p30)

    # Spec:
    # - if pinch_14d == True -> 100
    # - elif pinch_30d == True -> 70
    # - else -> 0
    if p14_flag:
        return 100, "pinch_14d=True"
    if p30_flag:
        return 70, "pinch_30d=True"
    return 0, "no pinch flags"


def _exposure_risk(exposure_flag: Any) -> Tuple[int, str]:
    # Spec:
    # - if exposure_flag == True -> 80 else 0
    # In MCOP, exposure_flag is a string ("OK"/"BLOCK"/etc). We treat non-OK as flagged.
    if isinstance(exposure_flag, bool):
        return (80, "exposure_flag=True") if exposure_flag else (0, "exposure_flag=False")

    s = str(exposure_flag or "").strip().upper()
    if s in ("", "OK", "GREEN"):
        return 0, f"exposure_flag={s or 'OK'}"
    return 80, f"exposure_flag={s} (flagged)"


def _stress_risk(payload: Dict[str, Any]) -> Tuple[int, str]:
    # Spec: Prefer runway delta if both present:
    # delta = base_runway_days - stress_runway_days
    # - delta >= 30 -> 100
    # - 15..29 -> linear 70..95
    # - 1..14 -> linear 20..70
    # - delta <= 0 -> 0
    base_rd = payload.get("runway_days_base", None)
    stress_rd = payload.get("runway_days_stress", None)

    # Try current MCOP structure: payload["base"]["runway_days"], payload["stress"]["runway_days"]
    if base_rd is None and isinstance(payload.get("base"), dict):
        base_rd = payload["base"].get("runway_days")
    if stress_rd is None and isinstance(payload.get("stress"), dict):
        stress_rd = payload["stress"].get("runway_days")

    b = _safe_float(base_rd)
    s = _safe_float(stress_rd)

    if b is None or s is None:
        return 40, "missing stress runway"

    delta = b - s
    if delta <= 0:
        return 0, f"delta={delta:.0f} (<=0)"
    if delta >= 30:
        return 100, f"delta={delta:.0f} (>=30)"
    if 15 <= delta <= 29:
        r = _linear_map(delta, 15, 29, 70, 95)
        return int(round(_clamp(r))), f"delta={delta:.0f} (15..29)"
    # 1..14
    r = _linear_map(delta, 1, 14, 20, 70)
    return int(round(_clamp(r))), f"delta={delta:.0f} (1..14)"


def _trading_health_risk(trading_health_score: Any) -> Tuple[int, str]:
    # Spec expects 0..100 where higher is better:
    # risk = clamp(100 - trading_health_score)
    th = _safe_float(trading_health_score)
    if th is None:
        return 50, "missing trading health"

    # MCOP currently outputs ~6.2 (0..10). If <= 10, scale to 0..100.
    if th <= 10:
        th_scaled = th * 10.0
        risk = 100.0 - th_scaled
        return int(round(_clamp(risk))), f"trading_health={th:.1f}/10 (scaled)"
    risk = 100.0 - th
    return int(round(_clamp(risk))), f"trading_health={th:.1f}/100"


@dataclass(frozen=True)
class _ComponentOut:
    name: str
    value: int
    weight: float
    contribution: float
    notes: str


def compute_cash_risk_score(payload: dict) -> dict:
    """Return {cash_risk_score, score_band, score_breakdown} per Week 3 spec."""
    if not isinstance(payload, dict):
        payload = {}

    runway_val, runway_note = _runway_risk(payload.get("runway_days", None) or (payload.get("base", {}) or {}).get("runway_days"))
    pinch_val, pinch_note = _pinch_risk(payload)
    exposure_val, exposure_note = _exposure_risk(payload.get("exposure_flag", None))
    stress_val, stress_note = _stress_risk(payload)
    th_val, th_note = _trading_health_risk(payload.get("trading_health_score", None))

    comps: List[_ComponentOut] = []
    for name, val, note in [
        ("runway", runway_val, runway_note),
        ("pinch", pinch_val, pinch_note),
        ("exposure", exposure_val, exposure_note),
        ("stress", stress_val, stress_note),
        ("trading_health", th_val, th_note),
    ]:
        w = float(WEIGHTS[name])
        contrib = float(val) * w
        comps.append(_ComponentOut(name=name, value=int(_clamp(val)), weight=w, contribution=contrib, notes=note))

    total = sum(c.contribution for c in comps)
    final_score = int(round(_clamp(total)))

    if final_score <= BAND_GREEN_MAX:
        band = "GREEN"
    elif final_score <= BAND_AMBER_MAX:
        band = "AMBER"
    else:
        band = "RED"

    # Top 3 by contribution desc, tie-break by name for determinism
    top = sorted(comps, key=lambda c: (-c.contribution, c.name))[:3]

    score_breakdown = {
        "components": {
            c.name: {
                "value": c.value,
                "weight": c.weight,
                "contribution": round(c.contribution, 6),
                "notes": c.notes,
            }
            for c in sorted(comps, key=lambda c: c.name)
        },
        "top_drivers": [c.name for c in top],
    }

    return {
        "cash_risk_score": int(final_score),
        "score_band": band,
        "score_breakdown": score_breakdown,
    }

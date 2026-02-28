from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def compute_drift_signals(out_dir: Path) -> List[str]:
    signals: List[str] = []

    # -------------------------
    # A) Trend-based drift (needs 2 history points)
    # -------------------------
    history_path = out_dir / "history.json"
    if history_path.exists():
        try:
            history: List[Dict[str, Any]] = json.loads(history_path.read_text(encoding="utf-8"))
        except Exception:
            history = []

        if len(history) >= 2:
            prev = history[-2] or {}
            last = history[-1] or {}

            gap_prev = prev.get("total_presell_gap")
            gap_last = last.get("total_presell_gap")

            try:
                if gap_prev is not None and gap_last is not None:
                    gap_prev = float(gap_prev)
                    gap_last = float(gap_last)

                    if gap_last > gap_prev:
                        signals.append("🚨 Sales gap widening (pre-sell position deteriorating).")
                    elif gap_last == gap_prev:
                        signals.append("⚠ Sales momentum stalled (no improvement this week).")
            except Exception:
                pass

            dep_prev = prev.get("deployment_ratio")
            dep_last = last.get("deployment_ratio")

            try:
                if dep_prev is not None and dep_last is not None:
                    dep_prev = float(dep_prev)
                    dep_last = float(dep_last)

                    if dep_last > dep_prev:
                        signals.append("⚠ Exposure increasing (more unsold incoming vs cash buffer).")
            except Exception:
                pass

    # -------------------------
    # B) Near-landing risk
    # -------------------------
    report = _read_json(out_dir / "liquidity_report.json") or {}
    container = (report.get("container_exposure") or {})

    at_risk = container.get("top_at_risk_incoming") or []
    urgent = []

    for x in at_risk:
        try:
            days = int(x.get("days_to_landing"))
        except Exception:
            continue

        if days <= 21:
            urgent.append(x)

    if urgent:
        urgent.sort(key=lambda r: int(r.get("days_to_landing", 9999)))
        u = urgent[0]

        ref = u.get("product_reference") or u.get("product_id") or "unknown"
        days = int(u.get("days_to_landing"))
        gap = u.get("shortfall_value_gbp")

        if gap is not None:
            try:
                gap_f = float(gap)
                gap_txt = f"≈£{gap_f:,.0f}"
            except Exception:
                gap_txt = "a material amount"
        else:
            gap_txt = "a material amount"

        signals.append(
            f"🚨 Landing risk urgent: {ref} lands in {days} days and is still under target ({gap_txt} gap)."
        )

    return signals

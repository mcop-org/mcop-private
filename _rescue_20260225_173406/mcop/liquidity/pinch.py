
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd


def _best_label(row: Dict[str, Any]) -> str:
    return row.get("product_reference") or row.get("product_id") or "unknown"

def _to_ts(x) -> Optional[pd.Timestamp]:
    try:
        return pd.to_datetime(x)
    except Exception:
        return None

def _sum_amount(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return 0.0
    return float(df["amount"].sum())

def _top_event(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    if df is None or df.empty:
        return None
    row = df.sort_values("amount", ascending=False).iloc[0].to_dict()
    # normalise
    out = {
        "date": str(pd.to_datetime(row.get("date")).date()) if row.get("date") is not None else None,
        "amount": float(row.get("amount") or 0.0),
        "product_id": row.get("product_id"),
        "product_reference": row.get("product_reference"),
        "event_type": row.get("event_type"),
        "label": _best_label(row),
    }
    return out

def compute_pinch_14d(
    as_of: pd.Timestamp,
    payables: pd.DataFrame,
    receivables: pd.DataFrame,
    days: int = 14,
) -> Dict[str, Any]:
    """
    Simple cash pinch view: next N days ins/outs, plus biggest in/out event.
    Expects payables/receivables DataFrames with at least columns: date, amount,
    and optional: product_id, product_reference, event_type.
    """
    as_of = pd.to_datetime(as_of)
    end = as_of + pd.Timedelta(days=int(days))

    def _window(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=["date","amount","product_id","product_reference","event_type"])
        x = df.copy()
        x["date"] = pd.to_datetime(x["date"])
        x = x[(x["date"] >= as_of) & (x["date"] < end)]
        return x

    p = _window(payables)
    r = _window(receivables)

    out_total = _sum_amount(p)
    in_total = _sum_amount(r)
    net = in_total - out_total

    return {
        "as_of": str(as_of.date()),
        "window_days": int(days),
        "expected_in_gbp": round(in_total, 2),
        "expected_out_gbp": round(out_total, 2),
        "net_gbp": round(net, 2),
        "biggest_out": _top_event(p),
        "biggest_in": _top_event(r),
    }

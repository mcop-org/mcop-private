import math
import pandas as pd
from typing import List, Dict


def _clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value or "").strip()

def governance_flag(liquidity_60: float, runway_days: float) -> str:
    if liquidity_60 < 0:
        return "BLOCK"
    if runway_days < 45:
        return "WATCH"
    return "OK"

def build_product_reference_map(products: pd.DataFrame) -> dict:
    """
    Map product_id -> product_reference.
    Supports canonical headers (product_id/product_reference) and legacy headers.
    """
    out: dict[str, str] = {}
    if products is None:
        return out

    # DataFrame or list[dict]
    if hasattr(products, "to_dict"):
        rows = products.to_dict(orient="records")
    else:
        rows = list(products)

    for r in rows:
        pid = str(r.get("product_id") or r.get("Product Id") or "").strip()
        pref = str(r.get("product_reference") or r.get("Product Reference") or "").strip()
        if pid:
            out[pid] = pref
    return out

def top_events_within(events: pd.DataFrame,
                      as_of: pd.Timestamp,
                      days: int,
                      product_map: dict,
                      top_n: int = 5) -> List[Dict]:

    if events is None or events.empty:
        return []

    e = events.copy()
    e["date"] = pd.to_datetime(e["date"], errors="coerce", format="mixed", dayfirst=True)
    e = e.dropna(subset=["date"])
    e["amount"] = pd.to_numeric(e["amount"], errors="coerce").fillna(0.0)

    end = as_of + pd.Timedelta(days=days)
    is_xero = (
        e.get("source_system", pd.Series("", index=e.index)).astype(str).str.strip().str.lower().eq("xero")
        | e.get("event_type", pd.Series("", index=e.index)).astype(str).str.strip().str.lower().str.startswith("xero_")
    )
    window = e[((e["date"] >= as_of) & (e["date"] <= end)) | (is_xero & (e["date"] <= end))]
    window = window.sort_values("amount", ascending=False).head(top_n)

    results = []
    for _, row in window.iterrows():
        pid = _clean_text(row.get("product_id", ""))
        source_doc_no = _clean_text(row.get("source_doc_no"))
        counterparty_name = _clean_text(row.get("counterparty_name"))
        product_reference = _clean_text(row.get("product_reference")) or _clean_text(product_map.get(pid, ""))
        row_is_xero = _clean_text(row.get("source_system")).lower() == "xero" or _clean_text(row.get("event_type")).lower().startswith("xero_")
        label = product_reference or pid
        if row_is_xero and not label:
            if source_doc_no and counterparty_name:
                label = f"{source_doc_no} ({counterparty_name})"
            else:
                label = source_doc_no or counterparty_name
        results.append({
            "product_id": pid,
            "product_reference": product_reference,
            "amount": round(float(row["amount"]),2),
            "date": row["date"].date().isoformat(),
            "label": label,
            "source_doc_no": source_doc_no,
            "counterparty_name": counterparty_name,
        })
    return results

def plain_english_summary(status: str,
                          cash: float,
                          rec_60: float,
                          pay_60: float,
                          runway: float) -> List[str]:

    lines = []

    if status == "OK":
        lines.append("Business liquidity is stable.")
    elif status == "WATCH":
        lines.append("Liquidity is tightening. Monitor closely.")
    else:
        lines.append("Liquidity risk detected. Commitments should be paused.")

    lines.append(f"Cash available today: £{round(cash,0):,.0f}")
    lines.append(f"Next 60 days: £{round(rec_60,0):,.0f} expected in, £{round(pay_60,0):,.0f} expected out.")
    if isinstance(runway, (int, float)) and math.isinf(float(runway)):
        runway_text = "∞"
    else:
        runway_text = str(round(runway,0))
    lines.append(f"Current cash runway: approx. {runway_text} days.")

    return lines

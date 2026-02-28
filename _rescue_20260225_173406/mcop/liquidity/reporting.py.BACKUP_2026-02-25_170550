import pandas as pd
from typing import List, Dict

def governance_flag(liquidity_60: float, runway_days: float) -> str:
    if liquidity_60 < 0:
        return "BLOCK"
    if runway_days < 45:
        return "WATCH"
    return "OK"

def build_product_reference_map(products: pd.DataFrame) -> dict:
    if "Product Id" not in products.columns or "Product Reference" not in products.columns:
        return {}
    df = products[["Product Id","Product Reference"]].copy()
    df["Product Id"] = df["Product Id"].astype(str)
    return dict(zip(df["Product Id"], df["Product Reference"]))

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
    window = e[(e["date"] >= as_of) & (e["date"] <= end)]
    window = window.sort_values("amount", ascending=False).head(top_n)

    results = []
    for _, row in window.iterrows():
        pid = str(row.get("product_id",""))
        results.append({
            "product_id": pid,
            "product_reference": product_map.get(pid,""),
            "amount": round(float(row["amount"]),2),
            "date": row["date"].date().isoformat(),
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
    lines.append(f"Current cash runway: approx. {round(runway,0)} days.")

    return lines

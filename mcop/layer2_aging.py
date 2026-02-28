import datetime as dt

def _parse_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(date_str, fmt).date()
        except Exception:
            continue
    return None

def _f(x, default=0.0):
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace("£","").replace(",","").strip()
        return float(x)
    except Exception:
        return default

def compute_landed_aging(products, as_of_date, stress_liquidity_60d):
    """
    Computes landed unsold stock aging by value.

    Expected canonical headers (your exports):
      product_id, product_reference, landing_status, landing_date,
      bags_remaining, bag_size_kg, price_per_kg

    Still tolerates older headers if present.
    """
    buckets = {"0_30": 0.0, "30_60": 0.0, "60_90": 0.0, "90_plus": 0.0}
    total_unsold_value = 0.0
    top_traps = []

    for row in products or []:
        landing_status = str(row.get("landing_status", row.get("Landing Status", ""))).strip().lower()
        if landing_status != "landed":
            continue

        landing_date = _parse_date(row.get("landing_date", row.get("Landing Date")))
        if not landing_date:
            continue

        bag_size = _f(row.get("bag_size_kg", row.get("Bag Size", 0)), 0.0)
        bags_remaining = _f(row.get("bags_remaining", row.get("Bags Remaining", 0)), 0.0)

        # IMPORTANT: your products.csv uses price_per_kg
        price = _f(row.get("price_per_kg", row.get("price_gbp_kg", row.get("Price ¬£/kg", 0))), 0.0)

        if bags_remaining <= 0 or bag_size <= 0 or price <= 0:
            continue

        unsold_kg = bag_size * bags_remaining
        unsold_value = unsold_kg * price

        days = (as_of_date - landing_date).days
        total_unsold_value += unsold_value

        if days <= 30:
            buckets["0_30"] += unsold_value
        elif days <= 60:
            buckets["30_60"] += unsold_value
        elif days <= 90:
            buckets["60_90"] += unsold_value
        else:
            buckets["90_plus"] += unsold_value

        pid = str(row.get("product_id", row.get("Product Id", ""))).strip()
        pref = str(row.get("product_reference", row.get("Product Reference", ""))).strip()
        label = f"{pref} ({pid})" if (pref or pid) else "—"

        top_traps.append({
            "label": label,
            "days_since_landing": int(days),
            "unsold_value": round(float(unsold_value), 2),
        })

    top_traps = sorted(top_traps, key=lambda x: x["unsold_value"], reverse=True)[:5]

    liquidity_60d = max(float(stress_liquidity_60d or 0.0), 1.0)
    unsold_ratio = float(total_unsold_value) / liquidity_60d

    total_unsold = max(float(total_unsold_value), 1.0)
    pct_60_plus = float(buckets["60_90"] + buckets["90_plus"]) / total_unsold
    pct_90_plus = float(buckets["90_plus"]) / total_unsold

    if pct_90_plus > 0.30 or unsold_ratio > 1.2:
        flag = "BLOCK"
    elif unsold_ratio > 0.7 or pct_60_plus > 0.40:
        flag = "WATCH"
    else:
        flag = "OK"

    return {
        "total_unsold_value": round(float(total_unsold_value), 2),
        "buckets": {k: round(float(v), 2) for k, v in buckets.items()},
        "top_cash_traps": top_traps,
        "flag": flag,
    }

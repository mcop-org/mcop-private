from __future__ import annotations
import pandas as pd
import re
# --- header normalisation for costs exports (csv/tsv) ---
def _normalise_costs_columns(df):
    """Return a copy of df with columns normalised to snake_case (robust to hidden chars)."""
    if df is None:
        return df
    if not hasattr(df, "columns"):
        return df

    out = df.copy()

    def _clean(c: str) -> str:
        c = str(c)
        c = c.replace("\ufeff", "").replace("\u200b", "").replace("¬", "").strip()
        c = c.lower()
        c = re.sub(r"[^a-z0-9]+", "_", c)
        c = re.sub(r"_+", "_", c).strip("_")
        return c

    rename = {c: _clean(c) for c in out.columns}
    out = out.rename(columns=rename)

    # Common aliases (legacy -> canonical)
    aliases = {
        "productid": "product_id",
        "product_id": "product_id",
        "bag_size_kg": "bag_size",
        "bagsize": "bag_size",
        "bag_size": "bag_size",
        "cost_of_green_coffee_gbp_kg": "cost_of_green_coffee_gbp_kg",
        "cost_of_green_coffee_kg": "cost_of_green_coffee_gbp_kg",
        "cost_of_green_coffee": "cost_of_green_coffee_gbp_kg",
        "cost_farm_to_port_gbp_kg": "cost_farm_to_port_gbp_kg",
        "freight_cost_gbp_kg": "freight_cost_gbp_kg",
        "cost_uk_port_to_warehouse_gbp_kg": "cost_uk_port_to_warehouse_gbp_kg",
        "initial_payment_pct": "initial_payment_pct",
        "remaining_payment_pct": "remaining_payment_pct",
        "initial_payment_date": "initial_payment_date",
        "remaining_payment_date": "remaining_payment_date",
        "harvest_date": "harvest_date",
        "landing_date": "landing_date",
        "bags": "bags",
    }

    # apply aliases where exact keys exist
    for src, dst in list(aliases.items()):
        if src in out.columns and dst not in out.columns:
            out = out.rename(columns={src: dst})

    return out
# ------------------------------------------------------

# --- header normalisation for products exports (csv/tsv) ---
def _normalise_products_columns(df):
    """Return a copy of df with columns normalised to snake_case (robust to hidden chars)."""
    try:
        import pandas as pd
    except Exception:
        pd = None

    if df is None:
        return df

    # accept list[dict] as well
    if hasattr(df, "to_dict") and callable(getattr(df, "to_dict")):
        out = df.copy()
        cols = list(out.columns)
    else:
        # if it's not a DataFrame, just return as-is
        return df

    def _clean(c: str) -> str:
        c = str(c)
        # remove common hidden chars / odd glyphs seen in exports
        c = c.replace("\ufeff", "").replace("\u200b", "").replace("¬", "").strip()
        c = c.lower()
        c = re.sub(r"[^a-z0-9]+", "_", c)
        c = re.sub(r"_+", "_", c).strip("_")
        return c

    rename = {_c: _clean(_c) for _c in cols}
    out = out.rename(columns=rename)

    # Canonical aliases (keep data model consistent)
    # If you standardise exports later, you can delete these.
    if "bag_size_kg" in out.columns and "bag_size" not in out.columns:
        out = out.rename(columns={"bag_size_kg": "bag_size"})
    if "price_per_kg" in out.columns and "price_gbp_kg" not in out.columns:
        out = out.rename(columns={"price_per_kg": "price_gbp_kg"})

    return out
# --------------------------------------------------------


def _to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def _parse_dt(s):
    return pd.to_datetime(s, errors="coerce", format="mixed", dayfirst=True)

CORE_RE = re.compile(r"^core-\d+", re.IGNORECASE)

def is_core_reference(ref: str) -> bool:
    if ref is None:
        return False
    return bool(CORE_RE.match(str(ref).strip()))

def target_precommit(days_to_landing: float, is_core: bool) -> float:
    """
    Dynamic targets:
      Non-Core: >60:30% | 45-60:45% | 30-45:60% | <=30:70%
      Core:     >60:40% | 45-60:55% | 30-45:70% | <=30:80%
    """
    d = days_to_landing
    if is_core:
        if d > 60: return 0.40
        if d > 45: return 0.55
        if d > 30: return 0.70
        return 0.80
    else:
        if d > 60: return 0.30
        if d > 45: return 0.45
        if d > 30: return 0.60
        return 0.70

def build_cost_table(costs: pd.DataFrame) -> pd.DataFrame:
    costs = _normalise_costs_columns(costs)
    required = {
        "product_id","bag_size","bags",
        "cost_of_green_coffee_gbp_kg","cost_farm_to_port_gbp_kg","freight_cost_gbp_kg","cost_uk_port_to_warehouse_gbp_kg"
    }
    missing = required - set(costs.columns)
    if missing:
        raise ValueError(f"product_costs_protected.csv missing columns: {sorted(missing)}")

    c = costs.copy()
    c["product_id"] = c["product_id"].astype(str).str.strip()

    total_kg = _to_num(c["bag_size"]) * _to_num(c["bags"])
    landed_cost_per_kg = (
        _to_num(c["cost_of_green_coffee_gbp_kg"]) +
        _to_num(c["cost_farm_to_port_gbp_kg"]) +
        _to_num(c["freight_cost_gbp_kg"]) +
        _to_num(c["cost_uk_port_to_warehouse_gbp_kg"])
    )

    out = pd.DataFrame({
        "product_id": c["product_id"],
        "total_kg": total_kg,
        "landed_cost_per_kg": landed_cost_per_kg,
    })
    out["total_value_gbp"] = out["total_kg"] * out["landed_cost_per_kg"]
    return out

def build_reserved_kg(activity: pd.DataFrame) -> pd.DataFrame:
    activity = _normalise_activity_columns(activity)
    required = {"product_id","bags","bag_size_kg"}
    missing = required - set(activity.columns)
    if missing:
        raise ValueError(f"activity.csv missing columns: {sorted(missing)}")

    a = activity.copy()
    a["product_id"] = a["product_id"].astype(str).str.strip()
    a["reserved_kg"] = _to_num(a["bags"]) * _to_num(a["bag_size_kg"])
    return a.groupby("product_id", as_index=False)["reserved_kg"].sum()

def _normalise_activity_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Accept canonical CSV exports + legacy headers
    out = df.copy()

    def _canon(s: str) -> str:
        s = str(s).strip().lower()
        # remove common weird chars
        for ch in ["\ufeff", "\u200b", "¬", "£"]:
            s = s.replace(ch, "")
        s = s.replace("/", "_").replace(" ", "_")
        while "__" in s:
            s = s.replace("__", "_")
        return s

    out.columns = [_canon(c) for c in out.columns]

    alias = {
        "product_id": "product_id",
        "productid": "product_id",
        "product": "product_id",

        "bags": "bags",

        "bag_size": "bag_size_kg",
        "bag_size_kg": "bag_size_kg",
        "bagsz": "bag_size_kg",
        "bagsize": "bag_size_kg",

        "product_reference": "product_reference",
        "landing_date": "landing_date",
        "landing_status": "landing_status",

        "price_per_kg": "price_per_kg",
        "price_gbp_kg": "price_per_kg",
        "price_kg": "price_per_kg",

        "reservation_days": "reservation_days",
        "payment_days": "payment_days",
    }

    out = out.rename(columns={c: alias.get(c, c) for c in out.columns})
    return out

def compute_container_exposure(
    products: pd.DataFrame,
    costs: pd.DataFrame,
    activity: pd.DataFrame,
    as_of: pd.Timestamp,
    cash_on_hand: float,
    liquidity_60: float,
) -> dict:
    # --- header aliasing (accept legacy exports + new snake_case exports) ---
    products = _normalise_products_columns(products)
    # Back-compat: keep legacy column names for the existing logic below
    _legacy = {
        'Product Id': 'product_id',
        'Product Reference': 'product_reference',
        'Bag Size': 'bag_size',
        'Bags': 'bags',
        'Bags Remaining': 'bags_remaining',
        'Landing Status': 'landing_status',
        'Landing Date': 'landing_date',
        'Status': 'status',
    }
    for legacy, canon in _legacy.items():
        if legacy not in products.columns and canon in products.columns:
            products[legacy] = products[canon]
    # --------------------------------------------------------------

    p_required = {"Product Id","Product Reference","Bag Size","Bags","Bags Remaining","Landing Status","Status","Landing Date"}
    missing = p_required - set(products.columns)
    if missing:
        raise ValueError(f"products.csv missing columns: {sorted(missing)}")

    p = products.copy()
    p["Product Id"] = p["Product Id"].astype(str).str.strip()
    p["Product Reference"] = p["Product Reference"].astype(str)
    p["Landing Date"] = _parse_dt(p["Landing Date"])

    cost_tbl = build_cost_table(costs)
    res_tbl = build_reserved_kg(activity)

    df = p.merge(cost_tbl, on="product_id", how="left").merge(res_tbl, on="product_id", how="left")
    df["reserved_kg"] = df["reserved_kg"].fillna(0.0)

    df["remaining_kg"] = _to_num(df["Bags Remaining"]) * _to_num(df["Bag Size"])

    is_incoming = (df["Landing Status"].astype(str).str.strip().str.lower() == "incoming") | \
                  (df["Status"].astype(str).str.strip().str.lower() == "incoming")
    is_landed = df["Landing Status"].astype(str).str.strip().str.lower() == "landed"

    # Landed unsold capital
    landed_unsold = df[is_landed & (df["remaining_kg"] > 0)].copy()
    landed_unsold["capital_unsold_gbp"] = _to_num(landed_unsold["remaining_kg"]) * _to_num(landed_unsold["landed_cost_per_kg"])
    landed_capital_unsold = float(landed_unsold["capital_unsold_gbp"].sum())

    # Incoming
    incoming = df[is_incoming].copy()
    incoming["incoming_value_gbp"] = _to_num(incoming["total_kg"]) * _to_num(incoming["landed_cost_per_kg"])
    incoming_capital_total = float(incoming["incoming_value_gbp"].sum())

    incoming_total_kg = float(_to_num(incoming["total_kg"]).sum())
    incoming_reserved_kg = float(_to_num(incoming["reserved_kg"]).sum())
    overall_precommit = (incoming_reserved_kg / incoming_total_kg) if incoming_total_kg > 0 else 0.0
    overall_precommit = max(0.0, min(1.0, overall_precommit))

    incoming["uncommitted_kg"] = (_to_num(incoming["total_kg"]) - _to_num(incoming["reserved_kg"])).clip(lower=0.0)
    incoming["uncommitted_value_gbp"] = incoming["uncommitted_kg"] * _to_num(incoming["landed_cost_per_kg"])
    incoming_uncommitted_gbp = float(incoming["uncommitted_value_gbp"].sum())

    # ---- Dynamic precommit discipline ----
    incoming["is_core"] = incoming["Product Reference"].apply(is_core_reference)
    incoming["days_to_landing"] = (incoming["Landing Date"] - as_of).dt.days
    incoming["days_to_landing"] = pd.to_numeric(incoming["days_to_landing"], errors="coerce").fillna(9999)

    incoming["precommit_pct_product"] = (
        _to_num(incoming["reserved_kg"]) /
        _to_num(incoming["total_kg"]).replace({0: pd.NA})
    ).fillna(0.0)

    incoming["target_precommit"] = incoming.apply(
        lambda r: target_precommit(float(r["days_to_landing"]), bool(r["is_core"])),
        axis=1
    )
    incoming["below_target"] = incoming["precommit_pct_product"] < incoming["target_precommit"]

    value_below = float(incoming.loc[incoming["below_target"], "incoming_value_gbp"].sum())
    pct_value_below = (value_below / incoming_capital_total) if incoming_capital_total > 0 else 0.0

    # Hard breach only when genuinely late-stage: <= 14 days AND >20% below target
    incoming["near_landing_hard_breach"] = (incoming["days_to_landing"] <= 14) & (
        incoming["precommit_pct_product"] < (incoming["target_precommit"] - 0.20)
    )
    any_near_landing_breach = bool(incoming["near_landing_hard_breach"].any())

    # ---- Overlap risk (45-day window) ----
    overlap_window_days = 45
    incoming_dates = incoming.dropna(subset=["Landing Date"]).sort_values("Landing Date")
    vals = incoming_dates[["Landing Date","incoming_value_gbp","Product Id","Product Reference"]].reset_index(drop=True)

    max_window_sum = 0.0
    max_window_start = None
    max_window_count = 0

    for i in range(len(vals)):
        start = vals.loc[i, "Landing Date"]
        end = start + pd.Timedelta(days=overlap_window_days)
        window = vals[(vals["Landing Date"] >= start) & (vals["Landing Date"] <= end)]
        window_sum = float(window["incoming_value_gbp"].sum())
        if window_sum > max_window_sum:
            max_window_sum = window_sum
            max_window_start = start
            max_window_count = int(len(window))

    overlap_flag = bool(max_window_count >= 2 and max_window_sum > 0)

    overlap_window_details = {
        "window_days": overlap_window_days,
        "window_start": max_window_start.date().isoformat() if isinstance(max_window_start, pd.Timestamp) else "",
        "window_incoming_value_gbp": round(float(max_window_sum), 2),
        "sku_count": int(max_window_count),
    }

    # ---- Capital Deployment Ratio (CDR) ----
    # Uncommitted incoming capital as % of base 60-day liquidity
    liq60 = float(liquidity_60 or 0.0)
    if liq60 <= 0:
        cdr = None
        deployment_flag = "BLOCK"
    else:
        cdr = float(incoming_uncommitted_gbp) / liq60
        if cdr < 0.25:
            deployment_flag = "OK"
        elif cdr < 0.50:
            deployment_flag = "WATCH"
        elif cdr < 0.75:
            deployment_flag = "WATCH"  # "aggressive", but still recoverable
        else:
            deployment_flag = "BLOCK"

    # ---- Exposure flag (disciplined) ----
    if cash_on_hand <= 0:
        exposure_flag = "BLOCK"
    elif incoming_capital_total > 1.5 * cash_on_hand:
        exposure_flag = "BLOCK"
    else:
        exposure_flag = "OK"
        if incoming_capital_total > 1.2 * cash_on_hand:
            exposure_flag = "WATCH"
        elif incoming_capital_total > 0 and pct_value_below > 0.25:
            exposure_flag = "WATCH"
        elif overlap_flag and incoming_capital_total > 0:
            exposure_flag = "WATCH"
        if any_near_landing_breach:
            exposure_flag = "BLOCK"

    # ---- Top incoming by value ----
    top_incoming = incoming.sort_values("incoming_value_gbp", ascending=False).head(5)
    breakdown_top_incoming = []
    for _, r in top_incoming.iterrows():
        breakdown_top_incoming.append({
            "product_id": str(r["Product Id"]),
            "product_reference": str(r["Product Reference"]),
            "is_core": bool(r["is_core"]),
            "landing_date": r["Landing Date"].date().isoformat() if pd.notna(r["Landing Date"]) else "",
            "days_to_landing": int(r["days_to_landing"]) if pd.notna(r["days_to_landing"]) else None,
            "incoming_value_gbp": round(float(r["incoming_value_gbp"]), 2),
            "precommit_pct_product": round(float(r["precommit_pct_product"]), 3),
            "target_precommit": round(float(r["target_precommit"]), 3),
            "below_target": bool(r["below_target"]),
        })

    # ---- Top at-risk (biggest shortfall, value-weighted) ----
    incoming["shortfall_pct"] = (incoming["target_precommit"] - incoming["precommit_pct_product"]).clip(lower=0.0)
    incoming["shortfall_value_gbp"] = incoming["incoming_value_gbp"] * incoming["shortfall_pct"]

    at_risk = incoming[incoming["shortfall_pct"] > 0].copy()
    at_risk = at_risk.sort_values("shortfall_value_gbp", ascending=False).head(5)

    top_at_risk_incoming = []
    for _, r in at_risk.iterrows():
        top_at_risk_incoming.append({
            "product_id": str(r["Product Id"]),
            "product_reference": str(r["Product Reference"]),
            "is_core": bool(r["is_core"]),
            "landing_date": r["Landing Date"].date().isoformat() if pd.notna(r["Landing Date"]) else "",
            "days_to_landing": int(r["days_to_landing"]) if pd.notna(r["days_to_landing"]) else None,
            "precommit_pct_product": round(float(r["precommit_pct_product"]), 3),
            "target_precommit": round(float(r["target_precommit"]), 3),
            "shortfall_pct": round(float(r["shortfall_pct"]), 3),
            "shortfall_value_gbp": round(float(r["shortfall_value_gbp"]), 2),
        })

    return {
        "exposure_flag": exposure_flag,

        "landed_capital_unsold_gbp": round(landed_capital_unsold, 2),
        "incoming_capital_total_gbp": round(incoming_capital_total, 2),

        "incoming_reserved_kg": round(incoming_reserved_kg, 2),
        "incoming_total_kg": round(incoming_total_kg, 2),
        "incoming_precommitted_pct": round(overall_precommit, 3),
        "incoming_uncommitted_gbp": round(incoming_uncommitted_gbp, 2),

        "capital_deployment_ratio": None if cdr is None else round(float(cdr), 3),
        "deployment_flag": deployment_flag,

        "dynamic_precommit": {
            "value_below_target_gbp": round(value_below, 2),
            "pct_incoming_value_below_target": round(float(pct_value_below), 3),
            "any_near_landing_hard_breach": bool(any_near_landing_breach),
        },

        "overlap_flag": bool(overlap_flag),
        "overlap_window_details": overlap_window_details,

        "breakdown_top_incoming": breakdown_top_incoming,
        "top_at_risk_incoming": top_at_risk_incoming,
    }

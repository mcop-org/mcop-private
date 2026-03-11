from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
import re

def parse_dt(x):
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def _parse_one(value):
        if value is None:
            return pd.NaT
        text = str(value).strip()
        if not text:
            return pd.NaT
        if iso_pattern.match(text):
            return pd.to_datetime(text, errors="coerce", format="%Y-%m-%d")
        return pd.to_datetime(text, errors="coerce", format="mixed", dayfirst=True)

    if isinstance(x, pd.Series):
        return x.apply(_parse_one)
    if isinstance(x, pd.Index):
        return pd.DatetimeIndex([_parse_one(v) for v in x])
    if isinstance(x, (list, tuple)):
        return pd.DatetimeIndex([_parse_one(v) for v in x])
    return _parse_one(x)

def require_cols(df: pd.DataFrame, cols: set[str], name: str):
    missing = cols - set(df.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _normalise_costs_columns(df):
    import re

    df = df.copy()

    def _clean(c):
        # handle BOM / odd unicode, normalize whitespace, then snake_case
        c = str(c).replace("\ufeff", "").replace("\u00a0", " ")
        c = re.sub(r"\s+", " ", c).strip()
        c = c.replace(" ", "_").lower()
        return c

    df.columns = [_clean(c) for c in df.columns]

    # Accept older exports (legacy) and newer exports (canonical)
    legacy_to_new = {
        "product_id": "product_id",
        "productid": "product_id",

        "harvest_date": "harvest_date",
        "landing_date": "landing_date",

        "bag_size": "bag_size",
        "bag_size_kg": "bag_size",
        "bagsize": "bag_size",

        "bags": "bags",

        "cost_of_green_coffee_£/kg": "cost_of_green_coffee_gbp_kg",
        "cost_of_green_coffee_gbp_kg": "cost_of_green_coffee_gbp_kg",

        "cost_farm_to_port_£/kg": "cost_farm_to_port_gbp_kg",
        "cost_farm_to_port_gbp_kg": "cost_farm_to_port_gbp_kg",

        "freight_cost_£/kg": "freight_cost_gbp_kg",
        "freight_cost_gbp_kg": "freight_cost_gbp_kg",

        "cost_uk_port_to_warehouse_£/kg": "cost_uk_port_to_warehouse_gbp_kg",
        "cost_uk_port_to_warehouse_gbp_kg": "cost_uk_port_to_warehouse_gbp_kg",

        "initial_payment_%": "initial_payment_pct",
        "initial_payment_pct": "initial_payment_pct",
        "initial_payment_date": "initial_payment_date",

        "remaining_payment_%": "remaining_payment_pct",
        "remaining_payment_pct": "remaining_payment_pct",
        "remaining_payment_date": "remaining_payment_date",
    }

    df = df.rename(columns={k: v for k, v in legacy_to_new.items() if k in df.columns})

    # Last-resort: if bag_size still missing but we have something close, coerce it
    if "bag_size" not in df.columns:
        for c in list(df.columns):
            if "bag" in c and "size" in c:
                df = df.rename(columns={c: "bag_size"})
                break

    return df
def latest_as_of(cash_position: pd.DataFrame) -> tuple[pd.Timestamp, float]:
    require_cols(cash_position, {"date", "cash_on_hand"}, "cash_position.csv")
    cp = cash_position.copy()
    cp["date"] = parse_dt(cp["date"])
    cp = cp.dropna(subset=["date"]).sort_values("date")
    if cp.empty:
        raise ValueError("cash_position.csv: could not parse any valid dates in 'date' column")
    latest = cp.iloc[-1]
    return pd.to_datetime(latest["date"]).normalize(), float(latest["cash_on_hand"])

def bucket_sum(events: pd.DataFrame, as_of: pd.Timestamp, days: int) -> float:
    if events is None or events.empty:
        return 0.0
    e = events.copy()
    e["date"] = parse_dt(e["date"])
    e = e.dropna(subset=["date"])
    e["amount"] = pd.to_numeric(e["amount"], errors="coerce").fillna(0.0)
    end = as_of + pd.Timedelta(days=days)
    return float(e[(e["date"] >= as_of) & (e["date"] <= end)]["amount"].sum())

def conservative_daily_burn_from_cash_position(cash_position: pd.DataFrame, lookback_days: int = 90) -> float:
    """
    Phase-1 conservative burn proxy:
    - Uses cash_on_hand history only (no cashflow statement required)
    - Finds worst (largest) cash drop over any ~30-day window in the last ~lookback_days
    - Converts to daily burn: worst_drop / 30
    """
    cp = cash_position.copy()
    require_cols(cp, {"date", "cash_on_hand"}, "cash_position.csv")
    cp["date"] = parse_dt(cp["date"])
    cp["cash_on_hand"] = pd.to_numeric(cp["cash_on_hand"], errors="coerce")
    cp = cp.dropna(subset=["date", "cash_on_hand"]).sort_values("date")
    if cp.empty or len(cp) < 2:
        # Fallback conservative default if insufficient history
        return 0.0

    as_of = cp.iloc[-1]["date"]
    cutoff = as_of - pd.Timedelta(days=lookback_days)
    cp = cp[cp["date"] >= cutoff]
    if len(cp) < 2:
        return 0.0

    # For each point, compare to nearest point >= 30 days earlier
    worst_drop = 0.0
    for i in range(len(cp)):
        d_i = cp.iloc[i]["date"]
        cash_i = float(cp.iloc[i]["cash_on_hand"])
        target = d_i - pd.Timedelta(days=30)

        # find closest earlier row on/before target
        earlier = cp[cp["date"] <= target]
        if earlier.empty:
            continue
        cash_prev = float(earlier.iloc[-1]["cash_on_hand"])
        drop = cash_prev - cash_i  # positive means cash fell
        if drop > worst_drop:
            worst_drop = drop

    # If cash never fell over a 30d window, set burn small (avoid divide by zero)
    daily_burn = worst_drop / 30.0 if worst_drop > 0 else 0.0
    return daily_burn

COST_REQUIRED = {
    "product_id",
    "harvest_date",
    "landing_date",
    "bag_size",
    "bags",
    "cost_of_green_coffee_gbp_kg",
    "cost_farm_to_port_gbp_kg",
    "freight_cost_gbp_kg",
    "cost_uk_port_to_warehouse_gbp_kg",
    "initial_payment_pct",
    "initial_payment_date",
    "remaining_payment_pct",
    "remaining_payment_date",
}
def build_payables_from_costs(costs: pd.DataFrame) -> pd.DataFrame:
    costs = _normalise_costs_columns(costs)
    require_cols(costs, COST_REQUIRED, "product_costs_protected.csv")
    c = costs.copy()
    c["product_id"] = c["product_id"].astype(str).str.strip()

    num_cols = [
        "bag_size","bags",
        "cost_of_green_coffee_gbp_kg","cost_farm_to_port_gbp_kg","freight_cost_gbp_kg","cost_uk_port_to_warehouse_gbp_kg",
        "initial_payment_pct","remaining_payment_pct"
    ]
    for col in num_cols:
        c[col] = pd.to_numeric(c[col], errors="coerce").fillna(0.0)

    total_kg = c["bag_size"] * c["bags"]
    landed_cost_per_kg = (
        c["cost_of_green_coffee_gbp_kg"] +
        c["cost_farm_to_port_gbp_kg"] +
        c["freight_cost_gbp_kg"] +
        c["cost_uk_port_to_warehouse_gbp_kg"]
    )
    total_cost = total_kg * landed_cost_per_kg

    init_pct = c["initial_payment_pct"] / 100.0
    rem_pct  = c["remaining_payment_pct"] / 100.0

    init_dates = parse_dt(c["initial_payment_date"])
    rem_dates  = parse_dt(c["remaining_payment_date"])

    init_df = pd.DataFrame({
        "date": init_dates,
        "amount": total_cost * init_pct,
        "event_type": "initial_payment",
        "product_id": c["product_id"],
    })
    rem_df = pd.DataFrame({
        "date": rem_dates,
        "amount": total_cost * rem_pct,
        "event_type": "remaining_payment",
        "product_id": c["product_id"],
    })

    out = pd.concat([init_df, rem_df], ignore_index=True)
    out = out.dropna(subset=["date"])
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce").fillna(0.0)
    return out

ACTIVITY_REQUIRED = {"product_id","bags","bag_size_kg","price_per_kg","reservation_days","payment_days","landing_date"}

def build_receivables_from_activity(activity: pd.DataFrame, delay_buffer_days: int = 7) -> pd.DataFrame:
    require_cols(activity, ACTIVITY_REQUIRED, "activity.csv")
    a = activity.copy()
    a["product_id"] = a["product_id"].astype(str).str.strip()
    a["landing_date"] = parse_dt(a["landing_date"])
    a = a.dropna(subset=["landing_date"])

    for col in ["bags","bag_size_kg","price_per_kg","reservation_days","payment_days"]:
        a[col] = pd.to_numeric(a[col], errors="coerce").fillna(0.0)

    events = []
    for _, row in a.iterrows():
        L: pd.Timestamp = pd.to_datetime(row["landing_date"]).normalize()
        R = float(row["reservation_days"])
        P = float(row["payment_days"])
        value = float(row["bags"] * row["bag_size_kg"] * row["price_per_kg"])
        if value <= 0:
            continue

        if R < 30:
            tranches = [(0.50, 1.00)]
        else:
            tranches = [(0.20, 0.40), (0.50, 0.35), (0.85, 0.25)]

        for frac_time, frac_amt in tranches:
            release_days = int(round(R * frac_time))
            cash_in_days = release_days + int(round(P)) + delay_buffer_days
            events.append({
                "date": L + pd.Timedelta(days=cash_in_days),
                "amount": value * frac_amt,
                "event_type": "receivable",
                "product_id": row["product_id"],
            })

    out = pd.DataFrame(events)
    if out.empty:
        return pd.DataFrame(columns=["date","amount","event_type","product_id"])
    out["date"] = parse_dt(out["date"])
    out = out.dropna(subset=["date"])
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce").fillna(0.0)
    return out

def stress_receivables(
    receivables: pd.DataFrame,
    as_of: pd.Timestamp,
    slowdown_shift_30_to_60: float = 0.20,
    extra_delay_shift: float = 0.15,
    inflow_haircut: float = 0.02,
) -> pd.DataFrame:
    if receivables is None or receivables.empty:
        return receivables

    r = receivables.copy()
    r["date"] = parse_dt(r["date"])
    r = r.dropna(subset=["date"])
    r["amount"] = pd.to_numeric(r["amount"], errors="coerce").fillna(0.0)

    d30 = as_of + pd.Timedelta(days=30)
    d60 = as_of + pd.Timedelta(days=60)

    within_30 = (r["date"] >= as_of) & (r["date"] <= d30)
    r30 = r[within_30].copy()
    r_other = r[~within_30].copy()

    r30_shift = r30.copy()
    r30_shift["amount"] *= slowdown_shift_30_to_60
    r30["amount"] *= (1 - slowdown_shift_30_to_60)
    r30_shift["date"] = r30_shift["date"] + pd.Timedelta(days=30)

    r2 = pd.concat([r_other, r30, r30_shift], ignore_index=True)

    within_60 = (r2["date"] >= as_of) & (r2["date"] <= d60)
    r60 = r2[within_60].copy()
    r2_other = r2[~within_60].copy()

    r60_shift = r60.copy()
    r60_shift["amount"] *= extra_delay_shift
    r60["amount"] *= (1 - extra_delay_shift)
    r60_shift["date"] = r60_shift["date"] + pd.Timedelta(days=60)

    r3 = pd.concat([r2_other, r60, r60_shift], ignore_index=True)
    r3["amount"] *= (1 - inflow_haircut)
    return r3

@dataclass(frozen=True)
class LiquiditySnapshot:
    as_of: str
    cash_on_hand: float
    receivables_30: float
    receivables_60: float
    payables_30: float
    payables_60: float
    liquidity_30: float
    liquidity_60: float
    runway_days: float

    def to_dict(self) -> dict:
        return {
            "as_of": self.as_of,
            "cash_on_hand": round(self.cash_on_hand, 2),
            "receivables_30": round(self.receivables_30, 2),
            "receivables_60": round(self.receivables_60, 2),
            "payables_30": round(self.payables_30, 2),
            "payables_60": round(self.payables_60, 2),
            "liquidity_30": round(self.liquidity_30, 2),
            "liquidity_60": round(self.liquidity_60, 2),
            "runway_days": round(self.runway_days, 1),
        }

def compute_liquidity_snapshot(cash_position: pd.DataFrame, payables: pd.DataFrame, receivables: pd.DataFrame) -> LiquiditySnapshot:
    as_of, cash = latest_as_of(cash_position)

    pay_30 = bucket_sum(payables, as_of, 30)
    pay_60 = bucket_sum(payables, as_of, 60)
    rec_30 = bucket_sum(receivables, as_of, 30)
    rec_60 = bucket_sum(receivables, as_of, 60)

    liq_30 = cash + rec_30 - pay_30
    liq_60 = cash + rec_60 - pay_60

    daily_burn = conservative_daily_burn_from_cash_position(cash_position)
    runway = (cash / daily_burn) if daily_burn and daily_burn > 0 else float("inf")

    return LiquiditySnapshot(
        as_of=as_of.date().isoformat(),
        cash_on_hand=cash,
        receivables_30=rec_30,
        receivables_60=rec_60,
        payables_30=pay_30,
        payables_60=pay_60,
        liquidity_30=liq_30,
        liquidity_60=liq_60,
        runway_days=runway,
    )

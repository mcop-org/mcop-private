
from __future__ import annotations

import re
import pandas as pd

def _clean_header(h: str) -> str:
    h = str(h)
    # remove invisible/odd chars that break matching
    h = h.replace("\ufeff", "")  # BOM
    h = h.replace("¬", "")
    h = h.replace("£", "gbp")
    h = h.strip()
    h = re.sub(r"\s+", "_", h)
    h = h.replace("/", "_per_")
    h = re.sub(r"[^a-zA-Z0-9_]+", "_", h)
    h = re.sub(r"_+", "_", h).strip("_")
    return h.lower()

def _rename_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    cols = {_clean_header(c): c for c in df.columns}
    out = df.copy()
    for src_clean, dst in mapping.items():
        if src_clean in cols:
            out = out.rename(columns={cols[src_clean]: dst})
    # also clean any columns not mapped (keeps them stable)
    out.columns = [ _clean_header(c) if c not in out.columns else c for c in out.columns ]
    return out

def normalise_products(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "product_id": "product_id",
        "productid": "product_id",
        "product_id_": "product_id",
        "product_id__": "product_id",
        "product_id__1": "product_id",
        "product_id__2": "product_id",
        "product_id__3": "product_id",
        "product_id__4": "product_id",
        "product_id__5": "product_id",
        "product_id__6": "product_id",
        "product_id__7": "product_id",
        "product_id__8": "product_id",
        "product_id__9": "product_id",
        "product_id__10": "product_id",
        "product_id__11": "product_id",
        "product_id__12": "product_id",
        "product_id__13": "product_id",
        "product_id__14": "product_id",
        "product_id__15": "product_id",
        "product_id__16": "product_id",
        "product_id__17": "product_id",
        "product_id__18": "product_id",
        "product_id__19": "product_id",
        "product_id__20": "product_id",
        "product_id__21": "product_id",
        "product_id__22": "product_id",
        "product_id__23": "product_id",
        "product_id__24": "product_id",
        "product_id__25": "product_id",
        "product_id__26": "product_id",
        "product_id__27": "product_id",
        "product_id__28": "product_id",
        "product_id__29": "product_id",
        "product_id__30": "product_id",
        "product_id__31": "product_id",
        "product_id__32": "product_id",
        "product_id__33": "product_id",
        "product_id__34": "product_id",
        "product_id__35": "product_id",
        "product_id__36": "product_id",
        "product_id__37": "product_id",
        "product_id__38": "product_id",
        "product_id__39": "product_id",
        "product_id__40": "product_id",
        "product_id__41": "product_id",
        "product_id__42": "product_id",
        "product_id__43": "product_id",
        "product_id__44": "product_id",
        "product_id__45": "product_id",
        "product_id__46": "product_id",
        "product_id__47": "product_id",
        "product_id__48": "product_id",
        "product_id__49": "product_id",
        "product_id__50": "product_id",

        "product_id": "product_id",
        "productid": "product_id",
        "product_id": "product_id",
        "product_id": "product_id",
        "product_id": "product_id",

        "product_id": "product_id",
        "product_reference": "product_reference",
        "productreference": "product_reference",

        "bag_size": "bag_size_kg",
        "bag_size_kg": "bag_size_kg",
        "bagsize": "bag_size_kg",

        "bags": "bags",
        "bags_remaining": "bags_remaining",

        "price_per_kg": "price_per_kg",
        "price_gbp_kg": "price_per_kg",
        "price_gbp_per_kg": "price_per_kg",
        "price_gbp_kg_": "price_per_kg",

        "landing_status": "landing_status",
        "landing_date": "landing_date",
        "status": "status",
    }
    out = _rename_columns(df, mapping)

    # Provide compatibility aliases to reduce downstream breakage:
    # if some code expects price_gbp_kg or bag_size, keep them too.
    if "price_per_kg" in out.columns and "price_gbp_kg" not in out.columns:
        out["price_gbp_kg"] = out["price_per_kg"]
    if "bag_size_kg" in out.columns and "bag_size" not in out.columns:
        out["bag_size"] = out["bag_size_kg"]
    return out

def normalise_activity(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "product_id": "product_id",
        "productid": "product_id",
        "product_reference": "product_reference",

        "bags": "bags",
        "bag_size": "bag_size_kg",
        "bag_size_kg": "bag_size_kg",

        "price_per_kg": "price_per_kg",
        "price_gbp_kg": "price_per_kg",

        "reservation_days": "reservation_days",
        "payment_days": "payment_days",
        "landing_status": "landing_status",
        "landing_date": "landing_date",
    }
    out = _rename_columns(df, mapping)
    if "bag_size_kg" in out.columns and "bag_size" not in out.columns:
        out["bag_size"] = out["bag_size_kg"]
    return out

def normalise_costs(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "product_id": "product_id",
        "productid": "product_id",

        "bag_size": "bag_size_kg",
        "bag_size_kg": "bag_size_kg",
        "bags": "bags",

        "harvest_date": "harvest_date",
        "landing_date": "landing_date",

        "cost_of_green_coffee_gbp_per_kg": "cost_of_green_coffee_gbp_kg",
        "cost_of_green_coffee_gbp_kg": "cost_of_green_coffee_gbp_kg",
        "cost_farm_to_port_gbp_per_kg": "cost_farm_to_port_gbp_kg",
        "cost_farm_to_port_gbp_kg": "cost_farm_to_port_gbp_kg",
        "freight_cost_gbp_per_kg": "freight_cost_gbp_kg",
        "freight_cost_gbp_kg": "freight_cost_gbp_kg",
        "cost_uk_port_to_warehouse_gbp_per_kg": "cost_uk_port_to_warehouse_gbp_kg",
        "cost_uk_port_to_warehouse_gbp_kg": "cost_uk_port_to_warehouse_gbp_kg",

        "initial_payment_pct": "initial_payment_pct",
        "initial_payment_date": "initial_payment_date",
        "remaining_payment_pct": "remaining_payment_pct",
        "remaining_payment_date": "remaining_payment_date",
    }
    out = _rename_columns(df, mapping)

    # compatibility aliases
    if "bag_size_kg" in out.columns and "bag_size" not in out.columns:
        out["bag_size"] = out["bag_size_kg"]
    return out

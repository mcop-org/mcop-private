import pandas as pd

def load_product_ref_map(products_df: pd.DataFrame) -> dict:
    if products_df is None or not hasattr(products_df, "columns"):
        return {}
    cols = {str(c).strip(): c for c in products_df.columns}
    id_col = cols.get("product_id") or cols.get("Product Id")
    ref_col = cols.get("product_reference") or cols.get("Product Reference")
    if id_col is None or ref_col is None:
        return {}
    out = {}
    for pid, pref in zip(products_df[id_col].astype(str), products_df[ref_col].astype(str)):
        pid = str(pid).strip()
        pref = str(pref).strip()
        if pid:
            out[pid] = pref
    return out

def decorate_event(ev: dict, ref_map: dict):
    if not isinstance(ev, dict):
        return
    pid = ev.get("product_id")
    if not pid:
        return
    pref = ref_map.get(str(pid).strip(), "")
    if pref:
        ev["product_reference"] = pref
        # standard label: E-11 (P1021)
        ev["label"] = f"{pref} ({pid})"

def decorate_rows(rows: list, ref_map: dict):
    if not isinstance(rows, list):
        return
    for r in rows:
        if not isinstance(r, dict):
            continue
        pid = r.get("product_id")
        if not pid:
            continue
        pref = ref_map.get(str(pid).strip(), "")
        if pref:
            r["product_reference"] = pref

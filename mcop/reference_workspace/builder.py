from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


RESERVATION_NOTE = (
    "Reservation completed means all products within the reservation have been released."
)
LANDED_AGING_BUCKETS = (
    ("0-30", 0, 30),
    ("31-60", 31, 60),
    ("61-90", 61, 90),
    ("91-180", 91, 180),
    ("181-270", 181, 270),
    ("270+", 271, None),
)


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _to_float_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([0.0] * len(frame), index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def _normalise_date_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([pd.NaT] * len(frame), index=frame.index, dtype="datetime64[ns]")
    return pd.to_datetime(frame[column], errors="coerce", format="%Y-%m-%d")


def _to_numeric_or_nan_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([float("nan")] * len(frame), index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _first_text(values: Iterable[object]) -> str:
    cleaned = sorted({_clean_text(value) for value in values if _clean_text(value)})
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "mixed"


def _normalise_iso_date(value: object) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    parsed = pd.to_datetime(text, errors="coerce", format="%Y-%m-%d")
    if pd.isna(parsed):
        return ""
    return parsed.date().isoformat()


def _pick_latest_snapshot_date(*date_groups: Iterable[object]) -> str:
    candidates: list[str] = []
    for values in date_groups:
        for value in values:
            normalised = _normalise_iso_date(value)
            if normalised:
                candidates.append(normalised)
    return sorted(candidates)[-1] if candidates else ""


def _aging_bucket_for_days(days_since_landing: float | None) -> str:
    if days_since_landing is None:
        return "Date unavailable"
    for label, minimum, maximum in LANDED_AGING_BUCKETS:
        if days_since_landing < minimum:
            continue
        if maximum is None or days_since_landing <= maximum:
            return label
    return "Date unavailable"


def _status_summary(parts: list[str]) -> str:
    cleaned = [part for part in parts if part]
    return "; ".join(cleaned) if cleaned else "Complete"


def _available_bags_by_reference(products: pd.DataFrame) -> dict[str, float]:
    if products.empty or "bags_available" not in products.columns:
        return {}

    available = products.copy()
    if "product_reference" not in available.columns:
        available["product_reference"] = ""
    available["product_reference"] = available["product_reference"].map(_clean_text)
    available = available[available["product_reference"] != ""].copy()
    if available.empty:
        return {}

    available["bags_available"] = _to_float_series(available, "bags_available")
    grouped = available.groupby("product_reference", sort=True, as_index=False)["bags_available"].sum()
    return {
        _clean_text(row["product_reference"]): round(float(row["bags_available"]), 4)
        for _, row in grouped.iterrows()
        if _clean_text(row["product_reference"])
    }


def _landed_selector_refs(products: pd.DataFrame) -> list[str]:
    if products.empty:
        return []

    landed = products.copy()
    if "product_reference" not in landed.columns:
        landed["product_reference"] = ""
    if "landing_status" not in landed.columns:
        landed["landing_status"] = ""

    landed["product_reference"] = landed["product_reference"].map(_clean_text)
    landed["landing_status"] = landed["landing_status"].map(_clean_text).str.lower()
    landed = landed[
        (landed["product_reference"] != "")
        & (landed["landing_status"] == "landed")
    ].copy()
    if landed.empty:
        return []

    return sorted({reference for reference in landed["product_reference"].tolist() if reference})


def _product_reference_fallbacks(products: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    if products.empty:
        return {}, {}

    product_lookup: dict[str, str] = {}
    status_groups: dict[str, list[str]] = {}
    for _, row in products.iterrows():
        product_id = _clean_text(row.get("product_id"))
        reference = _clean_text(row.get("product_reference"))
        landing_status = _clean_text(row.get("landing_status")).lower()
        if product_id and reference:
            product_lookup[product_id] = reference
        if reference and landing_status:
            status_groups.setdefault(reference, []).append(landing_status)

    reference_lookup = {
        reference: _first_text(values)
        for reference, values in status_groups.items()
        if _first_text(values)
    }
    return product_lookup, reference_lookup


def _metric_bags_and_kg(rows: pd.DataFrame, bag_column: str) -> dict[str, object]:
    if rows.empty:
        return {
            "bags": 0.0,
            "bags_available": True,
            "kg": 0.0,
            "kg_available": True,
        }

    bag_values = _to_numeric_or_nan_series(rows, bag_column)
    size_values = _to_numeric_or_nan_series(rows, "bag_size_kg")
    bags_available = bool(bag_values.notna().all())
    kg_available = bool(bag_values.notna().all() and size_values.notna().all())

    bags_value = round(float(bag_values.fillna(0.0).sum()), 4) if bags_available else 0.0
    kg_value = round(float((bag_values * size_values).fillna(0.0).sum()), 4) if kg_available else 0.0
    return {
        "bags": bags_value,
        "bags_available": bags_available,
        "kg": kg_value,
        "kg_available": kg_available,
    }


def _classify_stock_health(
    incoming_metric: dict[str, object],
    landed_metric: dict[str, object],
    landed_available_metric: dict[str, object],
) -> str:
    if not (
        incoming_metric["bags_available"]
        and landed_metric["bags_available"]
        and landed_available_metric["bags_available"]
    ):
        return "Data Incomplete"

    incoming_bags = float(incoming_metric["bags"])
    landed_bags = float(landed_metric["bags"])
    landed_available_bags = float(landed_available_metric["bags"])

    if incoming_bags > 0 and landed_bags <= 0:
        return "Mostly Incoming"
    if landed_available_bags > 0 and landed_available_bags >= incoming_bags:
        return "Landed Build-Up"
    if incoming_bags > landed_bags:
        return "Mostly Incoming"
    return "Balanced"


def _build_product_reference_intelligence(
    products: pd.DataFrame,
    selector_refs: list[str],
) -> tuple[list[dict], list[dict]]:
    if products.empty:
        product_summary = [
            {
                "product_reference": reference,
                "incoming_bags": 0.0,
                "incoming_bags_available": True,
                "incoming_kg": 0.0,
                "incoming_kg_available": True,
                "landed_bags": 0.0,
                "landed_bags_available": True,
                "landed_kg": 0.0,
                "landed_kg_available": True,
                "landed_available_bags": 0.0,
                "landed_available_bags_available": False,
                "landed_available_kg": 0.0,
                "landed_available_kg_available": False,
                "stock_health": "Data Incomplete",
            }
            for reference in selector_refs
        ]
        return product_summary, []

    product_rows = products.copy()
    for column in ("product_id", "product_reference", "landing_status", "landing_date", "warehouse", "status"):
        if column not in product_rows.columns:
            product_rows[column] = pd.NA

    product_rows["product_reference"] = product_rows["product_reference"].map(_clean_text)
    product_rows["product_id"] = product_rows["product_id"].map(_clean_text)
    product_rows["landing_status"] = product_rows["landing_status"].map(_clean_text).str.lower()
    product_rows["landing_date"] = product_rows["landing_date"].map(_clean_text)
    product_rows["warehouse"] = product_rows["warehouse"].map(_clean_text)
    product_rows["status"] = product_rows["status"].map(_clean_text)
    product_rows = product_rows[product_rows["product_reference"] != ""].copy()

    product_rows["bags_num"] = _to_numeric_or_nan_series(product_rows, "bags")
    product_rows["bags_available_num"] = _to_numeric_or_nan_series(product_rows, "bags_available")
    product_rows["bag_size_kg_num"] = _to_numeric_or_nan_series(product_rows, "bag_size_kg")
    product_rows["total_kg_num"] = product_rows["bags_num"] * product_rows["bag_size_kg_num"]
    product_rows["available_kg_num"] = product_rows["bags_available_num"] * product_rows["bag_size_kg_num"]
    product_rows["landed_available_sort"] = product_rows["bags_available_num"].fillna(0.0)
    product_rows["concern_rank"] = 2
    product_rows.loc[
        (product_rows["landing_status"] == "landed") & (product_rows["landed_available_sort"] > 0),
        "concern_rank",
    ] = 0
    product_rows.loc[
        (product_rows["landing_status"] == "landed") & (product_rows["landed_available_sort"] <= 0),
        "concern_rank",
    ] = 1

    product_rows = product_rows.sort_values(
        ["product_reference", "concern_rank", "landing_date", "warehouse", "product_id"],
        kind="stable",
        na_position="last",
    )

    product_details = [
        {
            "product_reference": _clean_text(row["product_reference"]),
            "product_id": _clean_text(row["product_id"]),
            "landing_status": _clean_text(row["landing_status"]).title(),
            "landing_date": _clean_text(row["landing_date"]),
            "warehouse": _clean_text(row["warehouse"]),
            "bags": round(float(row["bags_num"]), 4) if pd.notna(row["bags_num"]) else None,
            "bag_size_kg": round(float(row["bag_size_kg_num"]), 4) if pd.notna(row["bag_size_kg_num"]) else None,
            "total_kg": round(float(row["total_kg_num"]), 4) if pd.notna(row["bags_num"]) and pd.notna(row["bag_size_kg_num"]) else None,
            "bags_available": round(float(row["bags_available_num"]), 4) if pd.notna(row["bags_available_num"]) else None,
            "available_kg": round(float(row["available_kg_num"]), 4) if pd.notna(row["bags_available_num"]) and pd.notna(row["bag_size_kg_num"]) else None,
        }
        for _, row in product_rows.iterrows()
    ]

    summary_rows: list[dict] = []
    summary_refs = sorted({_clean_text(row["product_reference"]) for _, row in product_rows.iterrows() if _clean_text(row["product_reference"])})
    all_refs = sorted({*selector_refs, *summary_refs})
    for reference in all_refs:
        group = product_rows[product_rows["product_reference"] == reference].copy()
        incoming = group[group["landing_status"] == "incoming"].copy()
        landed = group[group["landing_status"] == "landed"].copy()
        landed_available = landed.copy()

        incoming_metric = _metric_bags_and_kg(incoming, "bags")
        landed_metric = _metric_bags_and_kg(landed, "bags")
        landed_available_metric = _metric_bags_and_kg(landed_available, "bags_available")
        summary_rows.append(
            {
                "product_reference": reference,
                "incoming_bags": incoming_metric["bags"],
                "incoming_bags_available": incoming_metric["bags_available"],
                "incoming_kg": incoming_metric["kg"],
                "incoming_kg_available": incoming_metric["kg_available"],
                "landed_bags": landed_metric["bags"],
                "landed_bags_available": landed_metric["bags_available"],
                "landed_kg": landed_metric["kg"],
                "landed_kg_available": landed_metric["kg_available"],
                "landed_available_bags": landed_available_metric["bags"],
                "landed_available_bags_available": landed_available_metric["bags_available"],
                "landed_available_kg": landed_available_metric["kg"],
                "landed_available_kg_available": landed_available_metric["kg_available"],
                "stock_health": _classify_stock_health(
                    incoming_metric,
                    landed_metric,
                    landed_available_metric,
                ),
            }
        )

    return summary_rows, product_details


def _build_landed_stock_intelligence(
    products: pd.DataFrame,
    activity_snapshot_date: str,
) -> tuple[dict, list[dict], list[dict], list[dict], list[dict]]:
    if products.empty:
        return (
            {
                "as_of_date": activity_snapshot_date,
                "landed_bags": 0.0,
                "unsold_landed_bags": 0.0,
                "unsold_landed_kg": 0.0,
                "unsold_landed_kg_available": True,
                "aged_180_plus_bags": 0.0,
                "warehouses_exposed": 0,
                "unsold_landed_value_gbp": 0.0,
                "unsold_landed_value_available": True,
                "value_completeness_status": "No landed stock rows.",
            },
            [
                {"aging_bucket": label, "unsold_bags": 0.0}
                for label, _, _ in LANDED_AGING_BUCKETS
            ],
            [],
            [],
            [],
        )

    landed_rows = products.copy()
    for column in (
        "product_reference",
        "product_id",
        "landing_status",
        "landing_date",
        "warehouse",
        "bags",
        "bags_available",
        "bag_size_kg",
        "price_per_kg",
    ):
        if column not in landed_rows.columns:
            landed_rows[column] = pd.NA

    landed_rows["product_reference"] = landed_rows["product_reference"].map(_clean_text)
    landed_rows["product_id"] = landed_rows["product_id"].map(_clean_text)
    landed_rows["landing_status"] = landed_rows["landing_status"].map(_clean_text).str.lower()
    landed_rows["landing_date"] = landed_rows["landing_date"].map(_normalise_iso_date)
    landed_rows["warehouse"] = landed_rows["warehouse"].map(_clean_text)
    landed_rows["bags_num"] = _to_numeric_or_nan_series(landed_rows, "bags")
    landed_rows["bags_available_num"] = _to_numeric_or_nan_series(landed_rows, "bags_available")
    landed_rows["bag_size_kg_num"] = _to_numeric_or_nan_series(landed_rows, "bag_size_kg")
    landed_rows["price_per_kg_num"] = _to_numeric_or_nan_series(landed_rows, "price_per_kg")
    landed_rows = landed_rows[landed_rows["landing_status"] == "landed"].copy()

    as_of_date = _pick_latest_snapshot_date(
        [activity_snapshot_date],
        landed_rows["landing_date"].tolist(),
    )

    landed_bags = round(float(landed_rows["bags_num"].fillna(0.0).sum()), 4)
    landed_rows["unsold_active"] = landed_rows["bags_available_num"].notna() & (landed_rows["bags_available_num"] > 0)
    landed_rows["unsold_bags_value"] = landed_rows["bags_available_num"].where(landed_rows["unsold_active"], 0.0)
    landed_rows["kg_complete"] = landed_rows["unsold_active"] & landed_rows["bag_size_kg_num"].notna()
    landed_rows["unsold_kg_value"] = (
        landed_rows["bags_available_num"] * landed_rows["bag_size_kg_num"]
    ).where(landed_rows["kg_complete"], 0.0)
    landed_rows["value_complete"] = landed_rows["kg_complete"] & landed_rows["price_per_kg_num"].notna()
    landed_rows["unsold_value_gbp_value"] = (
        landed_rows["unsold_kg_value"] * landed_rows["price_per_kg_num"]
    ).where(landed_rows["value_complete"], 0.0)

    as_of_ts = pd.to_datetime(as_of_date, errors="coerce", format="%Y-%m-%d")
    landing_ts = pd.to_datetime(landed_rows["landing_date"], errors="coerce", format="%Y-%m-%d")
    if pd.isna(as_of_ts):
        landed_rows["days_since_landing_num"] = pd.Series(
            [float("nan")] * len(landed_rows), index=landed_rows.index, dtype="float64"
        )
    else:
        landed_rows["days_since_landing_num"] = (as_of_ts - landing_ts).dt.days.astype("float64")
        landed_rows.loc[landed_rows["days_since_landing_num"] < 0, "days_since_landing_num"] = float("nan")
    landed_rows["aging_bucket"] = landed_rows["days_since_landing_num"].map(
        lambda value: _aging_bucket_for_days(None if pd.isna(value) else float(value))
    )

    incomplete_value_rows = landed_rows[landed_rows["unsold_active"] & ~landed_rows["value_complete"]]
    value_completeness_status = "Complete"
    if landed_rows["unsold_active"].sum() == 0:
        value_completeness_status = "No unsold landed rows."
    elif not incomplete_value_rows.empty:
        value_completeness_status = (
            f"Unavailable on {len(incomplete_value_rows)} unsold landed row(s) due to missing kg or price."
        )

    summary = {
        "as_of_date": as_of_date,
        "landed_bags": landed_bags,
        "unsold_landed_bags": round(float(landed_rows["unsold_bags_value"].sum()), 4),
        "unsold_landed_kg": round(float(landed_rows["unsold_kg_value"].sum()), 4),
        "unsold_landed_kg_available": bool(
            landed_rows[landed_rows["unsold_active"]].empty
            or landed_rows.loc[landed_rows["unsold_active"], "kg_complete"].all()
        ),
        "aged_180_plus_bags": round(
            float(
                landed_rows[
                    landed_rows["unsold_active"]
                    & landed_rows["days_since_landing_num"].notna()
                    & (landed_rows["days_since_landing_num"] >= 181)
                ]["bags_available_num"].sum()
            ),
            4,
        ),
        "warehouses_exposed": int(
            landed_rows[landed_rows["unsold_active"]]["warehouse"].map(_clean_text).replace("", pd.NA).dropna().nunique()
        ),
        "unsold_landed_value_gbp": round(float(landed_rows["unsold_value_gbp_value"].sum()), 2),
        "unsold_landed_value_available": bool(
            landed_rows[landed_rows["unsold_active"]].empty
            or landed_rows.loc[landed_rows["unsold_active"], "value_complete"].all()
        ),
        "value_completeness_status": value_completeness_status,
    }

    aging_chart: list[dict] = []
    aging_source = landed_rows[
        landed_rows["unsold_active"] & landed_rows["days_since_landing_num"].notna()
    ].copy()
    for label, _, _ in LANDED_AGING_BUCKETS:
        bucket_rows = aging_source[aging_source["aging_bucket"] == label]
        aging_chart.append(
            {
                "aging_bucket": label,
                "unsold_bags": round(float(bucket_rows["bags_available_num"].sum()), 4),
            }
        )

    unsold_rows = landed_rows[landed_rows["unsold_active"]].copy()
    warehouse_groups = (
        unsold_rows.assign(warehouse_key=unsold_rows["warehouse"].where(unsold_rows["warehouse"] != "", "Unknown"))
        .groupby("warehouse_key", sort=True, as_index=False)[
            ["bags_available_num", "unsold_kg_value"]
        ]
        .sum()
        .rename(
            columns={
                "warehouse_key": "warehouse",
                "bags_available_num": "unsold_bags",
                "unsold_kg_value": "unsold_kg",
            }
        )
    )
    warehouse_groups = warehouse_groups.sort_values(
        ["unsold_bags", "warehouse"],
        ascending=[False, True],
        kind="stable",
    )
    warehouse_exposure = [
        {
            "warehouse": _clean_text(row["warehouse"]) or "Unknown",
            "unsold_bags": round(float(row["unsold_bags"]), 4),
            "unsold_kg": round(float(row["unsold_kg"]), 4),
        }
        for _, row in warehouse_groups.iterrows()
        if float(row["unsold_bags"]) > 0
    ]

    reference_groups = (
        unsold_rows.assign(
            reference_key=unsold_rows["product_reference"].where(
                unsold_rows["product_reference"] != "", "Unknown"
            )
        )
        .groupby("reference_key", sort=True, as_index=False)[
            ["bags_available_num", "unsold_kg_value"]
        ]
        .sum()
        .rename(
            columns={
                "reference_key": "product_reference",
                "bags_available_num": "unsold_bags",
                "unsold_kg_value": "unsold_kg",
            }
        )
    )
    reference_groups = reference_groups.sort_values(
        ["unsold_bags", "product_reference"],
        ascending=[False, True],
        kind="stable",
    )
    reference_exposure = [
        {
            "product_reference": _clean_text(row["product_reference"]) or "Unknown",
            "unsold_bags": round(float(row["unsold_bags"]), 4),
            "unsold_kg": round(float(row["unsold_kg"]), 4),
        }
        for _, row in reference_groups.iterrows()
        if float(row["unsold_bags"]) > 0
    ]

    detail_rows = landed_rows[
        landed_rows["bags_available_num"].isna() | (landed_rows["bags_available_num"] > 0)
    ].copy()
    detail_rows["data_status"] = [
        _status_summary(
            [
                "Unsold bags unavailable" if pd.isna(row["bags_available_num"]) else "",
                (
                    "Unsold kg unavailable"
                    if bool(row["unsold_active"]) and not bool(row["kg_complete"])
                    else ""
                ),
                (
                    "Unsold value unavailable"
                    if bool(row["unsold_active"]) and bool(row["kg_complete"]) and not bool(row["value_complete"])
                    else ""
                ),
                "Landing date unavailable" if pd.isna(row["days_since_landing_num"]) else "",
            ]
        )
        for _, row in detail_rows.iterrows()
    ]
    detail_rows = detail_rows.sort_values(
        ["days_since_landing_num", "bags_available_num", "product_reference", "product_id"],
        ascending=[False, False, True, True],
        kind="stable",
        na_position="last",
    )
    landed_details = [
        {
            "product_reference": _clean_text(row["product_reference"]),
            "product_id": _clean_text(row["product_id"]),
            "warehouse": _clean_text(row["warehouse"]),
            "landing_date": _clean_text(row["landing_date"]),
            "days_since_landing": (
                int(row["days_since_landing_num"]) if pd.notna(row["days_since_landing_num"]) else None
            ),
            "aging_bucket": _clean_text(row["aging_bucket"]),
            "landed_bags": round(float(row["bags_num"]), 4) if pd.notna(row["bags_num"]) else None,
            "unsold_bags": (
                round(float(row["bags_available_num"]), 4) if pd.notna(row["bags_available_num"]) else None
            ),
            "unsold_kg": round(float(row["unsold_kg_value"]), 4) if bool(row["kg_complete"]) else None,
            "unsold_value_gbp": (
                round(float(row["unsold_value_gbp_value"]), 2) if bool(row["value_complete"]) else None
            ),
            "data_status": _clean_text(row["data_status"]),
        }
        for _, row in detail_rows.iterrows()
    ]

    return summary, aging_chart, warehouse_exposure, reference_exposure, landed_details


def _latest_rows_per_reservation_product(reservations: pd.DataFrame) -> pd.DataFrame:
    keyed = reservations.copy()
    keyed["product_key"] = keyed["product_id"].map(_clean_text)
    keyed.loc[keyed["product_key"] == "", "product_key"] = keyed.loc[
        keyed["product_key"] == "", "product_reference"
    ].map(_clean_text)
    keyed["reservation_product_key"] = keyed["reservation_key"] + "||" + keyed["product_key"]
    return keyed.groupby("reservation_product_key", dropna=False, as_index=False).tail(1).copy()


def _empty_dataset(
    selector_refs: list[str],
    landed_selector_refs: list[str],
    landing_status_by_reference: dict[str, str],
    available_bags_by_reference: dict[str, float],
) -> dict:
    return {
        "snapshot_date": "",
        "default_reference": selector_refs[0] if selector_refs else "",
        "default_landed_reference": landed_selector_refs[0] if landed_selector_refs else "",
        "notes": [RESERVATION_NOTE],
        "reference_options": [
            {
                "product_reference": reference,
                "has_reservations": False,
                "landing_status": landing_status_by_reference.get(reference, "").title(),
            }
            for reference in selector_refs
        ],
        "landed_reference_options": [
            {"product_reference": reference}
            for reference in landed_selector_refs
        ],
        "reference_summary": [
            {
                "product_reference": reference,
                "landing_status": landing_status_by_reference.get(reference, "").title(),
                "is_landed": landing_status_by_reference.get(reference, "") == "landed",
                "reservation_row_count": 0,
                "client_count": 0,
                "reserved_bags": 0.0,
                "bags_available": available_bags_by_reference.get(reference, 0.0),
                "reserved_pct": 0.0,
                "reserved_kg": 0.0,
                "reserved_value_gbp": 0.0,
            }
            for reference in selector_refs
        ],
        "reservation_details": [],
        "product_reference_summary": [
            {
                "product_reference": reference,
                "incoming_bags": 0.0,
                "incoming_bags_available": True,
                "incoming_kg": 0.0,
                "incoming_kg_available": True,
                "landed_bags": 0.0,
                "landed_bags_available": True,
                "landed_kg": 0.0,
                "landed_kg_available": True,
                "landed_available_bags": 0.0,
                "landed_available_bags_available": False,
                "landed_available_kg": 0.0,
                "landed_available_kg_available": False,
                "stock_health": "Data Incomplete",
            }
            for reference in selector_refs
        ],
        "product_landing_profile": [],
        "landed_stock_summary": {
            "as_of_date": "",
            "landed_bags": 0.0,
            "unsold_landed_bags": 0.0,
            "unsold_landed_kg": 0.0,
            "unsold_landed_kg_available": True,
            "aged_180_plus_bags": 0.0,
            "warehouses_exposed": 0,
            "unsold_landed_value_gbp": 0.0,
            "unsold_landed_value_available": True,
            "value_completeness_status": "No landed stock rows.",
        },
        "landed_stock_aging": [
            {"aging_bucket": label, "unsold_bags": 0.0}
            for label, _, _ in LANDED_AGING_BUCKETS
        ],
        "landed_stock_warehouse_exposure": [],
        "landed_stock_reference_exposure": [],
        "landed_stock_details": [],
    }


def build_reference_workspace_dataset(activity: pd.DataFrame, products: pd.DataFrame) -> dict:
    product_ref_by_id, landing_status_by_reference = _product_reference_fallbacks(products)
    available_bags_by_reference = _available_bags_by_reference(products)

    selector_refs = sorted(
        {
            _clean_text(row.get("product_reference"))
            for _, row in products.iterrows()
            if _clean_text(row.get("product_reference"))
        }
    )
    landed_selector_refs = _landed_selector_refs(products)

    reservations = activity.copy()
    if reservations.empty:
        empty_dataset = _empty_dataset(
            selector_refs,
            landed_selector_refs,
            landing_status_by_reference,
            available_bags_by_reference,
        )
        product_summary, product_details = _build_product_reference_intelligence(
            products,
            selector_refs,
        )
        (
            landed_summary,
            landed_aging,
            landed_warehouse,
            landed_reference,
            landed_details,
        ) = _build_landed_stock_intelligence(products, empty_dataset["snapshot_date"])
        empty_dataset["product_reference_summary"] = product_summary
        empty_dataset["product_landing_profile"] = product_details
        empty_dataset["landed_stock_summary"] = landed_summary
        empty_dataset["landed_stock_aging"] = landed_aging
        empty_dataset["landed_stock_warehouse_exposure"] = landed_warehouse
        empty_dataset["landed_stock_reference_exposure"] = landed_reference
        empty_dataset["landed_stock_details"] = landed_details
        return empty_dataset

    reservations["request_type"] = (
        reservations.get("request_type", pd.Series(dtype="object")).astype(str).str.lower().str.strip()
    )
    reservations["request_status"] = (
        reservations.get("request_status", pd.Series(dtype="object")).astype(str).str.lower().str.strip()
    )
    reservations = reservations[
        (reservations["request_type"] == "reservation")
        & (reservations["request_status"] != "rejected")
    ].copy()

    for column in (
        "id_booking",
        "id_request",
        "product_id",
        "product_reference",
        "client_id",
        "company_name",
        "contact_first_name",
        "contact_last_name",
        "landing_status",
        "landing_date",
        "warehouse",
        "request_date",
        "approval_date",
        "amendment_date",
    ):
        if column not in reservations.columns:
            reservations[column] = pd.NA

    if reservations.empty:
        empty_dataset = _empty_dataset(
            selector_refs,
            landed_selector_refs,
            landing_status_by_reference,
            available_bags_by_reference,
        )
        product_summary, product_details = _build_product_reference_intelligence(
            products,
            selector_refs,
        )
        (
            landed_summary,
            landed_aging,
            landed_warehouse,
            landed_reference,
            landed_details,
        ) = _build_landed_stock_intelligence(products, empty_dataset["snapshot_date"])
        empty_dataset["product_reference_summary"] = product_summary
        empty_dataset["product_landing_profile"] = product_details
        empty_dataset["landed_stock_summary"] = landed_summary
        empty_dataset["landed_stock_aging"] = landed_aging
        empty_dataset["landed_stock_warehouse_exposure"] = landed_warehouse
        empty_dataset["landed_stock_reference_exposure"] = landed_reference
        empty_dataset["landed_stock_details"] = landed_details
        return empty_dataset

    reservations["reservation_key"] = reservations["id_booking"].where(
        reservations["id_booking"].notna() & (reservations["id_booking"].astype(str).str.strip() != ""),
        reservations["id_request"],
    )
    reservations = reservations.dropna(subset=["reservation_key"]).copy()
    reservations["reservation_key"] = reservations["reservation_key"].astype(str).str.strip()
    reservations = reservations[reservations["reservation_key"] != ""].copy()

    reservations["request_dt"] = _normalise_date_column(reservations, "request_date")
    reservations["approval_dt"] = _normalise_date_column(reservations, "approval_date")
    reservations["amendment_dt"] = _normalise_date_column(reservations, "amendment_date")
    reservations["effective_dt"] = (
        reservations["amendment_dt"]
        .fillna(reservations["approval_dt"])
        .fillna(reservations["request_dt"])
    )

    reservations["bags"] = _to_float_series(reservations, "bags")
    reservations["bags_remaining"] = _to_float_series(reservations, "bags_remaining")
    reservations["bag_size_kg"] = _to_float_series(reservations, "bag_size_kg")
    reservations["price_per_kg"] = _to_float_series(reservations, "price_per_kg")

    reservations = reservations.sort_values(
        ["reservation_key", "effective_dt", "id_request"],
        kind="stable",
        na_position="last",
    )
    latest = _latest_rows_per_reservation_product(reservations)
    latest = latest.sort_values(
        ["reservation_key", "effective_dt", "id_request"],
        kind="stable",
        na_position="last",
    )
    if "reservation_product_key" in latest.columns:
        latest = latest.drop(columns=["reservation_product_key"])
    if "product_key" in latest.columns:
        latest = latest.drop(columns=["product_key"])

    latest["product_id"] = latest["product_id"].map(_clean_text)
    latest["product_reference"] = latest["product_reference"].map(_clean_text)
    latest.loc[latest["product_reference"] == "", "product_reference"] = (
        latest.loc[latest["product_reference"] == "", "product_id"].map(product_ref_by_id).fillna("")
    )
    latest["landing_status"] = latest["landing_status"].map(_clean_text).str.lower()
    latest.loc[latest["landing_status"] == "", "landing_status"] = (
        latest.loc[latest["landing_status"] == "", "product_reference"]
        .map(landing_status_by_reference)
        .fillna("")
    )

    latest["effective_bags"] = latest["bags_remaining"].where(latest["bags_remaining"] > 0, latest["bags"])
    latest["reserved_kg"] = latest["effective_bags"] * latest["bag_size_kg"]
    latest["reserved_value_gbp"] = latest["reserved_kg"] * latest["price_per_kg"]

    detail_rows = latest.copy()
    detail_rows["landing_date"] = detail_rows["landing_date"].map(_clean_text)
    detail_rows["warehouse"] = detail_rows["warehouse"].map(_clean_text)
    detail_rows["company_name"] = detail_rows["company_name"].map(_clean_text)
    detail_rows["client_id"] = detail_rows["client_id"].map(_clean_text)
    detail_rows["contact_first_name"] = detail_rows["contact_first_name"].map(_clean_text)
    detail_rows["contact_last_name"] = detail_rows["contact_last_name"].map(_clean_text)
    detail_rows["id_request"] = detail_rows["id_request"].map(_clean_text)
    detail_rows["reservation_key"] = detail_rows["reservation_key"].map(_clean_text)
    detail_rows["request_date"] = detail_rows["request_date"].map(_clean_text)
    detail_rows["approval_date"] = detail_rows["approval_date"].map(_clean_text)
    detail_rows["amendment_date"] = detail_rows["amendment_date"].map(_clean_text)

    detail_rows = detail_rows.sort_values(
        ["product_reference", "company_name", "request_status", "effective_dt", "id_request"],
        kind="stable",
        na_position="last",
    )

    reservation_details = [
        {
            "product_reference": _clean_text(row["product_reference"]),
            "reservation_key": _clean_text(row["reservation_key"]),
            "id_request": _clean_text(row["id_request"]),
            "client_id": _clean_text(row["client_id"]),
            "company_name": _clean_text(row["company_name"]),
            "contact_first_name": _clean_text(row["contact_first_name"]),
            "contact_last_name": _clean_text(row["contact_last_name"]),
            "request_status": _clean_text(row["request_status"]).title(),
            "request_date": _clean_text(row["request_date"]),
            "approval_date": _clean_text(row["approval_date"]),
            "amendment_date": _clean_text(row["amendment_date"]),
            "landing_status": _clean_text(row["landing_status"]).title(),
            "landing_date": _clean_text(row["landing_date"]),
            "warehouse": _clean_text(row["warehouse"]),
            "bags": round(float(row["bags"]), 4),
            "bags_remaining": round(float(row["bags_remaining"]), 4),
            "effective_bags": round(float(row["effective_bags"]), 4),
            "bag_size_kg": round(float(row["bag_size_kg"]), 4),
            "reserved_kg": round(float(row["reserved_kg"]), 4),
            "price_per_kg": round(float(row["price_per_kg"]), 4),
            "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
        }
        for _, row in detail_rows.iterrows()
        if _clean_text(row["product_reference"])
    ]

    summary_rows: list[dict] = []
    for reference, group in latest.groupby("product_reference", sort=True):
        reference_text = _clean_text(reference)
        if not reference_text:
            continue

        client_keys = {
            key
            for key in (
                _clean_text(row.get("client_id")) or _clean_text(row.get("company_name"))
                for _, row in group.iterrows()
            )
            if key
        }
        landing_status = _first_text(group["landing_status"])
        summary_rows.append(
            {
                "product_reference": reference_text,
                "landing_status": landing_status.title() if landing_status else "",
                "is_landed": landing_status == "landed",
                "reservation_row_count": int(len(group)),
                "client_count": int(len(client_keys)),
                "reserved_bags": round(float(group["effective_bags"].sum()), 4),
                "reserved_kg": round(float(group["reserved_kg"].sum()), 4),
                "reserved_value_gbp": round(float(group["reserved_value_gbp"].sum()), 2),
            }
        )

    summary_rows = sorted(summary_rows, key=lambda row: row["product_reference"])
    summary_refs = {row["product_reference"] for row in summary_rows}
    selector_refs = sorted({*summary_refs, *selector_refs})
    for row in summary_rows:
        denominator = float(row["reserved_bags"]) + float(available_bags_by_reference.get(row["product_reference"], 0.0))
        row["bags_available"] = available_bags_by_reference.get(row["product_reference"], 0.0)
        row["reserved_pct"] = round((float(row["reserved_bags"]) / denominator) if denominator > 0 else 0.0, 4)
    for reference in selector_refs:
        if reference in summary_refs:
            continue
        summary_rows.append(
            {
                "product_reference": reference,
                "landing_status": landing_status_by_reference.get(reference, "").title(),
                "is_landed": landing_status_by_reference.get(reference, "") == "landed",
                "reservation_row_count": 0,
                "client_count": 0,
                "reserved_bags": 0.0,
                "bags_available": available_bags_by_reference.get(reference, 0.0),
                "reserved_pct": 0.0,
                "reserved_kg": 0.0,
                "reserved_value_gbp": 0.0,
            }
        )
    summary_rows = sorted(summary_rows, key=lambda row: row["product_reference"])

    reference_options = [
        {
            "product_reference": reference,
            "has_reservations": reference in summary_refs,
            "landing_status": (
                next(
                    (
                        row["landing_status"]
                        for row in summary_rows
                        if row["product_reference"] == reference and row["landing_status"]
                    ),
                    landing_status_by_reference.get(reference, "").title(),
                )
            ),
        }
        for reference in selector_refs
    ]
    landed_reference_options = [
        {"product_reference": reference}
        for reference in landed_selector_refs
    ]

    snapshot_candidates = latest["effective_dt"].dropna().sort_values(kind="stable")
    snapshot_date = ""
    if not snapshot_candidates.empty:
        snapshot_date = snapshot_candidates.iloc[-1].date().isoformat()

    default_reference = ""
    if summary_rows:
        default_reference = summary_rows[0]["product_reference"]
    elif selector_refs:
        default_reference = selector_refs[0]
    default_landed_reference = landed_selector_refs[0] if landed_selector_refs else ""

    product_summary, product_details = _build_product_reference_intelligence(
        products,
        selector_refs,
    )
    (
        landed_summary,
        landed_aging,
        landed_warehouse,
        landed_reference,
        landed_details,
    ) = _build_landed_stock_intelligence(products, snapshot_date)

    return {
        "snapshot_date": snapshot_date,
        "default_reference": default_reference,
        "default_landed_reference": default_landed_reference,
        "notes": [RESERVATION_NOTE],
        "reference_options": reference_options,
        "landed_reference_options": landed_reference_options,
        "reference_summary": summary_rows,
        "reservation_details": reservation_details,
        "product_reference_summary": product_summary,
        "product_landing_profile": product_details,
        "landed_stock_summary": landed_summary,
        "landed_stock_aging": landed_aging,
        "landed_stock_warehouse_exposure": landed_warehouse,
        "landed_stock_reference_exposure": landed_reference,
        "landed_stock_details": landed_details,
    }

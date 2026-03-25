from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


RESERVATION_NOTE = (
    "Reservation completed means all products within the reservation have been released."
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


def _first_text(values: Iterable[object]) -> str:
    cleaned = sorted({_clean_text(value) for value in values if _clean_text(value)})
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "mixed"


def _product_reference_fallbacks(products: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    if products.empty:
        return {}, {}

    product_lookup: dict[str, str] = {}
    reference_lookup: dict[str, str] = {}
    for _, row in products.iterrows():
        product_id = _clean_text(row.get("product_id"))
        reference = _clean_text(row.get("product_reference"))
        landing_status = _clean_text(row.get("landing_status")).lower()
        if product_id and reference:
            product_lookup[product_id] = reference
        if reference and landing_status and reference not in reference_lookup:
            reference_lookup[reference] = landing_status
    return product_lookup, reference_lookup


def _latest_rows_per_reservation_product(reservations: pd.DataFrame) -> pd.DataFrame:
    keyed = reservations.copy()
    keyed["product_key"] = keyed["product_id"].map(_clean_text)
    keyed.loc[keyed["product_key"] == "", "product_key"] = keyed.loc[
        keyed["product_key"] == "", "product_reference"
    ].map(_clean_text)
    keyed["reservation_product_key"] = keyed["reservation_key"] + "||" + keyed["product_key"]
    return keyed.groupby("reservation_product_key", dropna=False, as_index=False).tail(1).copy()


def build_reference_workspace_dataset(activity: pd.DataFrame, products: pd.DataFrame) -> dict:
    product_ref_by_id, landing_status_by_reference = _product_reference_fallbacks(products)

    reservations = activity.copy()
    if reservations.empty:
        selector_refs = sorted(
            {
                _clean_text(row.get("product_reference"))
                for _, row in products.iterrows()
                if _clean_text(row.get("product_reference"))
            }
        )
        return {
            "snapshot_date": "",
            "default_reference": selector_refs[0] if selector_refs else "",
            "notes": [RESERVATION_NOTE],
            "reference_options": [
                {
                    "product_reference": reference,
                    "has_reservations": False,
                    "landing_status": landing_status_by_reference.get(reference, ""),
                }
                for reference in selector_refs
            ],
            "reference_summary": [],
            "reservation_details": [],
        }

    reservations["request_type"] = reservations.get("request_type", pd.Series(dtype="object")).astype(str).str.lower().str.strip()
    reservations["request_status"] = reservations.get("request_status", pd.Series(dtype="object")).astype(str).str.lower().str.strip()
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
        selector_refs = sorted(
            {
                _clean_text(row.get("product_reference"))
                for _, row in products.iterrows()
                if _clean_text(row.get("product_reference"))
            }
        )
        return {
            "snapshot_date": "",
            "default_reference": selector_refs[0] if selector_refs else "",
            "notes": [RESERVATION_NOTE],
            "reference_options": [
                {
                    "product_reference": reference,
                    "has_reservations": False,
                    "landing_status": landing_status_by_reference.get(reference, ""),
                }
                for reference in selector_refs
            ],
            "reference_summary": [],
            "reservation_details": [],
        }

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
    selector_refs = sorted(
        {
            *summary_refs,
            *{
                _clean_text(row.get("product_reference"))
                for _, row in products.iterrows()
                if _clean_text(row.get("product_reference"))
            },
        }
    )

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

    snapshot_candidates = latest["effective_dt"].dropna().sort_values(kind="stable")
    snapshot_date = ""
    if not snapshot_candidates.empty:
        snapshot_date = snapshot_candidates.iloc[-1].date().isoformat()

    default_reference = ""
    if summary_rows:
        default_reference = summary_rows[0]["product_reference"]
    elif selector_refs:
        default_reference = selector_refs[0]

    return {
        "snapshot_date": snapshot_date,
        "default_reference": default_reference,
        "notes": [RESERVATION_NOTE],
        "reference_options": reference_options,
        "reference_summary": summary_rows,
        "reservation_details": reservation_details,
    }

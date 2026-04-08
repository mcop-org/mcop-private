from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path

import pandas as pd

from mcop.reference_workspace.geography_resolver import (
    RESOLVER_VERSION as GEOGRAPHY_RESOLVER_VERSION,
    OfflineGeographyResolver,
)
from mcop.reference_workspace.uk_postcode_service import UKPostcodeServiceConfig


RESERVATION_NOTE = (
    "Reservation completed means all products within the reservation have been released."
)
ACTION_QUEUE_NEAR_EXPIRY_DAYS = 7
LANDED_AGING_BUCKETS = (
    ("0-30", 0, 30),
    ("31-60", 31, 60),
    ("61-90", 61, 90),
    ("91-180", 91, 180),
    ("181-270", 181, 270),
    ("270+", 271, None),
)
CLIENT_GEOGRAPHY_COORDINATE_CACHE = Path(__file__).with_name("client_geography_coordinates.json")


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _normalise_geo_part(value: object) -> str:
    return " ".join(_clean_text(value).split()).casefold()


def _normalise_postcode_part(value: object) -> str:
    return "".join(_clean_text(value).split()).casefold()


def _client_geography_exact_key(country: object, city: object, postcode: object) -> str:
    return "||".join(
        [
            _normalise_geo_part(country),
            _normalise_geo_part(city),
            _normalise_postcode_part(postcode),
        ]
    )


def _client_geography_city_key(country: object, city: object) -> str:
    return "||".join(
        [
            _normalise_geo_part(country),
            _normalise_geo_part(city),
        ]
    )


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


def _action_bucket_and_priority(
    is_breached: bool,
    is_near_expiry: bool,
    is_landed_not_approved: bool,
    is_landed_not_released: bool,
) -> tuple[str, str, int]:
    if is_breached:
        return "Breached", "P1 Breached", 1
    if is_near_expiry:
        return "Near Expiry", "P2 Near Expiry", 2
    if is_landed_not_approved:
        return "Landed Not Approved", "P3 Landed Not Approved", 3
    if is_landed_not_released:
        return "Landed Not Released", "P4 Landed Not Released", 4
    return "Open Exposure", "P5 Open Exposure", 5


def _client_key(row: pd.Series) -> str:
    client_id = _clean_text(row.get("client_id"))
    if client_id:
        return client_id
    return _clean_text(row.get("company_name"))


def _empty_client_summary() -> dict:
    return {
        "clients_with_current_exposure": 0,
        "total_current_reserved_value_gbp": 0.0,
        "total_current_reserved_value_available": True,
        "largest_client_company_name": "",
        "largest_client_id": "",
        "largest_client_reserved_value_gbp": 0.0,
        "largest_client_reserved_value_available": True,
        "clients_concentrated_in_one_reference": 0,
    }


def _empty_client_geography_summary() -> dict:
    return {
        "mapped_clients": 0,
        "unmapped_clients": 0,
        "countries_covered": 0,
        "cities_covered": 0,
        "exposed_client_locations": 0,
        "duplicate_client_ids": 0,
        "duplicate_client_rows": 0,
        "matched_client_rows": 0,
        "unmatched_client_rows": 0,
        "resolved_map_clients": 0,
        "unresolved_map_clients": 0,
        "coordinate_conflicts": 0,
        "map_included": True,
        "map_status": "No deterministically resolved client coordinates are available for plotting.",
    }


def _empty_client_geography_plot_diagnostics() -> dict:
    return {
        "total_usable_rows": 0,
        "total_plotted_rows": 0,
        "grouped_exclusion_stages": [],
        "grouped_exclusion_reasons": [],
        "excluded_candidate_rows": [],
        "location_key_counts": {
            "table_visible": 0,
            "plotted": 0,
            "missing_from_markers": 0,
        },
        "missing_location_keys_from_markers": [],
        "client_key_counts": {
            "candidate_rows": 0,
            "plotted": 0,
            "missing_from_markers": 0,
        },
        "missing_client_keys_from_markers": [],
        "resolver_cache_summary": {
            "resolver_version": GEOGRAPHY_RESOLVER_VERSION,
            "entry_count": 0,
            "datasets": [],
            "country_sources": [],
        },
    }


def _load_client_geography_coordinate_cache() -> dict[str, object]:
    if not CLIENT_GEOGRAPHY_COORDINATE_CACHE.exists():
        return {"exact": {}, "city": {}, "postcode": {}, "conflicts": set()}

    raw = json.loads(CLIENT_GEOGRAPHY_COORDINATE_CACHE.read_text(encoding="utf-8"))
    exact_candidates: dict[str, list[dict]] = {}
    city_candidates: dict[str, list[dict]] = {}
    postcode_candidates: dict[str, list[dict]] = {}

    entries = raw if isinstance(raw, list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        country = _clean_text(entry.get("country"))
        city = _clean_text(entry.get("city"))
        postcode = _clean_text(entry.get("postcode"))
        try:
            latitude = round(float(entry.get("latitude")), 6)
            longitude = round(float(entry.get("longitude")), 6)
        except (TypeError, ValueError):
            continue
        if not country or not city:
            continue

        record = {
            "country": country,
            "city": city,
            "postcode": postcode,
            "latitude": latitude,
            "longitude": longitude,
            "match_level": "country_city" if bool(entry.get("postcode_independent")) and not postcode else "country_city_postcode",
        }
        if postcode:
            exact_candidates.setdefault(_client_geography_exact_key(country, city, postcode), []).append(record)
            postcode_candidates.setdefault(_normalise_postcode_part(postcode), []).append(record)
        elif bool(entry.get("postcode_independent")):
            city_candidates.setdefault(_client_geography_city_key(country, city), []).append(record)

    conflicts: set[str] = set()
    exact: dict[str, dict] = {}
    city: dict[str, dict] = {}
    postcode: dict[str, list[dict]] = {}
    for key, records in exact_candidates.items():
        if len(records) == 1:
            exact[key] = records[0]
        else:
            conflicts.add(key)
    for key, records in city_candidates.items():
        if len(records) == 1:
            city[key] = records[0]
        else:
            conflicts.add(key)
    for key, records in postcode_candidates.items():
        postcode[key] = sorted(
            records,
            key=lambda row: (
                _normalise_geo_part(row.get("country")),
                _normalise_geo_part(row.get("city")),
                _normalise_postcode_part(row.get("postcode")),
            ),
        )
    return {"exact": exact, "city": city, "postcode": postcode, "conflicts": conflicts}


def _resolve_client_geography_coordinate(
    country: str,
    city: str,
    postcode: str,
    resolver: OfflineGeographyResolver,
) -> tuple[dict | None, str, str]:
    return resolver.resolve(country, city, postcode)


def _resolve_client_geography_city_fallback(
    country: str,
    city: str,
    cache: dict[str, object],
) -> tuple[dict | None, str, str]:
    city_key = _client_geography_city_key(country, city)
    if not _clean_text(country) or not _clean_text(city):
        return None, "No deterministic coordinate cache coverage for delivery geography", ""

    city_cache = cache.get("city", {})
    if city_key in city_cache:
        return city_cache[city_key], "", ""
    if city_key in cache.get("conflicts", set()):
        return None, "City fallback matched multiple postcode-independent cache rows", "city fallback conflict"
    return None, "City fallback found no deterministic cache match", "city fallback miss"


def _client_geography_exclusion_row(
    row: dict[str, object],
    reason: str,
    stage: str,
) -> dict[str, object]:
    country = _clean_text(row.get("country"))
    city = _clean_text(row.get("city"))
    postcode = _clean_text(row.get("postcode"))
    return {
        "client_id": _clean_text(row.get("client_id")),
        "company_name": _clean_text(row.get("company_name")),
        "country": country,
        "city": city,
        "postcode": postcode,
        "normalized_country": _normalise_geo_part(country),
        "normalized_city": _normalise_geo_part(city),
        "normalized_postcode": _normalise_postcode_part(postcode),
        "failure_stage": _clean_text(stage),
        "reason": _clean_text(reason),
    }


def _build_client_geography_plot_diagnostics(
    location_rows: list[dict],
    mapped_records: list[dict],
    map_client_rows: list[dict],
    excluded_candidate_rows: list[dict],
    resolver_cache_entries: dict[str, dict[str, object]],
) -> dict:
    exclusion_stage_counts: dict[str, int] = {}
    exclusion_reason_counts: dict[str, int] = {}
    for row in excluded_candidate_rows:
        stage = _clean_text(row.get("failure_stage"))
        reason = _clean_text(row.get("reason"))
        if stage:
            exclusion_stage_counts[stage] = exclusion_stage_counts.get(stage, 0) + 1
        if not reason:
            continue
        exclusion_reason_counts[reason] = exclusion_reason_counts.get(reason, 0) + 1

    grouped_exclusion_stages = [
        {"failure_stage": stage, "row_count": int(exclusion_stage_counts[stage])}
        for stage in sorted(exclusion_stage_counts)
    ]
    grouped_exclusion_reasons = [
        {"reason": reason, "row_count": int(exclusion_reason_counts[reason])}
        for reason in sorted(exclusion_reason_counts)
    ]

    location_keys = {
        (
            _clean_text(row.get("country")),
            _clean_text(row.get("city")),
            _clean_text(row.get("postcode")),
        )
        for row in location_rows
    }
    marker_location_keys = {
        (
            _clean_text(row.get("country")),
            _clean_text(row.get("city")),
            _clean_text(row.get("postcode")),
        )
        for row in map_client_rows
    }
    missing_location_keys = sorted(location_keys - marker_location_keys)
    missing_location_key_rows = [
        {
            "country": country,
            "city": city,
            "postcode": postcode,
            "normalized_country": _normalise_geo_part(country),
            "normalized_city": _normalise_geo_part(city),
            "normalized_postcode": _normalise_postcode_part(postcode),
        }
        for country, city, postcode in missing_location_keys
    ]

    candidate_client_rows = sorted(
        {
            (
                _clean_text(row.get("client_id")),
                _clean_text(row.get("company_name")),
            )
            for row in mapped_records
        }
    )
    plotted_client_rows = {
        (
            _clean_text(row.get("client_id")),
            _clean_text(row.get("company_name")),
        )
        for row in map_client_rows
    }
    missing_client_keys = [
        {"client_id": client_id, "company_name": company_name}
        for client_id, company_name in candidate_client_rows
        if (client_id, company_name) not in plotted_client_rows
    ]

    excluded_candidate_rows = sorted(
        excluded_candidate_rows,
        key=lambda row: (
            _clean_text(row["reason"]).lower(),
            _clean_text(row["company_name"]).lower(),
            _clean_text(row["client_id"]).lower(),
            _clean_text(row["country"]).lower(),
            _clean_text(row["city"]).lower(),
            _clean_text(row["postcode"]).lower(),
        ),
    )

    dataset_versions = sorted(
        {
            _clean_text(entry.get("dataset_version"))
            for entry in resolver_cache_entries.values()
            if _clean_text(entry.get("dataset_version"))
        }
    )
    country_sources = sorted(
        {
            _clean_text(entry.get("country_source"))
            for entry in resolver_cache_entries.values()
            if _clean_text(entry.get("country_source"))
        }
    )

    return {
        "total_usable_rows": int(len(mapped_records)),
        "total_plotted_rows": int(len(map_client_rows)),
        "grouped_exclusion_stages": grouped_exclusion_stages,
        "grouped_exclusion_reasons": grouped_exclusion_reasons,
        "excluded_candidate_rows": excluded_candidate_rows,
        "location_key_counts": {
            "table_visible": int(len(location_keys)),
            "plotted": int(len(marker_location_keys)),
            "missing_from_markers": int(len(missing_location_keys)),
        },
        "missing_location_keys_from_markers": missing_location_key_rows,
        "client_key_counts": {
            "candidate_rows": int(len(candidate_client_rows)),
            "plotted": int(len(plotted_client_rows)),
            "missing_from_markers": int(len(missing_client_keys)),
        },
        "missing_client_keys_from_markers": missing_client_keys,
        "resolver_cache_summary": {
            "resolver_version": GEOGRAPHY_RESOLVER_VERSION,
            "entry_count": int(len(resolver_cache_entries)),
            "datasets": dataset_versions,
            "country_sources": country_sources,
        },
    }


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


def _landing_mix(values: Iterable[object]) -> str:
    cleaned = sorted(
        {
            _clean_text(value).lower()
            for value in values
            if _clean_text(value).lower() in {"incoming", "landed"}
        }
    )
    if not cleaned:
        return "Unknown"
    if len(cleaned) == 1:
        return cleaned[0].title()
    return "Mixed"


def _build_client_intelligence_rows(latest: pd.DataFrame) -> pd.DataFrame:
    if latest.empty:
        return latest.copy()

    client_rows = latest.copy()
    client_rows["client_key"] = [_client_key(row) for _, row in client_rows.iterrows()]
    client_rows = client_rows[client_rows["client_key"] != ""].copy()
    if client_rows.empty:
        return client_rows

    client_rows["company_name"] = client_rows["company_name"].map(_clean_text)
    client_rows["client_id"] = client_rows["client_id"].map(_clean_text)
    client_rows["product_reference"] = client_rows["product_reference"].map(_clean_text)
    client_rows["landing_status"] = client_rows["landing_status"].map(_clean_text).str.lower()
    client_rows["request_date"] = client_rows["request_date"].map(_normalise_iso_date)
    client_rows["effective_bags"] = pd.to_numeric(client_rows["effective_bags"], errors="coerce").fillna(0.0)
    client_rows["reserved_kg"] = pd.to_numeric(client_rows["reserved_kg"], errors="coerce").fillna(0.0)
    client_rows["reserved_value_gbp"] = pd.to_numeric(client_rows["reserved_value_gbp"], errors="coerce").fillna(0.0)

    client_rows["value_complete"] = (
        client_rows["effective_bags_raw"].notna()
        & client_rows["bag_size_kg_raw"].notna()
        & client_rows["price_per_kg_raw"].notna()
    )
    client_rows["kg_complete"] = (
        client_rows["effective_bags_raw"].notna()
        & client_rows["bag_size_kg_raw"].notna()
    )
    return client_rows


def _build_client_intelligence_from_rows(client_rows: pd.DataFrame) -> tuple[dict, list[dict], list[dict], list[dict]]:
    if client_rows.empty:
        return _empty_client_summary(), [], [], []

    detail_rows: list[dict] = []
    concentration_rows: list[dict] = []
    for client_key, group in client_rows.groupby("client_key", sort=True):
        client_id = _clean_text(group["client_id"].iloc[0])
        company_candidates = sorted({name for name in group["company_name"].tolist() if name})
        company_name = company_candidates[0] if company_candidates else client_id or _clean_text(client_key)
        reservation_row_count = int(len(group))
        reserved_bags = round(float(group["effective_bags"].sum()), 4)
        reserved_kg = round(float(group["reserved_kg"].sum()), 4)
        reserved_value = round(float(group["reserved_value_gbp"].sum()), 2)
        value_available = bool(group["value_complete"].all())
        distinct_references = int(group["product_reference"].replace("", pd.NA).dropna().nunique())
        landing_mix = _landing_mix(group["landing_status"].tolist())

        reference_groups = (
            group.groupby("product_reference", sort=True, as_index=False)[
                ["reserved_value_gbp", "reserved_kg", "effective_bags"]
            ]
            .sum()
            .rename(columns={"effective_bags": "reserved_bags"})
        )
        reference_groups = reference_groups[reference_groups["product_reference"].map(_clean_text) != ""].copy()
        reference_groups = reference_groups.sort_values(
            ["reserved_value_gbp", "reserved_kg", "product_reference"],
            ascending=[False, False, True],
            kind="stable",
        )

        primary_reference = ""
        primary_reference_share = None
        primary_reference_share_available = False
        if not reference_groups.empty:
            primary_row = reference_groups.iloc[0]
            primary_reference = _clean_text(primary_row["product_reference"])
            if value_available and reserved_value > 0:
                primary_reference_share = round(float(primary_row["reserved_value_gbp"]) / reserved_value, 4)
                primary_reference_share_available = True
            elif reserved_kg > 0:
                primary_reference_share = round(float(primary_row["reserved_kg"]) / reserved_kg, 4)
                primary_reference_share_available = True

            for _, row in reference_groups.iterrows():
                concentration_rows.append(
                    {
                        "company_name": company_name,
                        "client_id": client_id,
                        "product_reference": _clean_text(row["product_reference"]),
                        "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
                    }
                )

        detail_rows.append(
            {
                "company_name": company_name,
                "client_id": client_id,
                "reservation_row_count": reservation_row_count,
                "reserved_bags": reserved_bags,
                "reserved_kg": reserved_kg,
                "reserved_value_gbp": reserved_value,
                "reserved_value_available": value_available,
                "distinct_reference_count": distinct_references,
                "primary_reference": primary_reference,
                "primary_reference_share": primary_reference_share,
                "primary_reference_share_available": primary_reference_share_available,
                "landing_mix": landing_mix,
            }
        )

    detail_rows = sorted(
        detail_rows,
        key=lambda row: (
            -float(row["reserved_value_gbp"]),
            -float(row["reserved_kg"]),
            _clean_text(row["company_name"]).lower(),
            _clean_text(row["client_id"]).lower(),
        ),
    )
    top_clients = [
        {
            "company_name": row["company_name"],
            "client_id": row["client_id"],
            "reserved_value_gbp": row["reserved_value_gbp"],
        }
        for row in detail_rows[:10]
    ]

    ranked_client_keys = {
        (_clean_text(row["client_id"]) or _clean_text(row["company_name"]))
        for row in detail_rows
        if float(row["reserved_bags"]) > 0
    }
    total_value_available = bool(client_rows["value_complete"].all())
    client_summary = {
        "clients_with_current_exposure": int(len(ranked_client_keys)),
        "total_current_reserved_value_gbp": round(float(client_rows["reserved_value_gbp"].sum()), 2),
        "total_current_reserved_value_available": total_value_available,
        "largest_client_company_name": detail_rows[0]["company_name"] if detail_rows else "",
        "largest_client_id": detail_rows[0]["client_id"] if detail_rows else "",
        "largest_client_reserved_value_gbp": round(float(detail_rows[0]["reserved_value_gbp"]), 2) if detail_rows else 0.0,
        "largest_client_reserved_value_available": bool(detail_rows[0]["reserved_value_available"]) if detail_rows else True,
        "clients_concentrated_in_one_reference": int(
            sum(
                1
                for row in detail_rows
                if bool(row["primary_reference_share_available"])
                and row["primary_reference_share"] is not None
                and float(row["primary_reference_share"]) >= 0.8
            )
        ),
    }
    concentration_rows = sorted(
        concentration_rows,
        key=lambda row: (
            -next(
                (
                    float(detail["reserved_value_gbp"])
                    for detail in detail_rows
                    if _clean_text(detail["company_name"]) == _clean_text(row["company_name"])
                    and _clean_text(detail["client_id"]) == _clean_text(row["client_id"])
                ),
                0.0,
            ),
            _clean_text(row["company_name"]).lower(),
            -float(row["reserved_value_gbp"]),
            _clean_text(row["product_reference"]).lower(),
        ),
    )
    return client_summary, detail_rows, top_clients, concentration_rows


def _build_client_intelligence(latest: pd.DataFrame) -> tuple[dict, list[dict], list[dict], list[dict], list[dict]]:
    client_rows = _build_client_intelligence_rows(latest)
    client_summary, detail_rows, top_clients, concentration_rows = _build_client_intelligence_from_rows(client_rows)
    client_activity_rows = [
        {
            "company_name": _clean_text(row["company_name"]),
            "client_id": _clean_text(row["client_id"]),
            "client_key": _clean_text(row["client_key"]),
            "product_reference": _clean_text(row["product_reference"]),
            "request_date": _clean_text(row["request_date"]),
            "request_date_available": bool(_clean_text(row["request_date"])),
            "landing_status": _clean_text(row["landing_status"]).title(),
            "effective_bags": round(float(row["effective_bags"]), 4),
            "reserved_kg": round(float(row["reserved_kg"]), 4),
            "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
            "reserved_value_available": bool(row["value_complete"]),
        }
        for _, row in client_rows.sort_values(
            ["company_name", "client_id", "product_reference", "request_date"],
            kind="stable",
            na_position="last",
        ).iterrows()
    ]
    return client_summary, detail_rows, top_clients, concentration_rows, client_activity_rows


def _prepare_clients_master(clients: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    metadata = {
        "duplicate_client_ids": 0,
        "duplicate_client_rows": 0,
    }
    if clients.empty:
        return pd.DataFrame(), metadata

    master = clients.copy()
    for column in ("client_id", "company_name", "country", "city", "postcode"):
        if column not in master.columns:
            master[column] = pd.NA

    for column in ("client_id", "company_name", "country", "city", "postcode"):
        master[column] = master[column].map(_clean_text)

    master = master[master["client_id"] != ""].copy()
    if master.empty:
        return master, metadata

    duplicate_counts = master["client_id"].value_counts(dropna=False)
    duplicate_counts = duplicate_counts[duplicate_counts > 1]
    metadata["duplicate_client_ids"] = int(len(duplicate_counts))
    metadata["duplicate_client_rows"] = int(duplicate_counts.sum()) if not duplicate_counts.empty else 0

    master["delivery_geo_score"] = (
        master["country"].ne("").astype(int)
        + master["city"].ne("").astype(int)
        + master["postcode"].ne("").astype(int)
    )
    master = master.sort_values(
        ["client_id", "delivery_geo_score", "company_name", "country", "city", "postcode"],
        ascending=[True, False, True, True, True, True],
        kind="stable",
        na_position="last",
    )
    master = master.groupby("client_id", sort=True, as_index=False).head(1).copy()
    return master, metadata


def _prepare_client_contact_master(clients: pd.DataFrame) -> pd.DataFrame:
    if clients.empty:
        return pd.DataFrame()

    master = clients.copy()
    for column in (
        "client_id",
        "company_name",
        "contact_first_name",
        "contact_last_name",
        "contact_email",
        "add_contact_email",
        "add_contact_include_email",
    ):
        if column not in master.columns:
            master[column] = pd.NA
        master[column] = master[column].map(_clean_text)

    master = master[master["client_id"] != ""].copy()
    if master.empty:
        return master

    master["primary_email_present"] = master["contact_email"].ne("")
    master["primary_name_present"] = master["contact_first_name"].ne("") | master["contact_last_name"].ne("")
    master["additional_email_allowed"] = (
        master["add_contact_include_email"].eq("1") & master["add_contact_email"].ne("")
    )
    master = master.sort_values(
        [
            "client_id",
            "primary_email_present",
            "primary_name_present",
            "additional_email_allowed",
            "company_name",
            "contact_email",
            "add_contact_email",
        ],
        ascending=[True, False, False, False, True, True, True],
        kind="stable",
        na_position="last",
    )
    return master.groupby("client_id", sort=True, as_index=False).head(1).copy()


def _empty_expired_draft_workflow(snapshot_date: str) -> dict:
    return {
        "summary": {
            "as_of_date": snapshot_date,
            "breached_rows": 0,
            "breached_reservations": 0,
            "draft_client_count": 0,
            "drafts_missing_primary_email": 0,
            "status": "No expired reservation draft candidates in the current workspace snapshot.",
        },
        "drafts": [],
    }


def _build_expired_reservation_draft_workflow(
    latest: pd.DataFrame,
    clients: pd.DataFrame,
    snapshot_date: str,
) -> dict:
    if latest.empty:
        return _empty_expired_draft_workflow(snapshot_date)

    rows = latest.copy()
    rows["company_name"] = rows["company_name"].map(_clean_text)
    rows["client_id"] = rows["client_id"].map(_clean_text)
    rows["reservation_key"] = rows["reservation_key"].map(_clean_text)
    rows["product_reference"] = rows["product_reference"].map(_clean_text)
    rows["approval_date"] = rows["approval_date"].map(_normalise_iso_date)
    rows["bags_remaining"] = pd.to_numeric(rows["bags_remaining"], errors="coerce").fillna(0.0)
    if "bag_size_kg_raw" not in rows.columns:
        rows["bag_size_kg_raw"] = _to_numeric_or_nan_series(rows, "bag_size_kg")
    if "price_per_kg_raw" not in rows.columns:
        rows["price_per_kg_raw"] = _to_numeric_or_nan_series(rows, "price_per_kg")
    if "reservation_days_raw" not in rows.columns:
        rows["reservation_days_raw"] = _to_numeric_or_nan_series(rows, "reservation_days")

    rows = rows[rows["bags_remaining"] > 0].copy()
    if rows.empty:
        return _empty_expired_draft_workflow(snapshot_date)

    rows["approval_dt"] = pd.to_datetime(rows["approval_date"], errors="coerce", format="%Y-%m-%d")
    rows["reservation_days_valid"] = rows["reservation_days_raw"].notna() & (rows["reservation_days_raw"] >= 0)
    rows["expiry_available"] = rows["approval_dt"].notna() & rows["reservation_days_valid"]
    rows["expiry_dt"] = pd.NaT
    rows.loc[rows["expiry_available"], "expiry_dt"] = (
        rows.loc[rows["expiry_available"], "approval_dt"]
        + pd.to_timedelta(rows.loc[rows["expiry_available"], "reservation_days_raw"], unit="D")
    )

    snapshot_ts = pd.to_datetime(snapshot_date, errors="coerce", format="%Y-%m-%d")
    rows["days_to_expiry"] = float("nan")
    if not pd.isna(snapshot_ts):
        rows.loc[rows["expiry_available"], "days_to_expiry"] = (
            rows.loc[rows["expiry_available"], "expiry_dt"] - snapshot_ts
        ).dt.days.astype("float64")

    rows["is_breached"] = rows["expiry_available"] & rows["days_to_expiry"].notna() & (rows["days_to_expiry"] < 0)
    rows = rows[rows["is_breached"]].copy()
    if rows.empty:
        return _empty_expired_draft_workflow(snapshot_date)

    rows["remaining_kg_value"] = (rows["bags_remaining"] * rows["bag_size_kg_raw"]).where(
        rows["bag_size_kg_raw"].notna(),
        0.0,
    )
    rows["value_complete"] = rows["bag_size_kg_raw"].notna() & rows["price_per_kg_raw"].notna()
    rows["remaining_value_gbp_value"] = (
        rows["remaining_kg_value"] * rows["price_per_kg_raw"]
    ).where(rows["value_complete"], 0.0)
    rows["days_expired"] = rows["days_to_expiry"].abs().astype("int64")
    rows = rows.sort_values(
        ["company_name", "client_id", "days_expired", "reservation_key", "product_reference"],
        ascending=[True, True, False, True, True],
        kind="stable",
        na_position="last",
    )

    contact_master = _prepare_client_contact_master(clients)
    contact_lookup = {
        _clean_text(row["client_id"]): row
        for _, row in contact_master.iterrows()
        if _clean_text(row.get("client_id"))
    }

    def _unique_reservation_count(frame: pd.DataFrame) -> int:
        if frame.empty:
            return 0
        return int(frame["reservation_key"].replace("", pd.NA).dropna().nunique())

    drafts: list[dict] = []
    for client_key, group in rows.groupby(["company_name", "client_id"], sort=True, dropna=False):
        company_name, client_id = client_key
        company_name = _clean_text(company_name)
        client_id = _clean_text(client_id)
        contact_row = contact_lookup.get(client_id)
        contact_first_name = _clean_text(contact_row.get("contact_first_name")) if contact_row is not None else ""
        contact_last_name = _clean_text(contact_row.get("contact_last_name")) if contact_row is not None else ""
        contact_email = _clean_text(contact_row.get("contact_email")) if contact_row is not None else ""
        add_contact_email = ""
        if contact_row is not None and _clean_text(contact_row.get("add_contact_include_email")) == "1":
            add_contact_email = _clean_text(contact_row.get("add_contact_email"))

        recipient_emails = [email for email in [contact_email] if email]
        cc_emails = [email for email in [add_contact_email] if email and email not in recipient_emails]

        greeting_name = contact_first_name or (f"{company_name} team" if company_name else "team")
        subject = f"Mercanta reservation reminder: expired reservations for {company_name or client_id or 'client'}"

        group_rows = group.sort_values(
            ["days_expired", "reservation_key", "product_reference"],
            ascending=[False, True, True],
            kind="stable",
            na_position="last",
        )
        line_items: list[dict] = []
        for _, row in group_rows.iterrows():
            reservation_key = _clean_text(row["reservation_key"])
            product_reference = _clean_text(row["product_reference"])
            expiry_date = row["expiry_dt"].date().isoformat() if pd.notna(row["expiry_dt"]) else ""
            bags_remaining = round(float(row["bags_remaining"]), 4)
            remaining_kg = round(float(row["remaining_kg_value"]), 4) if pd.notna(row["bag_size_kg_raw"]) else None
            remaining_value_gbp = (
                round(float(row["remaining_value_gbp_value"]), 2) if bool(row["value_complete"]) else None
            )
            line_items.append(
                {
                    "reservation_key": reservation_key,
                    "product_reference": product_reference,
                    "bags_remaining": bags_remaining,
                    "remaining_kg": remaining_kg,
                    "remaining_value_gbp": remaining_value_gbp,
                    "expiry_date": expiry_date,
                    "days_expired": int(row["days_expired"]),
                }
            )

        intro = (
            f"Dear {greeting_name},\n\n"
            "We are writing to remind you that the reservations below are now past their expiry date on our latest workspace snapshot.\n"
        )
        bullet_lines = []
        for item in line_items:
            kg_segment = (
                f" | {int(round(item['remaining_kg'], 0))} kg remaining"
                if item["remaining_kg"] is not None
                else ""
            )
            value_segment = (
                f", value GBP {int(round(item['remaining_value_gbp'], 0)):,}"
                if item["remaining_value_gbp"] is not None
                else ""
            )
            bullet_lines.append(
                f"- Reservation {item['reservation_key']} | {item['product_reference']} | "
                f"{int(round(item['bags_remaining'], 0))} bags remaining | "
                f"expired on {item['expiry_date']} | {item['days_expired']} days expired"
                f"{kg_segment}"
                f"{value_segment}"
            )
        closing = (
            "\nPlease review these reservations and let us know how you would like to proceed with release planning.\n\n"
            "Kind regards,\nMercanta"
        )
        body = intro + "\n".join(bullet_lines) + closing
        drafts.append(
            {
                "company_name": company_name,
                "client_id": client_id,
                "contact_first_name": contact_first_name,
                "contact_last_name": contact_last_name,
                "contact_email": contact_email,
                "cc_emails": cc_emails,
                "to_emails": recipient_emails,
                "missing_primary_email": not bool(contact_email),
                "greeting_name": greeting_name,
                "subject": subject,
                "body": body,
                "breached_reservation_count": _unique_reservation_count(group_rows),
                "breached_row_count": int(len(group_rows)),
                "line_items": line_items,
            }
        )

    drafts = sorted(
        drafts,
        key=lambda row: (
            row["missing_primary_email"],
            row["company_name"].lower(),
            row["client_id"].lower(),
        ),
    )
    return {
        "summary": {
            "as_of_date": snapshot_date,
            "breached_rows": int(len(rows)),
            "breached_reservations": _unique_reservation_count(rows),
            "draft_client_count": int(len(drafts)),
            "drafts_missing_primary_email": int(sum(1 for draft in drafts if draft["missing_primary_email"])),
            "status": (
                f"Prepared {len(drafts)} grouped draft reminder(s) from breached reservations only. "
                "Manual review required before any external send."
            ),
        },
        "drafts": drafts,
    }


def _build_client_geography(
    latest: pd.DataFrame,
    clients: pd.DataFrame,
    geography_resolver: OfflineGeographyResolver | None = None,
) -> tuple[dict, list[dict], list[dict], list[dict], list[dict], list[dict], list[dict], dict]:
    empty_summary = _empty_client_geography_summary()
    empty_diagnostics = _empty_client_geography_plot_diagnostics()
    coordinate_resolver = geography_resolver or OfflineGeographyResolver(CLIENT_GEOGRAPHY_COORDINATE_CACHE)
    clients_master, metadata = _prepare_clients_master(clients)
    clients_lookup = {
        _clean_text(row["client_id"]): row
        for _, row in clients_master.iterrows()
        if _clean_text(row.get("client_id"))
    }
    client_rows = _build_client_intelligence_rows(latest)
    exposure_rows_by_client_id: dict[str, dict] = {}
    if not client_rows.empty:
        _client_summary, detail_rows, _top_clients, _concentration_rows = _build_client_intelligence_from_rows(client_rows)
        exposure_rows_by_client_id = {
            _clean_text(row["client_id"]): row
            for row in detail_rows
            if _clean_text(row.get("client_id"))
        }
    else:
        detail_rows = []

    if clients_master.empty and not detail_rows:
        return empty_summary, [], [], [], [], [], [], empty_diagnostics

    client_geography_activity_rows: list[dict] = []
    sorted_client_rows = client_rows
    if not client_rows.empty:
        sorted_client_rows = client_rows.sort_values(
            ["company_name", "client_id", "product_reference", "request_date"],
            kind="stable",
            na_position="last",
        )
    for _, row in sorted_client_rows.iterrows():
        client_id = _clean_text(row["client_id"])
        company_name = _clean_text(row["company_name"])
        request_date = _clean_text(row["request_date"])
        product_reference = _clean_text(row["product_reference"])
        reserved_bags = round(float(row["effective_bags"]), 4)
        reserved_kg = round(float(row["reserved_kg"]), 4)
        reserved_value_gbp = round(float(row["reserved_value_gbp"]), 2)
        reserved_value_available = bool(row["value_complete"])
        country = ""
        city = ""
        postcode = ""
        location_label = "Unknown"
        coordinate_match_level = ""
        latitude = None
        longitude = None
        unmapped_reason = ""
        coordinate: dict | None = None

        if not client_id:
            unmapped_reason = "Missing client_id on activity rows"
        else:
            client_master = clients_lookup.get(client_id)
            if client_master is None:
                unmapped_reason = "No matching clients master row for client_id"
            else:
                country = _clean_text(client_master.get("country"))
                city = _clean_text(client_master.get("city"))
                postcode = _clean_text(client_master.get("postcode"))
                location_label = ", ".join([part for part in (city, postcode, country) if part]) or "Unknown"
                if not any((country, city, postcode)):
                    unmapped_reason = "Missing delivery geography on clients master row"
                else:
                    coordinate, _reason, _failure_stage = _resolve_client_geography_coordinate(
                        country,
                        city,
                        postcode,
                        coordinate_resolver,
                    )
                    if coordinate is not None:
                        coordinate_match_level = _clean_text(coordinate["match_level"])
                        latitude = float(coordinate["latitude"])
                        longitude = float(coordinate["longitude"])

        client_geography_activity_rows.append(
            {
                "company_name": company_name,
                "client_id": client_id,
                "product_reference": product_reference,
                "request_date": request_date,
                "request_date_available": bool(request_date),
                "reserved_bags": reserved_bags,
                "reserved_kg": reserved_kg,
                "reserved_value_gbp": reserved_value_gbp,
                "reserved_value_available": reserved_value_available,
                "country": country,
                "city": city,
                "postcode": postcode,
                "location_label": location_label,
                "coordinate_match_level": coordinate_match_level,
                "latitude": latitude,
                "longitude": longitude,
                "unmapped_reason": unmapped_reason,
            }
        )

    mapped_records: list[dict] = []
    unmapped_records: list[dict] = []
    matched_client_rows = int(len(exposure_rows_by_client_id))
    unmatched_client_rows = 0

    for _, client_master in clients_master.iterrows():
        client_id = _clean_text(client_master.get("client_id"))
        company_name = _clean_text(client_master.get("company_name"))
        exposure = exposure_rows_by_client_id.get(client_id)
        reserved_value_gbp = round(float(exposure["reserved_value_gbp"]), 2) if exposure is not None else 0.0
        reserved_value_available = bool(exposure["reserved_value_available"]) if exposure is not None else True
        reserved_bags = round(float(exposure["reserved_bags"]), 4) if exposure is not None else 0.0
        reserved_kg = round(float(exposure["reserved_kg"]), 4) if exposure is not None else 0.0
        country = _clean_text(client_master.get("country"))
        city = _clean_text(client_master.get("city"))
        postcode = _clean_text(client_master.get("postcode"))
        if not any((country, city, postcode)):
            unmapped_records.append(
                {
                    "company_name": company_name,
                    "client_id": client_id,
                    "reserved_value_gbp": reserved_value_gbp,
                    "reserved_value_available": reserved_value_available,
                    "reserved_bags": reserved_bags,
                    "reserved_kg": reserved_kg,
                    "reason": "Missing delivery geography on clients master row",
                }
            )
            continue

        mapped_records.append(
            {
                "company_name": company_name,
                "client_id": client_id,
                "country": country,
                "city": city,
                "postcode": postcode,
                "reserved_value_gbp": reserved_value_gbp,
                "reserved_value_available": reserved_value_available,
                "reserved_bags": reserved_bags,
                "reserved_kg": reserved_kg,
                "has_exposure": bool(reserved_bags > 0),
                "distinct_reference_count": int(exposure["distinct_reference_count"]) if exposure is not None else 0,
                "primary_reference": _clean_text(exposure["primary_reference"]) if exposure is not None else "",
            }
        )

    for row in detail_rows:
        client_id = _clean_text(row["client_id"])
        company_name = _clean_text(row["company_name"])
        if not client_id:
            unmatched_client_rows += 1
            unmapped_records.append(
                {
                    "company_name": company_name,
                    "client_id": client_id,
                    "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
                    "reserved_value_available": bool(row["reserved_value_available"]),
                    "reserved_bags": round(float(row["reserved_bags"]), 4),
                    "reserved_kg": round(float(row["reserved_kg"]), 4),
                    "reason": "Missing client_id on activity rows",
                }
            )
            continue
        if client_id not in clients_lookup:
            unmatched_client_rows += 1
            unmapped_records.append(
                {
                    "company_name": company_name,
                    "client_id": client_id,
                    "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
                    "reserved_value_available": bool(row["reserved_value_available"]),
                    "reserved_bags": round(float(row["reserved_bags"]), 4),
                    "reserved_kg": round(float(row["reserved_kg"]), 4),
                    "reason": "No matching clients master row for client_id",
                }
            )

    mapped_clients = len(mapped_records)
    unmapped_clients = len(unmapped_records)

    location_groups: dict[tuple[str, str, str], list[dict]] = {}
    for row in mapped_records:
        key = (row["country"], row["city"], row["postcode"])
        location_groups.setdefault(key, []).append(row)

    location_rows: list[dict] = []
    for key in sorted(location_groups):
        rows = location_groups[key]
        country, city, postcode = key
        value_available = all(bool(item["reserved_value_available"]) for item in rows)
        top_client = sorted(
            rows,
            key=lambda item: (
                -float(item["reserved_value_gbp"]),
                _clean_text(item["company_name"]).lower(),
                _clean_text(item["client_id"]).lower(),
            ),
        )[0]
        location_rows.append(
            {
                "country": country,
                "city": city,
                "postcode": postcode,
                "location_label": ", ".join([part for part in (city, postcode, country) if part]) or "Unknown",
                "client_count": int(len(rows)),
                "exposed_client_count": int(sum(1 for item in rows if bool(item["has_exposure"]))),
                "reserved_bags": round(sum(float(item["reserved_bags"]) for item in rows), 4),
                "reserved_kg": round(sum(float(item["reserved_kg"]) for item in rows), 4),
                "reserved_value_gbp": round(sum(float(item["reserved_value_gbp"]) for item in rows), 2),
                "reserved_value_available": value_available,
                "top_client_company_name": _clean_text(top_client["company_name"]),
                "top_client_id": _clean_text(top_client["client_id"]),
            }
        )

    location_rows = sorted(
        location_rows,
        key=lambda row: (
            -float(row["reserved_value_gbp"]),
            -int(row["client_count"]),
            _clean_text(row["country"]).lower(),
            _clean_text(row["city"]).lower(),
            _clean_text(row["postcode"]).lower(),
        ),
    )

    country_rows: list[dict] = []
    city_rows: list[dict] = []
    if mapped_records:
        mapped_frame = pd.DataFrame(mapped_records)
        country_groups = (
            mapped_frame.groupby("country", sort=True, as_index=False)[
                ["client_id", "reserved_bags", "reserved_kg", "reserved_value_gbp"]
            ]
            .agg(
                {
                    "client_id": "nunique",
                    "reserved_bags": "sum",
                    "reserved_kg": "sum",
                    "reserved_value_gbp": "sum",
                }
            )
            .rename(columns={"client_id": "client_count"})
        )
        country_rows = [
            {
                "country": _clean_text(row["country"]) or "Unknown",
                "client_count": int(row["client_count"]),
                "reserved_bags": round(float(row["reserved_bags"]), 4),
                "reserved_kg": round(float(row["reserved_kg"]), 4),
                "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
            }
            for _, row in country_groups.sort_values(
                ["reserved_value_gbp", "client_count", "country"],
                ascending=[False, False, True],
                kind="stable",
            ).head(8).iterrows()
        ]

        city_groups = (
            mapped_frame.assign(city_label=mapped_frame.apply(
                lambda row: ", ".join([part for part in (_clean_text(row["city"]), _clean_text(row["country"])) if part]),
                axis=1,
            ))
            .groupby(["city_label", "country", "city"], sort=True, as_index=False)[
                ["client_id", "reserved_bags", "reserved_kg", "reserved_value_gbp"]
            ]
            .agg(
                {
                    "client_id": "nunique",
                    "reserved_bags": "sum",
                    "reserved_kg": "sum",
                    "reserved_value_gbp": "sum",
                }
            )
            .rename(columns={"client_id": "client_count"})
        )
        city_rows = [
            {
                "city_label": _clean_text(row["city_label"]) or "Unknown",
                "country": _clean_text(row["country"]),
                "city": _clean_text(row["city"]),
                "client_count": int(row["client_count"]),
                "reserved_bags": round(float(row["reserved_bags"]), 4),
                "reserved_kg": round(float(row["reserved_kg"]), 4),
                "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
            }
            for _, row in city_groups.sort_values(
                ["reserved_value_gbp", "client_count", "city_label"],
                ascending=[False, False, True],
                kind="stable",
            ).head(8).iterrows()
        ]

    unmapped_records = sorted(
        unmapped_records,
        key=lambda row: (
            -float(row["reserved_value_gbp"]),
            _clean_text(row["company_name"]).lower(),
            _clean_text(row["client_id"]).lower(),
            _clean_text(row["reason"]).lower(),
        ),
    )

    map_client_rows: list[dict] = []
    excluded_candidate_rows: list[dict] = []
    coordinate_conflicts = 0
    for row in mapped_records:
        coordinate, reason, failure_stage = _resolve_client_geography_coordinate(
            row["country"],
            row["city"],
            row["postcode"],
            coordinate_resolver,
        )
        if coordinate is None:
            if "conflict" in reason.lower():
                coordinate_conflicts += 1
            excluded_candidate_rows.append(_client_geography_exclusion_row(row, reason, failure_stage))
            continue
        map_client_rows.append(
            {
                "marker_id": (_clean_text(row["client_id"]) or _clean_text(row["company_name"])),
                "company_name": _clean_text(row["company_name"]),
                "client_id": _clean_text(row["client_id"]),
                "country": _clean_text(row["country"]),
                "city": _clean_text(row["city"]),
                "postcode": _clean_text(row["postcode"]),
                "location_label": ", ".join(
                    [
                        part
                        for part in (
                            _clean_text(row["city"]),
                            _clean_text(row["postcode"]),
                            _clean_text(row["country"]),
                        )
                        if part
                    ]
                ) or "Unknown",
                "latitude": float(coordinate["latitude"]),
                "longitude": float(coordinate["longitude"]),
                "coordinate_match_level": _clean_text(coordinate["match_level"]),
                "reserved_value_gbp": round(float(row["reserved_value_gbp"]), 2),
                "reserved_value_available": bool(row["reserved_value_available"]),
                "reserved_bags": round(float(row["reserved_bags"]), 4),
                "reserved_kg": round(float(row["reserved_kg"]), 4),
                "has_exposure": bool(row["has_exposure"]),
                "distinct_reference_count": int(row["distinct_reference_count"]),
                "primary_reference": _clean_text(row["primary_reference"]),
            }
        )

    map_client_rows = sorted(
        map_client_rows,
        key=lambda row: (
            not bool(row["has_exposure"]),
            -float(row["reserved_value_gbp"]),
            -float(row["reserved_bags"]),
            _clean_text(row["company_name"]).lower(),
            _clean_text(row["client_id"]).lower(),
        ),
    )

    resolved_map_clients = int(len(map_client_rows))
    unresolved_map_clients = int(max(mapped_clients - resolved_map_clients, 0))
    if resolved_map_clients > 0:
        map_status = (
            f"Plotting {resolved_map_clients} deterministically resolved client markers; "
            f"{unresolved_map_clients} mapped clients remain unplotted."
        )
    else:
        map_status = "No deterministically resolved client coordinates are available for plotting."
    if coordinate_conflicts > 0:
        map_status = f"{map_status} {coordinate_conflicts} mapped clients hit coordinate-cache conflicts."

    summary = {
        "mapped_clients": int(mapped_clients),
        "unmapped_clients": int(unmapped_clients),
        "countries_covered": int(len({row["country"] for row in mapped_records if _clean_text(row["country"])})),
        "cities_covered": int(
            len(
                {
                    (_clean_text(row["country"]), _clean_text(row["city"]))
                    for row in mapped_records
                    if _clean_text(row["city"])
                }
            )
        ),
        "exposed_client_locations": int(sum(1 for row in location_rows if int(row["exposed_client_count"]) > 0)),
        "duplicate_client_ids": int(metadata["duplicate_client_ids"]),
        "duplicate_client_rows": int(metadata["duplicate_client_rows"]),
        "matched_client_rows": int(matched_client_rows),
        "unmatched_client_rows": int(unmatched_client_rows),
        "resolved_map_clients": resolved_map_clients,
        "unresolved_map_clients": unresolved_map_clients,
        "coordinate_conflicts": int(coordinate_conflicts),
        "map_included": True,
        "map_status": map_status,
    }
    diagnostics = _build_client_geography_plot_diagnostics(
        location_rows,
        mapped_records,
        map_client_rows,
        excluded_candidate_rows,
        coordinate_resolver.memo_entries,
    )
    return (
        summary,
        location_rows,
        country_rows,
        city_rows,
        unmapped_records,
        map_client_rows,
        client_geography_activity_rows,
        diagnostics,
    )


def _empty_action_queue_dataset(snapshot_date: str) -> dict:
    return {
        "summary": {
            "as_of_date": snapshot_date,
            "near_expiry_threshold_days": ACTION_QUEUE_NEAR_EXPIRY_DAYS,
            "open_reservation_rows": 0,
            "open_reservations": 0,
            "open_reserved_bags": 0.0,
            "open_reserved_bags_landed": 0.0,
            "open_reserved_bags_incoming": 0.0,
            "open_reserved_value_gbp": 0.0,
            "open_reserved_value_available": True,
            "open_reserved_value_landed_gbp": 0.0,
            "open_reserved_value_landed_available": True,
            "open_reserved_value_incoming_gbp": 0.0,
            "open_reserved_value_incoming_available": True,
            "near_expiry_rows": 0,
            "near_expiry_reservations": 0,
            "breached_rows": 0,
            "breached_reservations": 0,
            "landed_not_released_value_gbp": 0.0,
            "landed_not_released_value_available": True,
            "landed_not_released_value_status": "No landed open reservation rows.",
            "action_now_rows": 0,
            "action_now_reservations": 0,
            "open_exposure_reservations": 0,
        },
        "action_bucket_counts": [
            {"action_bucket": "Breached", "row_count": 0},
            {"action_bucket": "Near Expiry", "row_count": 0},
            {"action_bucket": "Landed Not Approved", "row_count": 0},
            {"action_bucket": "Landed Not Released", "row_count": 0},
            {"action_bucket": "Open Exposure", "row_count": 0},
        ],
        "open_bags_by_expiry_bucket": [
            {"expiry_bucket": "Breached", "open_bags": 0.0},
            {"expiry_bucket": "0-7 days", "open_bags": 0.0},
            {"expiry_bucket": "8+ days", "open_bags": 0.0},
            {"expiry_bucket": "No expiry data", "open_bags": 0.0},
        ],
        "top_landed_references": {
            "metric": "remaining_value_gbp",
            "metric_label": "Landed Not Released Value",
            "value_available": True,
            "status": "No landed open reservation rows.",
            "rows": [],
        },
        "expired_draft_workflow": _empty_expired_draft_workflow(snapshot_date),
        "details": [],
    }


def _build_reservation_action_queue(latest: pd.DataFrame, snapshot_date: str) -> dict:
    if latest.empty:
        return _empty_action_queue_dataset(snapshot_date)

    rows = latest.copy()
    rows["company_name"] = rows["company_name"].map(_clean_text)
    rows["client_id"] = rows["client_id"].map(_clean_text)
    rows["reservation_key"] = rows["reservation_key"].map(_clean_text)
    rows["product_reference"] = rows["product_reference"].map(_clean_text)
    rows["product_id"] = rows["product_id"].map(_clean_text)
    rows["request_status"] = rows["request_status"].map(_clean_text).str.lower()
    rows["approval_date"] = rows["approval_date"].map(_normalise_iso_date)
    rows["landing_date"] = rows["landing_date"].map(_normalise_iso_date)
    rows["landing_status"] = rows["landing_status"].map(_clean_text).str.lower()
    rows["warehouse"] = rows["warehouse"].map(_clean_text)
    rows["bags_remaining"] = pd.to_numeric(rows["bags_remaining"], errors="coerce").fillna(0.0)
    if "bag_size_kg_raw" not in rows.columns:
        rows["bag_size_kg_raw"] = _to_numeric_or_nan_series(rows, "bag_size_kg")
    if "price_per_kg_raw" not in rows.columns:
        rows["price_per_kg_raw"] = _to_numeric_or_nan_series(rows, "price_per_kg")
    if "reservation_days_raw" not in rows.columns:
        rows["reservation_days_raw"] = _to_numeric_or_nan_series(rows, "reservation_days")

    rows = rows[rows["bags_remaining"] > 0].copy()
    if rows.empty:
        return _empty_action_queue_dataset(snapshot_date)

    rows["approval_dt"] = pd.to_datetime(rows["approval_date"], errors="coerce", format="%Y-%m-%d")
    rows["reservation_days_valid"] = rows["reservation_days_raw"].notna() & (rows["reservation_days_raw"] >= 0)
    rows["expiry_available"] = rows["approval_dt"].notna() & rows["reservation_days_valid"]
    rows["expiry_dt"] = pd.NaT
    rows.loc[rows["expiry_available"], "expiry_dt"] = (
        rows.loc[rows["expiry_available"], "approval_dt"]
        + pd.to_timedelta(rows.loc[rows["expiry_available"], "reservation_days_raw"], unit="D")
    )

    snapshot_ts = pd.to_datetime(snapshot_date, errors="coerce", format="%Y-%m-%d")
    rows["days_to_expiry"] = float("nan")
    if not pd.isna(snapshot_ts):
        rows.loc[rows["expiry_available"], "days_to_expiry"] = (
            rows.loc[rows["expiry_available"], "expiry_dt"] - snapshot_ts
        ).dt.days.astype("float64")

    rows["is_breached"] = rows["expiry_available"] & rows["days_to_expiry"].notna() & (rows["days_to_expiry"] < 0)
    rows["is_near_expiry"] = (
        rows["expiry_available"]
        & rows["days_to_expiry"].notna()
        & (rows["days_to_expiry"] >= 0)
        & (rows["days_to_expiry"] <= ACTION_QUEUE_NEAR_EXPIRY_DAYS)
    )
    rows["is_landed_not_approved"] = (
        (rows["landing_status"] == "landed") & (rows["request_status"] == "created")
    )
    rows["is_landed_not_released"] = (rows["landing_status"] == "landed") & ~rows["is_landed_not_approved"]
    rows["kg_complete"] = rows["bag_size_kg_raw"].notna()
    rows["remaining_kg_value"] = (rows["bags_remaining"] * rows["bag_size_kg_raw"]).where(rows["kg_complete"], 0.0)
    rows["value_complete"] = rows["kg_complete"] & rows["price_per_kg_raw"].notna()
    rows["remaining_value_gbp_value"] = (
        rows["remaining_kg_value"] * rows["price_per_kg_raw"]
    ).where(rows["value_complete"], 0.0)

    labels = [
        _action_bucket_and_priority(
            bool(row["is_breached"]),
            bool(row["is_near_expiry"]),
            bool(row["is_landed_not_approved"]),
            bool(row["is_landed_not_released"]),
        )
        for _, row in rows.iterrows()
    ]
    rows["action_bucket"] = [label[0] for label in labels]
    rows["action_priority"] = [label[1] for label in labels]
    rows["action_priority_rank"] = [label[2] for label in labels]
    rows["action_now"] = (
        rows["is_breached"]
        | rows["is_near_expiry"]
        | rows["is_landed_not_approved"]
        | rows["is_landed_not_released"]
    )

    rows["data_status"] = [
        _status_summary(
            [
                "Approval date unavailable" if not bool(row["approval_date"]) else "",
                "Reservation days unavailable" if not bool(row["reservation_days_valid"]) else "",
                "Remaining kg unavailable" if not bool(row["kg_complete"]) else "",
                "Remaining value unavailable" if bool(row["kg_complete"]) and not bool(row["value_complete"]) else "",
            ]
        )
        for _, row in rows.iterrows()
    ]

    landed_open_rows = rows[rows["is_landed_not_released"]].copy()
    landed_rows = rows[rows["landing_status"] == "landed"].copy()
    incoming_rows = rows[rows["landing_status"] == "incoming"].copy()
    landed_not_released_value_available = bool(
        landed_open_rows.empty or landed_open_rows["value_complete"].all()
    )
    if landed_open_rows.empty:
        landed_not_released_value_status = "No landed open reservation rows."
    elif landed_not_released_value_available:
        landed_not_released_value_status = "Complete across all landed open reservation rows."
    else:
        landed_not_released_value_status = (
            "Unavailable on one or more landed open reservation rows due to missing kg or price."
        )

    action_bucket_counts = []
    for bucket in (
        "Breached",
        "Near Expiry",
        "Landed Not Approved",
        "Landed Not Released",
        "Open Exposure",
    ):
        action_bucket_counts.append(
            {
                "action_bucket": bucket,
                "row_count": int((rows["action_bucket"] == bucket).sum()),
            }
        )

    def _unique_reservation_count(frame: pd.DataFrame) -> int:
        if frame.empty:
            return 0
        return int(frame["reservation_key"].map(_clean_text).replace("", pd.NA).dropna().nunique())

    expiry_bucket_rows = [
        {
            "expiry_bucket": "Breached",
            "open_bags": round(float(rows[rows["is_breached"]]["bags_remaining"].sum()), 4),
        },
        {
            "expiry_bucket": "0-7 days",
            "open_bags": round(float(rows[rows["is_near_expiry"]]["bags_remaining"].sum()), 4),
        },
        {
            "expiry_bucket": "8+ days",
            "open_bags": round(
                float(
                    rows[
                        rows["expiry_available"]
                        & rows["days_to_expiry"].notna()
                        & (rows["days_to_expiry"] > ACTION_QUEUE_NEAR_EXPIRY_DAYS)
                    ]["bags_remaining"].sum()
                ),
                4,
            ),
        },
        {
            "expiry_bucket": "No expiry data",
            "open_bags": round(float(rows[~rows["expiry_available"]]["bags_remaining"].sum()), 4),
        },
    ]

    top_ref_groups = (
        landed_open_rows.groupby("product_reference", sort=True, as_index=False)[
            ["bags_remaining", "remaining_kg_value", "remaining_value_gbp_value"]
        ]
        .sum()
        .rename(
            columns={
                "bags_remaining": "open_bags",
                "remaining_kg_value": "remaining_kg",
                "remaining_value_gbp_value": "remaining_value_gbp",
            }
        )
    )
    top_ref_groups = top_ref_groups.sort_values(
        ["remaining_value_gbp", "open_bags", "product_reference"],
        ascending=[False, False, True],
        kind="stable",
    )
    top_landed_reference_rows = [
        {
            "product_reference": _clean_text(row["product_reference"]) or "Unknown",
            "open_bags": round(float(row["open_bags"]), 4),
            "remaining_kg": round(float(row["remaining_kg"]), 4),
            "remaining_value_gbp": round(float(row["remaining_value_gbp"]), 2),
        }
        for _, row in top_ref_groups.head(8).iterrows()
        if _clean_text(row["product_reference"]) or float(row["open_bags"]) > 0
    ]

    rows = rows.sort_values(
        [
            "action_priority_rank",
            "days_to_expiry",
            "is_landed_not_released",
            "bags_remaining",
            "company_name",
            "reservation_key",
            "product_reference",
            "product_id",
        ],
        ascending=[True, True, False, False, True, True, True, True],
        kind="stable",
        na_position="last",
    )
    detail_rows = [
        {
            "action_priority": _clean_text(row["action_priority"]),
            "action_priority_rank": int(row["action_priority_rank"]),
            "action_bucket": _clean_text(row["action_bucket"]),
            "days_to_expiry": int(row["days_to_expiry"]) if pd.notna(row["days_to_expiry"]) else None,
            "expiry_date": row["expiry_dt"].date().isoformat() if pd.notna(row["expiry_dt"]) else "",
            "company_name": _clean_text(row["company_name"]),
            "client_id": _clean_text(row["client_id"]),
            "reservation_key": _clean_text(row["reservation_key"]),
            "product_reference": _clean_text(row["product_reference"]),
            "product_id": _clean_text(row["product_id"]),
            "request_status": _clean_text(row["request_status"]).title(),
            "approval_date": _clean_text(row["approval_date"]),
            "reservation_days": (
                int(float(row["reservation_days_raw"]))
                if pd.notna(row["reservation_days_raw"]) and float(row["reservation_days_raw"]).is_integer()
                else (round(float(row["reservation_days_raw"]), 4) if pd.notna(row["reservation_days_raw"]) else None)
            ),
            "bags_remaining": round(float(row["bags_remaining"]), 4),
            "remaining_kg": round(float(row["remaining_kg_value"]), 4) if bool(row["kg_complete"]) else None,
            "remaining_value_gbp": round(float(row["remaining_value_gbp_value"]), 2) if bool(row["value_complete"]) else None,
            "landing_status": _clean_text(row["landing_status"]).title(),
            "landing_date": _clean_text(row["landing_date"]),
            "warehouse": _clean_text(row["warehouse"]),
            "data_status": _clean_text(row["data_status"]),
        }
        for _, row in rows.iterrows()
    ]

    open_reserved_value_available = bool(rows.empty or rows["value_complete"].all())
    landed_value_available = bool(landed_rows.empty or landed_rows["value_complete"].all())
    incoming_value_available = bool(incoming_rows.empty or incoming_rows["value_complete"].all())

    return {
        "summary": {
            "as_of_date": snapshot_date,
            "near_expiry_threshold_days": ACTION_QUEUE_NEAR_EXPIRY_DAYS,
            "open_reservation_rows": int(len(rows)),
            "open_reservations": _unique_reservation_count(rows),
            "open_reserved_bags": round(float(rows["bags_remaining"].sum()), 4),
            "open_reserved_bags_landed": round(float(landed_rows["bags_remaining"].sum()), 4),
            "open_reserved_bags_incoming": round(float(incoming_rows["bags_remaining"].sum()), 4),
            "open_reserved_value_gbp": round(float(rows["remaining_value_gbp_value"].sum()), 2),
            "open_reserved_value_available": open_reserved_value_available,
            "open_reserved_value_landed_gbp": round(float(landed_rows["remaining_value_gbp_value"].sum()), 2),
            "open_reserved_value_landed_available": landed_value_available,
            "open_reserved_value_incoming_gbp": round(float(incoming_rows["remaining_value_gbp_value"].sum()), 2),
            "open_reserved_value_incoming_available": incoming_value_available,
            "near_expiry_rows": int(rows["is_near_expiry"].sum()),
            "near_expiry_reservations": _unique_reservation_count(rows[rows["is_near_expiry"]]),
            "breached_rows": int(rows["is_breached"].sum()),
            "breached_reservations": _unique_reservation_count(rows[rows["is_breached"]]),
            "landed_not_released_value_gbp": round(float(landed_open_rows["remaining_value_gbp_value"].sum()), 2),
            "landed_not_released_value_available": landed_not_released_value_available,
            "landed_not_released_value_status": landed_not_released_value_status,
            "action_now_rows": int(rows["action_now"].sum()),
            "action_now_reservations": _unique_reservation_count(rows[rows["action_now"]]),
            "open_exposure_reservations": _unique_reservation_count(
                rows[rows["action_bucket"] == "Open Exposure"]
            ),
        },
        "action_bucket_counts": action_bucket_counts,
        "open_bags_by_expiry_bucket": expiry_bucket_rows,
        "top_landed_references": {
            "metric": "remaining_value_gbp" if landed_not_released_value_available else "open_bags",
            "metric_label": "Landed Not Released Value" if landed_not_released_value_available else "Landed Not Released Bags",
            "value_available": landed_not_released_value_available,
            "status": (
                "Top references by landed not released value."
                if landed_not_released_value_available
                else "Value incomplete for one or more landed open reservation rows; showing bags instead."
            ),
            "rows": top_landed_reference_rows,
        },
        "details": detail_rows,
    }


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
        "client_summary": {
            **_empty_client_summary(),
        },
        "client_details": [],
        "client_top_exposure": [],
        "client_reference_concentration": [],
        "client_activity_rows": [],
        "client_geography_summary": {
            **_empty_client_geography_summary(),
        },
        "client_geography_locations": [],
        "client_geography_top_countries": [],
        "client_geography_top_cities": [],
        "client_geography_unmapped_clients": [],
        "client_geography_map_clients": [],
        "client_geography_activity_rows": [],
        "client_geography_plot_diagnostics": _empty_client_geography_plot_diagnostics(),
        "reservation_action_queue": _empty_action_queue_dataset(""),
    }


def build_reference_workspace_dataset(
    activity: pd.DataFrame,
    products: pd.DataFrame,
    clients: pd.DataFrame | None = None,
    enable_uk_postcode_service: bool = False,
    uk_postcode_service_config: UKPostcodeServiceConfig | None = None,
    uk_postcode_service_cache_path: Path | None = None,
    geography_resolver: OfflineGeographyResolver | None = None,
) -> dict:
    clients_frame = clients.copy() if clients is not None else pd.DataFrame()
    coordinate_resolver = geography_resolver or OfflineGeographyResolver(
        CLIENT_GEOGRAPHY_COORDINATE_CACHE,
        uk_success_cache_path=uk_postcode_service_cache_path or Path(__file__).with_name("client_geography_service_cache.json"),
        uk_postcode_service_config=uk_postcode_service_config or UKPostcodeServiceConfig(enabled=enable_uk_postcode_service),
    )
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
        (
            client_geography_summary,
            client_geography_locations,
            client_geography_top_countries,
            client_geography_top_cities,
            client_geography_unmapped_clients,
            client_geography_map_clients,
            client_geography_activity_rows,
            client_geography_plot_diagnostics,
        ) = _build_client_geography(pd.DataFrame(), clients_frame, coordinate_resolver)
        empty_dataset["client_geography_summary"] = client_geography_summary
        empty_dataset["client_geography_locations"] = client_geography_locations
        empty_dataset["client_geography_top_countries"] = client_geography_top_countries
        empty_dataset["client_geography_top_cities"] = client_geography_top_cities
        empty_dataset["client_geography_unmapped_clients"] = client_geography_unmapped_clients
        empty_dataset["client_geography_map_clients"] = client_geography_map_clients
        empty_dataset["client_geography_activity_rows"] = client_geography_activity_rows
        empty_dataset["client_geography_plot_diagnostics"] = client_geography_plot_diagnostics
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
        "reservation_days",
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
        (
            client_geography_summary,
            client_geography_locations,
            client_geography_top_countries,
            client_geography_top_cities,
            client_geography_unmapped_clients,
            client_geography_map_clients,
            client_geography_activity_rows,
            client_geography_plot_diagnostics,
        ) = _build_client_geography(pd.DataFrame(), clients_frame)
        empty_dataset["client_geography_summary"] = client_geography_summary
        empty_dataset["client_geography_locations"] = client_geography_locations
        empty_dataset["client_geography_top_countries"] = client_geography_top_countries
        empty_dataset["client_geography_top_cities"] = client_geography_top_cities
        empty_dataset["client_geography_unmapped_clients"] = client_geography_unmapped_clients
        empty_dataset["client_geography_map_clients"] = client_geography_map_clients
        empty_dataset["client_geography_activity_rows"] = client_geography_activity_rows
        empty_dataset["client_geography_plot_diagnostics"] = client_geography_plot_diagnostics
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

    reservations["bags_raw"] = _to_numeric_or_nan_series(reservations, "bags")
    reservations["bags_remaining_raw"] = _to_numeric_or_nan_series(reservations, "bags_remaining")
    reservations["bag_size_kg_raw"] = _to_numeric_or_nan_series(reservations, "bag_size_kg")
    reservations["price_per_kg_raw"] = _to_numeric_or_nan_series(reservations, "price_per_kg")
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
    latest["effective_bags_raw"] = latest["bags_remaining_raw"].where(latest["bags_remaining_raw"] > 0, latest["bags_raw"])

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
    (
        client_summary,
        client_details,
        client_top_exposure,
        client_reference_concentration,
        client_activity_rows,
    ) = _build_client_intelligence(latest)
    (
        client_geography_summary,
        client_geography_locations,
        client_geography_top_countries,
        client_geography_top_cities,
        client_geography_unmapped_clients,
        client_geography_map_clients,
        client_geography_activity_rows,
        client_geography_plot_diagnostics,
    ) = _build_client_geography(latest, clients_frame, coordinate_resolver)
    reservation_action_queue = _build_reservation_action_queue(latest, snapshot_date)
    reservation_action_queue["expired_draft_workflow"] = _build_expired_reservation_draft_workflow(
        latest,
        clients_frame,
        snapshot_date,
    )

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
        "client_summary": client_summary,
        "client_details": client_details,
        "client_top_exposure": client_top_exposure,
        "client_reference_concentration": client_reference_concentration,
        "client_activity_rows": client_activity_rows,
        "client_geography_summary": client_geography_summary,
        "client_geography_locations": client_geography_locations,
        "client_geography_top_countries": client_geography_top_countries,
        "client_geography_top_cities": client_geography_top_cities,
        "client_geography_unmapped_clients": client_geography_unmapped_clients,
        "client_geography_map_clients": client_geography_map_clients,
        "client_geography_activity_rows": client_geography_activity_rows,
        "client_geography_plot_diagnostics": client_geography_plot_diagnostics,
        "reservation_action_queue": reservation_action_queue,
    }

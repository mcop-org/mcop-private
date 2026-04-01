from __future__ import annotations


def _sort_reference_options(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("product_reference") or "").strip().lower(),
            str(row.get("landing_status") or "").strip().lower(),
        ),
    )


def build_product_reference_intelligence_readmodel(dataset: dict[str, object]) -> dict[str, object]:
    return {
        "snapshot_date": str(dataset.get("snapshot_date") or ""),
        "default_reference": str(dataset.get("default_reference") or ""),
        "reference_options": _sort_reference_options(
            [dict(row) for row in list(dataset.get("reference_options") or [])]
        ),
        "summary": [dict(row) for row in list(dataset.get("product_reference_summary") or [])],
        "landing_profile": [dict(row) for row in list(dataset.get("product_landing_profile") or [])],
        "filters": {
            "product_references": sorted(
                {
                    str(row.get("product_reference") or "").strip()
                    for row in list(dataset.get("product_reference_summary") or [])
                    if str(row.get("product_reference") or "").strip()
                },
                key=str.lower,
            ),
        },
    }

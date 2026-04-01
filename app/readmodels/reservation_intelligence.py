from __future__ import annotations


def build_reservation_intelligence_readmodel(dataset: dict[str, object]) -> dict[str, object]:
    details = list(dataset.get("reservation_details") or [])
    references = sorted(
        {
            str(row.get("product_reference") or "").strip()
            for row in details
            if str(row.get("product_reference") or "").strip()
        }
    )
    statuses = sorted(
        {
            str(row.get("request_status") or "").strip()
            for row in details
            if str(row.get("request_status") or "").strip()
        }
    )
    return {
        "snapshot_date": str(dataset.get("snapshot_date") or ""),
        "notes": list(dataset.get("notes") or []),
        "default_reference": str(dataset.get("default_reference") or ""),
        "reference_options": list(dataset.get("reference_options") or []),
        "summary": list(dataset.get("reference_summary") or []),
        "details": details,
        "filters": {
            "product_references": references,
            "statuses": statuses,
        },
    }

from __future__ import annotations

from app.readmodels.product_reference_intelligence import (
    build_product_reference_intelligence_readmodel,
)


def test_product_reference_intelligence_readmodel_preserves_trusted_stock_fields() -> None:
    payload = build_product_reference_intelligence_readmodel(
        {
            "snapshot_date": "2026-03-07",
            "default_reference": "REF-2",
            "reference_options": [
                {"product_reference": "REF-2", "has_reservations": False, "landing_status": "Incoming"},
                {"product_reference": "REF-1", "has_reservations": True, "landing_status": "Landed"},
            ],
            "product_reference_summary": [
                {"product_reference": "REF-2", "stock_health": "Balanced"},
            ],
            "product_landing_profile": [
                {"product_reference": "REF-2", "product_id": "p-2", "landing_status": "Incoming"},
            ],
        }
    )

    assert payload["snapshot_date"] == "2026-03-07"
    assert payload["default_reference"] == "REF-2"
    assert [row["product_reference"] for row in payload["reference_options"]] == ["REF-1", "REF-2"]
    assert payload["summary"] == [{"product_reference": "REF-2", "stock_health": "Balanced"}]
    assert payload["landing_profile"] == [
        {"product_reference": "REF-2", "product_id": "p-2", "landing_status": "Incoming"}
    ]
    assert payload["filters"] == {"product_references": ["REF-2"]}

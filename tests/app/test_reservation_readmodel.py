from __future__ import annotations

from app.readmodels.reservation_intelligence import build_reservation_intelligence_readmodel


def test_reservation_readmodel_shapes_filters() -> None:
    payload = build_reservation_intelligence_readmodel(
        {
            "snapshot_date": "2026-03-03",
            "notes": ["note"],
            "default_reference": "REF-1",
            "reference_options": [],
            "reference_summary": [],
            "reservation_details": [
                {
                    "product_reference": "REF-2",
                    "request_status": "Approved",
                    "company_name": "Alpha",
                    "reservation_key": "r2",
                },
                {
                    "product_reference": "REF-1",
                    "request_status": "Created",
                    "company_name": "Bravo",
                    "reservation_key": "r1",
                },
            ],
        }
    )

    assert payload["filters"]["product_references"] == ["REF-1", "REF-2"]
    assert payload["filters"]["statuses"] == ["Approved", "Created"]

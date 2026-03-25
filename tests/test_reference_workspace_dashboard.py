from __future__ import annotations

from pathlib import Path

from mcop.reference_workspace.dashboard import write_reference_workspace_html


def test_reference_workspace_html_is_deterministic_and_contains_core_ui(tmp_path: Path) -> None:
    dataset = {
        "snapshot_date": "2026-03-07",
        "default_reference": "REF-1",
        "notes": [
            "Reservation completed means all products within the reservation have been released."
        ],
        "reference_options": [
            {"product_reference": "REF-1", "has_reservations": True, "landing_status": "Incoming"},
            {"product_reference": "REF-2", "has_reservations": False, "landing_status": "Landed"},
        ],
        "reference_summary": [
            {
                "product_reference": "REF-1",
                "landing_status": "Incoming",
                "is_landed": False,
                "reservation_row_count": 2,
                "client_count": 2,
                "reserved_bags": 4.0,
                "reserved_kg": 110.0,
                "reserved_value_gbp": 1150.0,
            }
        ],
        "reservation_details": [
            {
                "product_reference": "REF-1",
                "reservation_key": "booking-1",
                "id_request": "r-1",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "contact_first_name": "Ava",
                "contact_last_name": "Stone",
                "request_status": "Completed",
                "request_date": "2026-03-04",
                "approval_date": "2026-03-05",
                "amendment_date": "2026-03-07",
                "landing_status": "Incoming",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
                "bags": 2.0,
                "bags_remaining": 1.0,
                "effective_bags": 1.0,
                "bag_size_kg": 20.0,
                "reserved_kg": 20.0,
                "price_per_kg": 12.5,
                "reserved_value_gbp": 250.0,
            }
        ],
    }
    out = tmp_path / "reference_workspace.html"

    write_reference_workspace_html(out, dataset)
    first = out.read_text(encoding="utf-8")

    write_reference_workspace_html(out, dataset)
    second = out.read_text(encoding="utf-8")

    assert first == second
    assert "<title>MCOP Reference Workspace v1</title>" in first
    assert "Reservation reference drill-down" in first
    assert 'id="reference-search"' in first
    assert 'id="table-filter"' in first
    assert 'data-sort="company_name"' in first
    assert "Reservation completed means all products within the reservation have been released." in first
    assert '"default_reference":"REF-1"' in first
    assert '"product_reference":"REF-2"' in first
    assert 'const landingStatus = row.landing_status || "Unknown";' in first
    assert 'const reservationState = row.has_reservations ? "reservations" : "no reservations";' in first
    assert 'const label = row.product_reference + " - " + landingStatus + " - " + reservationState;' in first
    assert "Latest effective reservation date from the current activity dataset." in first

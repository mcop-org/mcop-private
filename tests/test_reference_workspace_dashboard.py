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
                "landing_date": "2026-03-18",
                "is_landed": False,
                "reservation_row_count": 2,
                "client_count": 2,
                "reserved_bags": 4.0,
                "bags_available": 3.0,
                "reserved_pct": 0.5714,
                "reserved_kg": 110.0,
                "reserved_value_gbp": 1150.0,
            }
        ],
        "reservation_details": [
            {
                "product_reference": "REF-1",
                "reservation_key": "580.0",
                "id_request": "r-1",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
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
    assert '<html lang="en" data-theme="light">' in first
    assert "<title>MCOP Reference Workspace v1</title>" in first
    assert "Reference Workspace" in first
    assert "Reservation detail" in first
    assert 'id="theme-toggle"' in first
    assert 'id="reference-search"' in first
    assert 'id="table-filter"' in first
    assert 'data-sort="company_name"' in first
    assert '"default_reference":"REF-1"' in first
    assert '"product_reference":"REF-2"' in first
    assert 'const reservationState = row.has_reservations ? "Reservations live" : "No reservations";' in first
    assert 'const label = row.product_reference + " | " + landingStatus + " | " + reservationState;' in first
    assert "Snapshot: <strong>2026-03-07</strong>" in first
    assert 'id="kpi-reserved-pct"' in first
    assert 'id="kpi-available-bags"' in first
    assert "Landing Status" in first
    assert 'id="kpi-landing-status"' in first
    assert 'id="kpi-landing-meta"' in first
    assert 'id="kpi-rows"' not in first
    assert 'grid-template-columns: repeat(5, minmax(0, 1fr));' in first
    assert 'function buildLandingMeta(summary)' in first
    assert 'function formatReservationKey(value)' in first
    assert 'const reservationKey = formatReservationKey(row.reservation_key || row.id_request || "-");' in first
    assert 'return formatNumber(number, 0);' in first
    assert '"reservation_key":"580.0"' in first
    assert 'landingStatus.textContent = titleCaseWords(summary.landing_status || "Unknown") || "Unknown";' in first
    assert 'id="selected-reference-value"' in first
    assert "Search reservation rows" in first
    assert 'localStorage.getItem("mcop-reference-workspace-theme")' in first
    assert 'id="selected-reference-chip"' in first
    assert "Built from the latest reservation activity included in this workspace." not in first
    assert "Standalone reservation reference review" not in first
    assert "Selected Reference" not in first
    assert 'id="reservation-note"' not in first
    assert "contact_first_name" not in first
    assert "contact_last_name" not in first

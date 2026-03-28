from __future__ import annotations

from pathlib import Path

from mcop.reference_workspace.dashboard import write_reference_workspace_html


def test_reference_workspace_html_is_deterministic_and_keeps_safe_tabbed_shell(tmp_path: Path) -> None:
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
    assert '<html lang="en" data-theme="light">' in first
    assert "<title>MCOP Reference Workspace v1</title>" in first
    assert "Reference Workspace" in first
    assert 'id="theme-toggle"' in first
    assert 'id="reference-search"' in first
    assert 'id="selected-reference-chip"' in first
    assert 'id="selected-reference-value"' in first
    assert 'id="tab-reservation"' in first
    assert 'id="tab-product"' in first
    assert 'data-tab="reservation"' in first
    assert 'data-tab="product"' in first
    assert 'activeTab: "reservation"' in first
    assert 'id="reservation-view"' in first
    assert 'id="product-view" hidden' in first
    assert "Reservation Intelligence" in first
    assert "Product Reference Intelligence" in first
    assert "Metrics withheld pending verified business logic" in first
    assert "Released, open, and profile-level product reference metrics are not shown here" in first
    assert 'id="table-filter"' in first
    assert "Search reservation rows" in first
    assert 'data-sort="company_name"' in first
    assert 'data-sort="request_status"' in first
    assert 'data-sort="effective_bags"' in first
    assert 'data-sort="reserved_kg"' in first
    assert 'data-sort="reserved_value_gbp"' in first
    assert 'data-sort="landing_status"' in first
    assert 'data-sort="landing_date"' in first
    assert 'data-sort="warehouse"' in first
    assert 'data-sort="reservation_key"' in first
    assert 'id="reservation-kpi-kg"' in first
    assert 'id="reservation-kpi-value"' in first
    assert 'id="reservation-kpi-reserved-pct"' in first
    assert 'id="reservation-kpi-available-bags"' in first
    assert 'id="reservation-kpi-clients"' in first
    assert 'id="reservation-kpi-landing-status"' in first
    assert 'id="reservation-kpi-landing-support"' in first
    assert '"default_reference":"REF-1"' in first
    assert '"product_reference":"REF-2"' in first
    assert 'const reservationState = row.has_reservations ? "Reservations live" : "No reservations";' in first
    assert 'const label = row.product_reference + " | " + landingStatus + " | " + reservationState;' in first
    assert "Snapshot: <strong>2026-03-07</strong>" in first
    assert 'function formatPercent(value)' in first
    assert 'function formatReservationKey(value)' in first
    assert 'function renderStatusChip(value)' in first
    assert 'function landingSupportText(summary, rows)' in first
    assert 'const reservationKey = formatReservationKey(row.reservation_key || row.id_request || "-");' in first
    assert 'return formatNumber(number, 0);' in first
    assert '"reservation_key":"580.0"' in first
    assert 'localStorage.getItem("mcop-reference-workspace-theme")' in first
    assert 'reservationView.hidden = !reservationActive;' in first
    assert 'productView.hidden = reservationActive;' in first
    assert "grid-template-columns: repeat(5, minmax(0, 1fr));" in first
    assert "@media (max-width: 1280px)" in first
    assert ".pill.status-warm" in first
    assert ".pill.status-good" in first
    assert 'if (status === "incoming" || status === "created")' in first
    assert 'if (status === "landed" || status === "completed")' in first
    assert 'selectedReferenceChipEl.innerHTML =' in first
    assert 'landingStatus.innerHTML = renderStatusChip(summary.landing_status || "-");' in first
    assert '"<td>" + renderStatusChip(row.landing_status || "-") + "</td>" +' in first
    assert '"<td>" + renderStatusChip(row.request_status || "-") + "</td>" +' in first
    assert 'return "Expected on " + landingLabel + ", in " + formatNumber(diff, 0) + " days.";' in first
    assert 'return "Recorded as landed on " + landingLabel + ", " + formatNumber(daysSinceLanding, 0) + " days ago.";' in first
    assert 'return "Landing date not available for this reference.";' in first
    assert '"reference_profiles"' not in first
    assert "Reference Intelligence Workspace" not in first
    assert "Latest non-rejected reservation row per reservation key" not in first
    assert 'id="reservation-note"' not in first
    assert "Distinct clients attached to the selected reservation reference." not in first
    assert "Landing status carried on the reservation reference rows." not in first
    assert "reservation-kpi-rows" not in first
    assert ">Company</button>" in first
    assert ">Client</button>" not in first
    assert 'id="product-kpi-incoming"' not in first
    assert 'id="product-kpi-landed"' not in first
    assert 'id="product-kpi-reserved"' not in first
    assert 'id="product-kpi-released"' not in first
    assert 'id="product-kpi-open"' not in first
    assert 'id="product-detail-body"' not in first
    assert "Current phase-2 reference metrics for the selected product reference." not in first
    assert "Released Bags" not in first
    assert "Open Value GBP" not in first

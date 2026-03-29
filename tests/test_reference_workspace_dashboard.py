from __future__ import annotations

from pathlib import Path

from mcop.reference_workspace.dashboard import write_reference_workspace_html


def test_reference_workspace_html_is_deterministic_and_keeps_safe_tabbed_shell(tmp_path: Path) -> None:
    dataset = {
        "snapshot_date": "2026-03-07",
        "default_reference": "REF-1",
        "default_landed_reference": "REF-2",
        "notes": [
            "Reservation completed means all products within the reservation have been released."
        ],
        "reference_options": [
            {"product_reference": "REF-1", "has_reservations": True, "landing_status": "Incoming"},
            {"product_reference": "REF-2", "has_reservations": False, "landing_status": "Landed"},
        ],
        "landed_reference_options": [
            {"product_reference": "REF-2"},
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
        "product_reference_summary": [
            {
                "product_reference": "REF-1",
                "incoming_bags": 4.0,
                "incoming_bags_available": True,
                "incoming_kg": 120.0,
                "incoming_kg_available": True,
                "landed_bags": 2.0,
                "landed_bags_available": True,
                "landed_kg": 40.0,
                "landed_kg_available": True,
                "landed_available_bags": 1.0,
                "landed_available_bags_available": True,
                "landed_available_kg": 20.0,
                "landed_available_kg_available": True,
                "stock_health": "Mostly Incoming",
            },
            {
                "product_reference": "REF-2",
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
            },
        ],
        "product_landing_profile": [
            {
                "product_reference": "REF-1",
                "product_id": "p-2",
                "landing_status": "Landed",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
                "bags": 2.0,
                "bag_size_kg": 20.0,
                "total_kg": 40.0,
                "bags_available": 1.0,
                "available_kg": 20.0,
            },
            {
                "product_reference": "REF-1",
                "product_id": "p-1",
                "landing_status": "Incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
                "bags": 4.0,
                "bag_size_kg": 30.0,
                "total_kg": 120.0,
                "bags_available": 2.0,
                "available_kg": 60.0,
            },
        ],
        "landed_stock_summary": {
            "as_of_date": "2026-03-07",
            "landed_bags": 10.0,
            "unsold_landed_bags": 3.0,
            "unsold_landed_kg": 80.0,
            "unsold_landed_kg_available": True,
            "aged_180_plus_bags": 1.0,
            "warehouses_exposed": 2,
            "unsold_landed_value_gbp": 910.0,
            "unsold_landed_value_available": False,
            "value_completeness_status": "Unavailable on 1 unsold landed row(s) due to missing kg or price.",
        },
        "landed_stock_aging": [
            {"aging_bucket": "0-30", "unsold_bags": 1.0},
            {"aging_bucket": "31-60", "unsold_bags": 0.0},
            {"aging_bucket": "61-90", "unsold_bags": 2.0},
            {"aging_bucket": "91-180", "unsold_bags": 0.0},
            {"aging_bucket": "181-270", "unsold_bags": 0.0},
            {"aging_bucket": "270+", "unsold_bags": 0.0},
        ],
        "landed_stock_warehouse_exposure": [
            {"warehouse": "Bristol", "unsold_bags": 2.0, "unsold_kg": 40.0},
            {"warehouse": "London", "unsold_bags": 1.0, "unsold_kg": 40.0},
        ],
        "landed_stock_reference_exposure": [
            {"product_reference": "REF-1", "unsold_bags": 2.0, "unsold_kg": 40.0},
            {"product_reference": "REF-2", "unsold_bags": 1.0, "unsold_kg": 40.0},
        ],
        "landed_stock_details": [
            {
                "product_reference": "REF-1",
                "product_id": "p-2",
                "warehouse": "Bristol",
                "landing_date": "2025-12-30",
                "days_since_landing": 67,
                "aging_bucket": "61-90",
                "landed_bags": 2.0,
                "unsold_bags": 2.0,
                "unsold_kg": 40.0,
                "unsold_value_gbp": 500.0,
                "data_status": "Complete",
            },
            {
                "product_reference": "REF-2",
                "product_id": "p-3",
                "warehouse": "London",
                "landing_date": "2026-02-20",
                "days_since_landing": 15,
                "aging_bucket": "0-30",
                "landed_bags": 8.0,
                "unsold_bags": 1.0,
                "unsold_kg": 40.0,
                "unsold_value_gbp": None,
                "data_status": "Unsold value unavailable",
            },
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
    assert 'id="tab-landed"' in first
    assert 'data-tab="reservation"' in first
    assert 'data-tab="product"' in first
    assert 'data-tab="landed"' in first
    assert 'activeTab: "reservation"' in first
    assert 'id="reservation-view"' in first
    assert 'id="product-view" hidden' in first
    assert 'id="landed-view" hidden' in first
    assert "Reservation Intelligence" in first
    assert "Product Reference Intelligence" in first
    assert "Landed Stock Intelligence" in first
    assert "Stock-only view of whether the selected reference looks early-stage, balanced, or at risk of landed build-up." in first
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
    assert 'id="product-kpi-incoming"' in first
    assert 'id="product-kpi-incoming-kg"' in first
    assert 'id="product-kpi-landed"' in first
    assert 'id="product-kpi-landed-kg"' in first
    assert 'id="product-kpi-available"' in first
    assert 'id="product-kpi-available-kg"' in first
    assert 'id="product-kpi-health"' in first
    assert 'id="product-kpi-health-meta"' in first
    assert 'id="product-detail-body"' in first
    assert 'id="landed-kpi-unsold-bags"' in first
    assert 'id="landed-kpi-unsold-kg"' in first
    assert 'id="landed-kpi-aged-bags"' in first
    assert 'id="landed-kpi-warehouses"' in first
    assert 'id="landed-kpi-value"' in first
    assert 'id="landed-aging-chart"' in first
    assert 'id="landed-warehouse-chart"' in first
    assert 'id="landed-reference-chart"' in first
    assert 'id="landed-table-filter"' in first
    assert 'id="landed-warehouse-filter"' in first
    assert 'id="landed-aging-filter"' in first
    assert 'id="landed-status-filter"' in first
    assert 'id="landed-detail-body"' in first
    assert '"default_reference":"REF-1"' in first
    assert '"default_landed_reference":"REF-2"' in first
    assert '"landed_reference_options":[{"product_reference":"REF-2"}]' in first
    assert '"product_reference":"REF-2"' in first
    assert '"product_id":"p-1"' in first
    assert 'const reservationState = row.has_reservations ? "Reservations live" : "No reservations";' in first
    assert 'const label = row.product_reference + " | " + landingStatus + " | " + reservationState;' in first
    assert 'const LANDED_AGING_BUCKETS = ["0-30", "31-60", "61-90", "91-180", "181-270", "270+"];' in first
    assert "Snapshot: <strong>2026-03-07</strong>" in first
    assert 'function formatPercent(value)' in first
    assert 'function formatReservationKey(value)' in first
    assert 'function renderStatusChip(value)' in first
    assert 'function landingSupportText(summary, rows)' in first
    assert 'function canonicalAgingBucket(value)' in first
    assert 'const reservationKey = formatReservationKey(row.reservation_key || row.id_request || "-");' in first
    assert 'return formatNumber(number, 0);' in first
    assert '"reservation_key":"580.0"' in first
    assert 'localStorage.getItem("mcop-reference-workspace-theme")' in first
    assert 'reservationView.hidden = !reservationActive;' in first
    assert 'productView.hidden = !productActive;' in first
    assert 'landedView.hidden = !landedActive;' in first
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
    assert 'function renderProductKpis()' in first
    assert 'function renderProductTable()' in first
    assert 'function renderLandedKpis()' in first
    assert 'function renderLandedCharts()' in first
    assert 'function renderLandedTable()' in first
    assert 'function currentLandedDetails()' in first
    assert 'function renderBarChart(containerId, emptyId, rows, labelKey, valueKey, formatter, showZeroRows = false)' in first
    assert 'return "Unavailable";' in first
    assert 'const rows = productDetailsByReference.get(state.selectedReference) || [];' in first
    assert 'const landedSummary = data.landed_stock_summary || {};' in first
    assert 'const landedReferenceOptions = Array.isArray(data.landed_reference_options) ? data.landed_reference_options : [];' in first
    assert 'const landedAgingRaw = Array.isArray(data.landed_stock_aging) ? data.landed_stock_aging : [];' in first
    assert 'const landedAging = LANDED_AGING_BUCKETS.map((bucket) => ({' in first
    assert 'const landedWarehouseExposure = Array.isArray(data.landed_stock_warehouse_exposure) ? data.landed_stock_warehouse_exposure : [];' in first
    assert 'const landedReferenceExposure = Array.isArray(data.landed_stock_reference_exposure) ? data.landed_stock_reference_exposure : [];' in first
    assert 'const landedDetails = Array.isArray(data.landed_stock_details) ? data.landed_stock_details : [];' in first
    assert 'return state.activeTab === "landed"' in first
    assert 'state.landedSelectedReference = value;' in first
    assert 'canonicalAgingBucket(row.aging_bucket) !== state.landedAgingBucket' in first
    assert 'renderBarChart("landed-aging-chart", "landed-aging-empty", landedAging, "aging_bucket", "unsold_bags", (value) => formatNumber(value, 0) + " bags", true);' in first
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
    assert 'id="product-kpi-reserved"' not in first
    assert 'id="product-kpi-released"' not in first
    assert 'id="product-kpi-open"' not in first
    assert 'id="product-kpi-clients"' not in first
    assert 'id="product-kpi-clients-meta"' not in first
    assert 'id="product-clients-list"' not in first
    assert "Stock and client linkage shown here come only from the approved safe product and reservation fields." not in first
    assert "Current Stock Exposure by Lot/Warehouse" in first
    assert "Days Since Landing / Not landed" in first
    assert "Landed Available" in first
    assert "Stock Health" in first
    assert "Landed Available Exposure" in first
    assert "Aging Exposure" in first
    assert "Warehouse Exposure" in first
    assert "Largest Unsold References" in first
    assert "Unsold Landed Bags" in first
    assert "Aged 180+ Bags" in first
    assert "Unsold Landed Value" in first
    assert 'health.innerHTML = renderStatusChip(summary.stock_health || "Data Incomplete");' in first
    assert 'daysLabel = "Not landed";' in first
    assert 'renderLandedKpis();' in first
    assert 'renderLandedCharts();' in first
    assert 'renderLandedTable();' in first
    assert '"landed_stock_summary":{"aged_180_plus_bags":1.0,"as_of_date":"2026-03-07"' in first
    assert "Released Bags" not in first
    assert "Open Value GBP" not in first
    assert "Sell-through" not in first

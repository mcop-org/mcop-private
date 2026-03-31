from __future__ import annotations

from pathlib import Path

from mcop.reference_workspace.dashboard import write_reference_workspace_html


def render_html(dataset: dict) -> str:
    out = Path("reference_workspace_test.html")
    write_reference_workspace_html(out, dataset)
    try:
        return out.read_text(encoding="utf-8")
    finally:
        out.unlink(missing_ok=True)


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
        "client_summary": {
            "clients_with_current_exposure": 2,
            "total_current_reserved_value_gbp": 1150.0,
            "total_current_reserved_value_available": True,
            "largest_client_company_name": "Alpha Roasters",
            "largest_client_id": "c-1",
            "largest_client_reserved_value_gbp": 900.0,
            "largest_client_reserved_value_available": True,
            "clients_concentrated_in_one_reference": 1,
        },
        "client_details": [
            {
                "company_name": "Alpha Roasters",
                "client_id": "c-1",
                "reservation_row_count": 2,
                "reserved_bags": 3.0,
                "reserved_kg": 90.0,
                "reserved_value_gbp": 900.0,
                "reserved_value_available": True,
                "distinct_reference_count": 1,
                "primary_reference": "REF-1",
                "primary_reference_share": 1.0,
                "primary_reference_share_available": True,
                "landing_mix": "Incoming",
            },
            {
                "company_name": "Bravo Coffee",
                "client_id": "c-2",
                "reservation_row_count": 1,
                "reserved_bags": 1.0,
                "reserved_kg": 20.0,
                "reserved_value_gbp": 250.0,
                "reserved_value_available": True,
                "distinct_reference_count": 1,
                "primary_reference": "REF-1",
                "primary_reference_share": 1.0,
                "primary_reference_share_available": True,
                "landing_mix": "Landed",
            },
        ],
        "client_top_exposure": [
            {"company_name": "Alpha Roasters", "client_id": "c-1", "reserved_value_gbp": 900.0},
            {"company_name": "Bravo Coffee", "client_id": "c-2", "reserved_value_gbp": 250.0},
        ],
        "client_reference_concentration": [
            {"company_name": "Alpha Roasters", "client_id": "c-1", "product_reference": "REF-1", "reserved_value_gbp": 900.0},
            {"company_name": "Bravo Coffee", "client_id": "c-2", "product_reference": "REF-1", "reserved_value_gbp": 250.0},
        ],
        "client_activity_rows": [
            {
                "company_name": "Alpha Roasters",
                "client_id": "c-1",
                "client_key": "c-1",
                "product_reference": "REF-1",
                "request_date": "2026-03-04",
                "request_date_available": True,
                "landing_status": "Incoming",
                "effective_bags": 1.0,
                "reserved_kg": 20.0,
                "reserved_value_gbp": 250.0,
                "reserved_value_available": True,
            }
        ],
        "reservation_action_queue": {
            "summary": {
                "as_of_date": "2026-03-07",
                "near_expiry_threshold_days": 7,
                "open_reservation_rows": 2,
                "open_reservations": 2,
                "open_reserved_bags": 3.0,
                "open_reserved_bags_landed": 1.0,
                "open_reserved_bags_incoming": 2.0,
                "open_reserved_value_gbp": 750.0,
                "open_reserved_value_available": True,
                "open_reserved_value_landed_gbp": 250.0,
                "open_reserved_value_landed_available": True,
                "open_reserved_value_incoming_gbp": 500.0,
                "open_reserved_value_incoming_available": True,
                "near_expiry_rows": 1,
                "near_expiry_reservations": 1,
                "breached_rows": 0,
                "breached_reservations": 0,
                "landed_not_released_value_gbp": 250.0,
                "landed_not_released_value_available": True,
                "landed_not_released_value_status": "Complete across all landed open reservation rows.",
                "action_now_rows": 2,
                "action_now_reservations": 2,
                "open_exposure_reservations": 0,
            },
            "action_bucket_counts": [
                {"action_bucket": "Breached", "row_count": 0},
                {"action_bucket": "Near Expiry", "row_count": 1},
                {"action_bucket": "Landed Not Approved", "row_count": 0},
                {"action_bucket": "Landed Not Released", "row_count": 1},
                {"action_bucket": "Open Exposure", "row_count": 0},
            ],
            "open_bags_by_expiry_bucket": [
                {"expiry_bucket": "Breached", "open_bags": 0.0},
                {"expiry_bucket": "0-7 days", "open_bags": 2.0},
                {"expiry_bucket": "8+ days", "open_bags": 0.0},
                {"expiry_bucket": "No expiry data", "open_bags": 1.0},
            ],
            "top_landed_references": {
                "metric": "remaining_value_gbp",
                "metric_label": "Landed Not Released Value",
                "value_available": True,
                "status": "Top references by landed not released value.",
                "rows": [
                    {
                        "product_reference": "REF-1",
                        "open_bags": 1.0,
                        "remaining_kg": 20.0,
                        "remaining_value_gbp": 250.0,
                    }
                ],
            },
            "details": [
                {
                    "action_priority": "P2 Near Expiry",
                    "action_priority_rank": 2,
                    "action_bucket": "Near Expiry",
                    "days_to_expiry": 2,
                    "expiry_date": "2026-03-09",
                    "company_name": "Alpha Roasters",
                    "client_id": "c-1",
                    "reservation_key": "580.0",
                    "product_reference": "REF-1",
                    "product_id": "p-1",
                    "request_status": "Approved",
                    "approval_date": "2026-03-05",
                    "reservation_days": 4,
                    "bags_remaining": 2.0,
                    "remaining_kg": 40.0,
                    "remaining_value_gbp": 500.0,
                    "landing_status": "Incoming",
                    "landing_date": "2026-03-18",
                    "warehouse": "Bristol",
                    "data_status": "Complete",
                }
            ],
        },
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
    assert 'class="topbar-brand"' in first
    assert 'class="brand-mark"' in first
    assert 'class="brand-logo brand-logo-light"' in first
    assert 'class="brand-logo brand-logo-dark"' in first
    assert "data:image/png;base64," in first
    assert 'id="theme-toggle"' in first
    assert 'class="workspace-shell"' in first
    assert 'class="workspace-sidebar panel"' in first
    assert 'class="workspace-main"' in first
    assert "Workspace navigation" in first
    assert "Modules" in first
    assert 'id="shared-selector-panel"' in first
    assert 'id="reference-search"' in first
    assert 'id="selected-reference-chip"' in first
    assert 'id="selected-reference-value"' in first
    assert 'id="shared-selector-reset"' in first
    assert 'id="landed-reset"' in first
    assert 'id="tab-reservation"' in first
    assert 'id="tab-product"' in first
    assert 'id="tab-client"' in first
    assert 'id="tab-landed"' in first
    assert 'id="tab-action"' in first
    assert 'data-tab="reservation"' in first
    assert 'data-tab="product"' in first
    assert 'data-tab="client"' in first
    assert 'data-tab="landed"' in first
    assert 'data-tab="action"' in first
    assert 'class="module-nav-button is-active"' in first
    assert 'activeTab: "reservation"' in first
    assert 'id="reservation-view"' in first
    assert 'id="product-view" hidden' in first
    assert 'id="client-view" hidden' in first
    assert 'id="landed-view" hidden' in first
    assert 'id="action-view" hidden' in first
    assert "Reservation Intelligence" in first
    assert "Product Reference Intelligence" in first
    assert "Client Intelligence" in first
    assert "Landed Stock Intelligence" in first
    assert "Reservation Risk / Action Queue" in first
    assert "Reservation activity view, excluding rejected reservations." in first
    assert "Request Date" in first
    assert 'id="client-date-preset"' in first
    assert 'id="client-date-from-shell" hidden' in first
    assert 'id="client-date-to-shell" hidden' in first
    assert 'id="client-date-from"' in first
    assert 'id="client-date-to"' in first
    assert "All request dates" in first
    assert "Last 30 days" in first
    assert "Last 90 days" in first
    assert "Month to date" in first
    assert "Financial year to date" in first
    assert "Custom range" in first
    assert "Quarter to date" not in first
    assert "Clients With Reservation Activity" in first
    assert "Recorded Reservation Value" in first
    assert "Largest Recorded Reservation Value" in first
    assert "Clients Concentrated In One Reference" in first
    assert "Client Concentration" in first
    assert "Top Clients by Recorded Reservation Value" in first
    assert "Recorded Reservation Value by Client and Reference" in first
    assert "Ranks clients by recorded reservation value for the selected request-date range." in first
    assert "Shows how recorded reservation value is distributed across product references for the selected date range." in first
    assert "Reserved Bags Recorded" in first
    assert "Reserved KG Recorded" in first
    assert "Reserved Value GBP Recorded" in first
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
    assert 'id="client-kpi-count"' in first
    assert 'id="client-kpi-total-value"' in first
    assert 'id="client-kpi-largest-value"' in first
    assert 'id="client-kpi-concentrated"' in first
    assert 'id="client-kpi-top-five-share"' in first
    assert 'id="client-kpi-top-ten-share"' in first
    assert 'id="client-kpi-rest-share"' in first
    assert 'id="client-exposure-chart"' in first
    assert 'id="client-concentration-chart"' in first
    assert 'id="client-table-filter"' in first
    assert 'id="client-concentration-filter"' in first
    assert 'id="client-detail-body"' in first
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
    assert 'id="action-kpi-open-reservations"' in first
    assert 'id="action-kpi-open-bags"' in first
    assert 'id="action-kpi-open-bags-landed"' in first
    assert 'id="action-kpi-open-bags-incoming"' in first
    assert 'id="action-kpi-near-expiry-reservations"' in first
    assert 'id="action-kpi-breached-reservations"' in first
    assert 'id="action-kpi-open-value"' in first
    assert 'id="action-kpi-open-value-landed"' in first
    assert 'id="action-kpi-open-value-incoming"' in first
    assert 'id="action-kpi-open-exposure-reservations"' in first
    assert 'id="action-kpi-action-now-reservations"' in first
    assert 'id="action-bucket-chart"' in first
    assert 'id="action-expiry-chart"' in first
    assert 'id="action-reference-chart"' in first
    assert 'id="action-table-filter"' in first
    assert 'id="action-bucket-filter"' in first
    assert 'id="action-landing-filter"' in first
    assert 'id="action-data-filter"' in first
    assert 'id="action-detail-body"' in first
    assert '"default_reference":"REF-1"' in first
    assert '"default_landed_reference":"REF-2"' in first
    assert '"landed_reference_options":[{"product_reference":"REF-2"}]' in first
    assert '"client_activity_rows":[' in first
    assert '"reservation_action_queue":{' in first
    assert '"client_key":"c-1"' in first
    assert '"request_date":"2026-03-04"' in first
    assert '"request_date_available":true' in first
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
    assert "grid-template-columns: 228px minmax(0, 1fr);" in first
    assert ".action-kpi-grid {" in first
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in first
    assert "@media (max-width: 1280px)" in first
    assert "@media (max-width: 900px)" in first
    assert ".pill.status-warm" in first
    assert ".pill.status-good" in first
    assert ".pill.status-bad" in first
    assert 'if (status === "landed not approved" || status === "p3 landed not approved" || status === "breached" || status === "p1 breached")' in first
    assert 'if (status === "incoming" || status === "created")' in first
    assert 'if (status === "landed" || status === "completed")' in first
    assert "Default order shows breached first, then near-expiry, then landed-not-approved, then landed-not-released, then other open exposure." in first
    assert 'const bucketOptions = ["all", "Breached", "Near Expiry", "Landed Not Approved", "Landed Not Released", "Open Exposure"];' in first
    assert 'openReservations.textContent = formatNumber(actionSummary.open_reservations || 0, 0);' in first
    assert 'openBagsLanded.textContent = "Landed: " + formatBags(actionSummary.open_reserved_bags_landed || 0);' in first
    assert 'openBagsIncoming.textContent = "Incoming: " + formatBags(actionSummary.open_reserved_bags_incoming || 0);' in first
    assert 'nearExpiry.textContent = formatNumber(actionSummary.near_expiry_reservations || 0, 0);' in first
    assert 'breached.textContent = formatNumber(actionSummary.breached_reservations || 0, 0);' in first
    assert 'openValue.textContent = actionSummary.open_reserved_value_available' in first
    assert 'actionSummary.open_reserved_value_landed_available' in first
    assert 'actionSummary.open_reserved_value_incoming_available' in first
    assert 'openExposure.textContent = formatNumber(actionSummary.open_exposure_reservations || 0, 0);' in first
    assert 'actionNow.textContent = formatNumber(actionSummary.action_now_reservations || 0, 0);' in first
    assert 'selectedReferenceChipEl.innerHTML =' in first
    assert 'landingStatus.innerHTML = renderStatusChip(summary.landing_status || "-");' in first
    assert '"<td>" + renderStatusChip(row.landing_status || "-") + "</td>" +' in first
    assert '"<td>" + renderStatusChip(row.request_status || "-") + "</td>" +' in first
    assert 'function renderProductKpis()' in first
    assert 'function renderProductTable()' in first
    assert 'function renderClientKpis()' in first
    assert 'function renderClientCharts()' in first
    assert 'function renderClientTable()' in first
    assert 'function financialYearStart(value)' in first
    assert 'const year = anchor.getUTCMonth() >= 7 ? anchor.getUTCFullYear() : anchor.getUTCFullYear() - 1;' in first
    assert 'return isoFromDate(new Date(Date.UTC(year, 7, 1)));' in first
    assert 'if (state.clientDatePreset === "financial-year-to-date")' in first
    assert 'if (state.clientDatePreset === "month-to-date")' in first
    assert 'if (state.clientDatePreset === "last-30")' in first
    assert 'if (state.clientDatePreset === "last-90")' in first
    assert 'renderClientDateControls();' in first
    assert 'function renderStackedBarChart(containerId, emptyId, clients, segments)' in first
    assert 'function renderLandedKpis()' in first
    assert 'function renderLandedCharts()' in first
    assert 'function renderLandedTable()' in first
    assert 'function currentLandedDetails()' in first
    assert 'function resetSharedSelectorView()' in first
    assert 'function resetLandedView()' in first
    assert 'function renderBarChart(containerId, emptyId, rows, labelKey, valueKey, formatter, showZeroRows = false)' in first
    assert 'return "Unavailable";' in first
    assert 'const rows = productDetailsByReference.get(state.selectedReference) || [];' in first
    assert 'const landedSummary = data.landed_stock_summary || {};' in first
    assert 'const landedAgingRaw = Array.isArray(data.landed_stock_aging) ? data.landed_stock_aging : [];' in first
    assert 'const landedAging = LANDED_AGING_BUCKETS.map((bucket) => ({' in first
    assert 'const landedWarehouseExposure = Array.isArray(data.landed_stock_warehouse_exposure) ? data.landed_stock_warehouse_exposure : [];' in first
    assert 'const landedReferenceExposure = Array.isArray(data.landed_stock_reference_exposure) ? data.landed_stock_reference_exposure : [];' in first
    assert 'const landedDetails = Array.isArray(data.landed_stock_details) ? data.landed_stock_details : [];' in first
    assert 'canonicalAgingBucket(row.aging_bucket) !== state.landedAgingBucket' in first
    assert 'renderBarChart("landed-aging-chart", "landed-aging-empty", landedAging, "aging_bucket", "unsold_bags", (value) => formatNumber(value, 0) + " bags", true);' in first
    assert 'sharedSelectorPanel.hidden = landedActive || clientActive || actionActive;' in first
    assert 'state.selectedReference = "";' in first
    assert 'state.filterText = "";' in first
    assert 'state.sortKey = "company_name";' in first
    assert 'state.sortDirection = "asc";' in first
    assert 'tableFilter.value = "";' in first
    assert 'state.landedFilterText = "";' in first
    assert 'state.landedWarehouse = "all";' in first
    assert 'state.landedAgingBucket = "all";' in first
    assert 'state.landedStatus = "all";' in first
    assert 'landedTableFilter.value = "";' in first
    assert 'landedWarehouseFilter.value = "all";' in first
    assert 'landedAgingFilter.value = "all";' in first
    assert 'landedStatusFilter.value = "all";' in first
    assert 'sharedSelectorResetButton.addEventListener("click", () => {' in first
    assert 'clientTableFilter.addEventListener("input", () => {' in first
    assert 'clientConcentrationFilter.addEventListener("change", () => {' in first
    assert 'landedResetButton.addEventListener("click", () => {' in first
    assert 'return "Expected on " + landingLabel + ", in " + formatNumber(diff, 0) + " days.";' in first
    assert 'return "Recorded as landed on " + landingLabel + ", " + formatNumber(daysSinceLanding, 0) + " days ago.";' in first
    assert 'return "Landing date not available for this reference.";' in first
    assert 'const selectedReference = currentSelectedReference() || "Select product";' in first
    assert 'const landingStatus = currentSelectedReference() ? (summary?.landing_status || "Unknown") : "Not selected";' in first
    assert 'sharedSelectorPanel.hidden = landedActive || clientActive || actionActive;' in first
    assert 'state.activeTab = button.dataset.tab || "reservation";' in first
    assert 'const tabButtons = Array.from(document.querySelectorAll(".module-nav-button"));' in first
    assert 'summaryByReference.get(state.selectedReference);' in first
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
    assert "Stock Details by Lot / Warehouse" in first
    assert "Days Since Landing / Not landed" in first
    assert 'state.landedSelectedReference' not in first
    assert 'function currentOptionRows()' not in first
    assert "Landed Available" in first
    assert "Stock Health" in first
    assert "Landed Exposure Details" in first
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
    assert 'renderClientKpis();' in first
    assert 'renderClientCharts();' in first
    assert 'renderClientTable();' in first
    assert 'topFiveShare.textContent = formatPercent(clientMetrics.summary.concentration_top_five_share);' in first
    assert 'topTenShare.textContent = "Top 10: " + formatPercent(clientMetrics.summary.concentration_top_ten_share);' in first
    assert 'restShare.textContent = "Rest: " + formatPercent(clientMetrics.summary.concentration_rest_share);' in first
    assert 'topFiveShare.textContent = "No concentration view";' in first
    assert 'topTenShare.textContent = "Top 10: unavailable for this range";' in first
    assert 'restShare.textContent = "Rest: unavailable for this range";' in first
    assert 'concentration_share_available: false,' in first
    assert 'const filteredRows = currentClientActivityRows();' in first
    assert 'summary: clientSummary,' not in first
    assert 'details: clientDetails,' not in first
    assert 'topExposure: clientTopExposure,' not in first
    assert 'concentration: clientReferenceConcentration,' not in first
    assert '"landed_stock_summary":{"aged_180_plus_bags":1.0,"as_of_date":"2026-03-07"' in first
    assert '"client_summary":{"clients_concentrated_in_one_reference":1,"clients_with_current_exposure":2,"largest_client_company_name":"Alpha Roasters"' in first
    assert "Released Bags" not in first
    assert "Open Value GBP" not in first
    assert "Sell-through" not in first


def test_reference_workspace_client_concentration_contract_present() -> None:
    dataset = {
        "snapshot_date": "2026-03-07",
        "default_reference": "",
        "default_landed_reference": "",
        "notes": [],
        "reference_options": [],
        "landed_reference_options": [],
        "reference_summary": [],
        "reservation_details": [],
        "product_reference_summary": [],
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
            "value_completeness_status": "",
        },
        "landed_stock_aging": [],
        "landed_stock_warehouse_exposure": [],
        "landed_stock_reference_exposure": [],
        "landed_stock_details": [],
        "client_summary": {
            "clients_with_current_exposure": 6,
            "total_current_reserved_value_gbp": 2100.0,
            "total_current_reserved_value_available": True,
            "largest_client_company_name": "Alpha Roasters",
            "largest_client_id": "c-1",
            "largest_client_reserved_value_gbp": 700.0,
            "largest_client_reserved_value_available": True,
            "clients_concentrated_in_one_reference": 2,
        },
        "client_details": [],
        "client_top_exposure": [],
        "client_reference_concentration": [],
        "client_activity_rows": [
            {
                "company_name": "Alpha Roasters",
                "client_id": "c-1",
                "client_key": "c-1",
                "product_reference": "REF-1",
                "request_date": "2026-03-01",
                "request_date_available": True,
                "landing_status": "Incoming",
                "effective_bags": 1.0,
                "reserved_kg": 10.0,
                "reserved_value_gbp": 700.0,
                "reserved_value_available": True,
            },
            {
                "company_name": "Bravo Coffee",
                "client_id": "c-2",
                "client_key": "c-2",
                "product_reference": "REF-1",
                "request_date": "2026-03-01",
                "request_date_available": True,
                "landing_status": "Incoming",
                "effective_bags": 1.0,
                "reserved_kg": 10.0,
                "reserved_value_gbp": 500.0,
                "reserved_value_available": True,
            },
            {
                "company_name": "Cinder Roastery",
                "client_id": "c-3",
                "client_key": "c-3",
                "product_reference": "REF-1",
                "request_date": "2026-03-01",
                "request_date_available": True,
                "landing_status": "Incoming",
                "effective_bags": 1.0,
                "reserved_kg": 10.0,
                "reserved_value_gbp": 400.0,
                "reserved_value_available": True,
            },
            {
                "company_name": "Drift Coffee",
                "client_id": "c-4",
                "client_key": "c-4",
                "product_reference": "REF-1",
                "request_date": "2026-03-01",
                "request_date_available": True,
                "landing_status": "Incoming",
                "effective_bags": 1.0,
                "reserved_kg": 10.0,
                "reserved_value_gbp": 300.0,
                "reserved_value_available": True,
            },
            {
                "company_name": "Ember Coffee",
                "client_id": "c-5",
                "client_key": "c-5",
                "product_reference": "REF-1",
                "request_date": "2026-03-01",
                "request_date_available": True,
                "landing_status": "Incoming",
                "effective_bags": 1.0,
                "reserved_kg": 10.0,
                "reserved_value_gbp": 100.0,
                "reserved_value_available": True,
            },
            {
                "company_name": "Fable Coffee",
                "client_id": "c-6",
                "client_key": "c-6",
                "product_reference": "REF-1",
                "request_date": "2026-03-01",
                "request_date_available": True,
                "landing_status": "Incoming",
                "effective_bags": 1.0,
                "reserved_kg": 10.0,
                "reserved_value_gbp": 100.0,
                "reserved_value_available": True,
            },
        ],
    }

    html = render_html(dataset)

    assert 'concentration_top_five_share: concentrationTopFiveShare === null ? null : Number(concentrationTopFiveShare.toFixed(4))' in html
    assert 'concentration_top_ten_share: concentrationTopTenShare === null ? null : Number(concentrationTopTenShare.toFixed(4))' in html
    assert 'concentration_rest_share: concentrationRestShare === null ? null : Number(concentrationRestShare.toFixed(4))' in html
    assert 'const topFiveValue = rankedValues.slice(0, 5).reduce((sum, value) => sum + value, 0);' in html
    assert 'const topTenValue = rankedValues.slice(0, 10).reduce((sum, value) => sum + value, 0);' in html
    assert 'const filteredRows = currentClientActivityRows();' in html
    assert 'summary: clientSummary,' not in html
    assert 'details: clientDetails,' not in html
    assert 'topExposure: clientTopExposure,' not in html
    assert 'concentration: clientReferenceConcentration,' not in html
    assert 'Top 10: ' in html
    assert 'Rest: ' in html

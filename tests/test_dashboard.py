from __future__ import annotations

from pathlib import Path
import pandas as pd

from mcop.main import build_released_value_trend, build_reservation_pipeline_by_status
from mcop.report.dashboard import write_dashboard_html


def _sample_payload() -> dict:
    return {
        "status_flag": "WATCH",
        "exposure_flag": "BLOCK",
        "trading_health_score": 5.4,
        "base": {
            "as_of": "2026-03-10",
            "cash_on_hand": 125000.0,
            "liquidity_60": 42000.0,
            "runway_days": 48.0,
        },
        "pinch_14d": {"cash_alert": "AMBER"},
        "pinch_30d": {"cash_alert": "RED", "net_gbp": -6500.0},
        "container_exposure": {
            "incoming_capital_total_gbp": 90000.0,
            "incoming_reserved_kg": 1464.0,
            "incoming_total_kg": 2400.0,
            "incoming_reserved_balance_pct": 0.61,
            "incoming_precommitted_pct": 0.61,
            "incoming_uncommitted_gbp": 35100.0,
            "capital_deployment_ratio": 0.34,
            "dynamic_precommit": {"value_below_target_gbp": 18000.0},
            "incoming_by_landing_date": [
                {
                    "landing_date": "2026-03-18",
                    "reserved_value_gbp": 24000.0,
                    "unreserved_value_gbp": 8000.0,
                    "total_value_gbp": 32000.0,
                    "reserved_kg": 960.0,
                    "unreserved_kg": 320.0,
                    "total_kg": 1280.0,
                },
                {
                    "landing_date": "2026-03-29",
                    "reserved_value_gbp": 30900.0,
                    "unreserved_value_gbp": 27100.0,
                    "total_value_gbp": 58000.0,
                    "reserved_kg": 504.0,
                    "unreserved_kg": 616.0,
                    "total_kg": 1120.0,
                },
            ],
            "breakdown_top_incoming": [
                {"product_reference": "ALPHA-1", "incoming_value_gbp": 20000.0, "precommit_pct_product": 0.5},
                {"product_reference": "BETA-2", "incoming_value_gbp": 17000.0, "precommit_pct_product": 0.8},
            ],
            "top_at_risk_incoming": [
                {"product_reference": "BETA-2", "shortfall_value_gbp": 9000.0, "days_to_landing": 12},
                {"product_reference": "ALPHA-1", "shortfall_value_gbp": 12000.0, "days_to_landing": 12},
                {"product_reference": "GAMMA-3", "shortfall_value_gbp": 7000.0, "days_to_landing": 30},
            ],
        },
        "landed_aging": {
            "flag": "BLOCK",
            "total_unsold_value": 37743.6,
            "buckets": {"0_30": 0.0, "30_60": 5000.0, "60_90": 8000.0, "90_plus": 24743.6},
            "top_cash_traps": [
                {"label": "LOT-7", "unsold_value": 7800.0, "days_since_landing": 183},
                {"label": "LOT-5", "unsold_value": 4200.0, "days_since_landing": 121},
            ],
        },
        "top_payables_60": [
            {"date": "2026-03-20", "amount": 5000.0, "label": "PAY-2"},
            {"date": "2026-03-18", "amount": 3000.0, "label": "PAY-1"},
            {"date": "2026-03-20", "amount": 7000.0, "label": "PAY-3"},
        ],
        "top_receivables_60": [
            {"date": "2026-03-21", "amount": 10000.0, "label": "REC-2"},
            {"date": "2026-03-19", "amount": 8000.0, "label": "REC-1"},
        ],
        "reservation_pipeline_by_status": [
            {"status": "Created", "value_gbp": 12000.0},
            {"status": "Approved", "value_gbp": 27000.0},
            {"status": "Completed", "value_gbp": 8000.0},
        ],
        "released_value_trend": [
            {"date": "2026-02-20", "value_gbp": 3000.0},
            {"date": "2026-02-27", "value_gbp": 5200.0},
            {"date": "2026-03-05", "value_gbp": 6100.0},
        ],
        "summary": [
            "Trading Health (this week): 5.4/10",
            "Action: close GBP 18,000 total pre-sell gap across incoming coffees.",
            "Priority: ALPHA-1 landing in 12 days - GBP 12,000 gap.",
            "7-day target: secure GBP 7,200 additional pre-sell on ALPHA-1.",
            "This week's move: contact 5 target roasters for ALPHA-1.",
            "Summary <needs> escaping & stability.",
        ],
    }


def test_write_dashboard_html_is_deterministic(tmp_path: Path) -> None:
    payload = _sample_payload()
    out = tmp_path / "dashboard.html"

    write_dashboard_html(out, payload)
    first = out.read_text(encoding="utf-8")

    write_dashboard_html(out, payload)
    second = out.read_text(encoding="utf-8")

    assert first == second
    assert "MCOP Dashboard v1" in first
    assert "Generated for as_of 2026-03-10" in first
    assert "Summary &lt;needs&gt; escaping &amp; stability." in first
    assert "Immediate Actions" in first
    assert 'id="theme-toggle"' in first
    assert "Cash on Hand" in first
    assert "Incoming Reserved Balance" in first
    assert "Incoming Exposure" in first
    assert 'data-exposure-toggle="value"' in first
    assert 'data-exposure-toggle="kg"' in first
    assert 'data-exposure-view="value"' in first
    assert 'data-exposure-view="kg"' in first
    assert "Reserved kg" in first
    assert "Unreserved kg" in first
    assert "Reservation Pipeline by Status" in first
    assert "Released Value Trend" in first
    assert "Incoming Pre-sell Gap Queue" in first
    assert "Top Incoming Shortfalls" in first


def test_dashboard_line_chart_labels_use_clamped_edge_anchors(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.html"
    write_dashboard_html(out, _sample_payload())
    html = out.read_text(encoding="utf-8")

    assert "text-anchor='start' fill='var(--muted)' font-size='10'>3k</text>" in html
    assert "text-anchor='middle' fill='var(--muted)' font-size='10'>5k</text>" in html
    assert "text-anchor='end' fill='var(--muted)' font-size='10'>6k</text>" in html


def test_dashboard_orders_rows_stably(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.html"
    write_dashboard_html(out, _sample_payload())
    html = out.read_text(encoding="utf-8")

    alpha_idx = html.index("ALPHA-1")
    beta_idx = html.index("BETA-2")
    gamma_idx = html.index("GAMMA-3")
    assert alpha_idx < beta_idx < gamma_idx

    pay1_idx = html.index("PAY-1")
    pay3_idx = html.index("PAY-3")
    pay2_idx = html.index("PAY-2")
    assert pay1_idx < pay3_idx < pay2_idx

    rec1_idx = html.index("REC-1")
    rec2_idx = html.index("REC-2")
    assert rec1_idx < rec2_idx


def test_reservation_pipeline_uses_latest_effective_row_per_booking() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r1",
                "id_booking": "b1",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-03-01",
                "bags": 10,
                "bags_remaining": 10,
                "bag_size_kg": 24,
                "price_per_kg": 10.0,
            },
            {
                "id_request": "r2",
                "id_booking": "b1",
                "request_type": "reservation",
                "request_status": "approved",
                "approval_date": "2026-03-03",
                "bags": 10,
                "bags_remaining": 6,
                "bag_size_kg": 24,
                "price_per_kg": 10.0,
            },
            {
                "id_request": "r3",
                "id_booking": "b2",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-03-02",
                "bags": 5,
                "bag_size_kg": 24,
                "price_per_kg": 11.0,
            },
        ]
    )

    result = build_reservation_pipeline_by_status(activity)

    assert result == [
        {"status": "Created", "value_gbp": 1320.0},
        {"status": "Approved", "value_gbp": 1440.0},
    ]


def test_released_value_trend_uses_dispatch_then_approval_then_request_date() -> None:
    activity = pd.DataFrame(
        [
            {
                "request_type": "release",
                "dispatch_date": "2026-03-05",
                "bags": 5,
                "bag_size_kg": 24,
                "price_per_kg": 10.0,
            },
            {
                "request_type": "release",
                "approval_date": "2026-03-06",
                "bags": 4,
                "bag_size_kg": 24,
                "price_per_kg": 12.0,
            },
            {
                "request_type": "release",
                "request_date": "2026-03-06",
                "bags": 1,
                "bag_size_kg": 24,
                "price_per_kg": 20.0,
            },
        ]
    )

    result = build_released_value_trend(activity)

    assert result == [
        {"date": "2026-03-05", "value_gbp": 1200.0},
        {"date": "2026-03-06", "value_gbp": 1632.0},
    ]

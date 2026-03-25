from __future__ import annotations

import json
from pathlib import Path

from mcop.main import main
from mcop.report.html import write_weekly_brief


def _base_payload() -> dict:
    return {
        "snapshot_date": "2026-03-14",
        "status_flag": "WATCH",
        "exposure_flag": "BLOCK",
        "summary": ["Liquidity is tightening."],
        "base": {
            "as_of": "2026-03-10",
            "cash_on_hand": 125000.0,
            "liquidity_60": 42000.0,
            "runway_days": 48.0,
        },
        "stress": {
            "as_of": "2026-03-10",
            "liquidity_60": 30000.0,
        },
        "container_exposure": {},
        "top_payables_60": [],
        "top_receivables_60": [],
    }


def test_weekly_brief_visible_date_prefers_snapshot_date(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "As of <strong>2026-03-14</strong>" in html
    assert "As of <strong>2026-03-10</strong>" not in html


def test_weekly_brief_visible_date_falls_back_to_base_as_of(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()
    payload.pop("snapshot_date")

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "As of <strong>2026-03-10</strong>" in html


def test_weekly_brief_xero_tables_hide_internal_source_ids(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()
    payload["xero_import"] = {
        "available": True,
        "snapshot_date": "2026-03-14",
        "organisation_name": "Example Ltd",
        "base_currency": "GBP",
        "fx_rates_gbp": {},
        "detected_non_gbp_currencies": [],
        "converted_cash_on_hand_gbp": None,
        "converted_receivables_total_gbp": None,
        "converted_payables_total_gbp": None,
        "bank_totals_by_currency": [],
        "receivables_totals_by_currency": [],
        "payables_totals_by_currency": [],
        "comparison_lines": [],
        "top_receivables": [
            {
                "source_doc_no": "INV-0300",
                "source_id": "1e74f6f0-078d-4064-8abc-648688bed3f2",
                "counterparty_name": "Sipsisters",
                "due_date": "2026-03-28",
                "currency_code": "GBP",
                "amount_due": 1002.4,
            }
        ],
        "top_payables": [
            {
                "source_doc_no": "BILL-0100",
                "source_id": "6a0daff8-1634-46de-b791-2a67ea41971e",
                "counterparty_name": "Supplier A",
                "due_date": "2026-03-27",
                "currency_code": "GBP",
                "amount_due": 500.0,
            }
        ],
    }

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "INV-0300" in html
    assert "BILL-0100" in html
    assert "1e74f6f0-078d-4064-8abc-648688bed3f2" not in html
    assert "6a0daff8-1634-46de-b791-2a67ea41971e" not in html


def test_weekly_brief_renders_xero_fx_metadata(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()
    payload["xero_import"] = {
        "available": True,
        "snapshot_date": "2026-03-14",
        "organisation_name": "Example Ltd",
        "base_currency": "GBP",
        "fx_rates_gbp": {"USD": 0.79},
        "detected_non_gbp_currencies": ["USD"],
        "converted_cash_on_hand_gbp": 25790.0,
        "converted_receivables_total_gbp": 1748.0,
        "converted_payables_total_gbp": 1211.0,
        "bank_totals_by_currency": [],
        "receivables_totals_by_currency": [],
        "payables_totals_by_currency": [],
        "comparison_lines": [],
        "top_receivables": [],
        "top_payables": [],
    }

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "Detected non-GBP currencies: <strong>USD</strong>" in html
    assert "Manual FX rates used: <strong>USD=0.790000</strong>" in html
    assert "Converted Xero cash used in GBP analysis: <strong>£25,790.00</strong>" in html
    assert "Converted Xero receivables used in GBP analysis: <strong>£1,748.00</strong>" in html
    assert "Converted Xero payables used in GBP analysis: <strong>£1,211.00</strong>" in html


def test_weekly_brief_renders_infinite_runway_and_cash_risk_score(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()
    payload["base"]["runway_days"] = float("inf")
    payload["cash_risk_score"] = 42
    payload["score_band"] = "AMBER"

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "∞ days" in html
    assert ">42<" in html
    assert ">AMBER<" in html


def test_weekly_brief_top_drivers_accepts_mixed_item_types(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()
    payload["score_breakdown"] = {
        "top_drivers": [
            {"component": "stress", "contribution": 12.5},
            "pinch pressure elevated",
            {"component": "runway", "contribution": 8.0},
        ]
    }

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "stress</span> — 12.50" in html
    assert "<li>pinch pressure elevated</li>" in html
    assert "runway</span> — 8.00" in html


def test_weekly_brief_main_table_uses_xero_doc_label_when_product_reference_missing(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()
    payload["top_payables_60"] = [
        {
            "date": "2026-03-28",
            "amount": 1002.4,
            "label": "BILL-0100 (Supplier A)",
            "source_doc_no": "BILL-0100",
            "counterparty_name": "Supplier A",
        }
    ]

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "BILL-0100 (Supplier A)" in html
    assert "BILL-0100</strong> <span class='mono'>(—)</span>" not in html


def test_weekly_brief_main_table_keeps_legacy_product_rendering_unchanged(tmp_path: Path) -> None:
    out = tmp_path / "weekly.html"
    payload = _base_payload()
    payload["top_receivables_60"] = [
        {
            "date": "2026-03-29",
            "amount": 750.0,
            "product_reference": "ALPHA-1",
            "product_id": "p-1",
            "label": "SHOULD-NOT-BE-USED",
            "source_doc_no": "INV-9999",
            "counterparty_name": "Customer A",
        }
    ]

    write_weekly_brief(out, payload)
    html = out.read_text(encoding="utf-8")

    assert "ALPHA-1</strong> <span class='mono'>(p-1)</span>" in html
    assert "SHOULD-NOT-BE-USED" not in html


def test_run_uses_snapshot_date_for_external_artifacts(monkeypatch, tmp_path: Path) -> None:
    from mcop import main as main_mod

    class _Paths:
        def __init__(self, root: Path) -> None:
            self.data_dir = root / "data"
            self.out_dir = root / "out"

    class _Inputs:
        def __init__(self) -> None:
            self.cash_position = object()
            self.costs = object()
            self.activity = object()
            self.products = []

    class _Snapshot:
        def __init__(self, as_of: str, cash_on_hand: float, liquidity_60: float, runway_days: float) -> None:
            self.as_of = as_of
            self.cash_on_hand = cash_on_hand
            self.receivables_60 = 22000.0
            self.payables_60 = 12000.0
            self.liquidity_60 = liquidity_60
            self.runway_days = runway_days

        def to_dict(self) -> dict:
            return {
                "as_of": self.as_of,
                "cash_on_hand": self.cash_on_hand,
                "receivables_30": 10000.0,
                "receivables_60": self.receivables_60,
                "payables_30": 5000.0,
                "payables_60": self.payables_60,
                "liquidity_30": 130000.0,
                "liquidity_60": self.liquidity_60,
                "runway_days": self.runway_days,
            }

    paths = _Paths(tmp_path)
    paths.data_dir.mkdir(parents=True)
    paths.out_dir.mkdir(parents=True)

    written_weekly: list[tuple[Path, dict]] = []
    written_dashboard: list[tuple[Path, dict]] = []

    monkeypatch.setattr(main_mod, "get_paths", lambda: paths)
    monkeypatch.setattr(main_mod, "load_inputs", lambda _data_dir: _Inputs())
    monkeypatch.setattr(main_mod, "build_payables_from_costs", lambda _costs: [])
    monkeypatch.setattr(main_mod, "build_receivables_from_activity", lambda _activity, delay_buffer_days=7: [])
    monkeypatch.setattr(main_mod, "latest_as_of", lambda _cash_position: (main_mod.pd.Timestamp("2026-03-10"), 125000.0))
    monkeypatch.setattr(main_mod, "stress_receivables", lambda receivables, as_of, *_args: receivables)
    monkeypatch.setattr(main_mod, "compute_liquidity_snapshot", lambda *_args: _Snapshot("2026-03-10", 125000.0, 42000.0, 48.0))
    monkeypatch.setattr(main_mod, "governance_flag", lambda *_args: "WATCH")
    monkeypatch.setattr(main_mod, "build_product_reference_map", lambda _products: {})
    monkeypatch.setattr(
        main_mod,
        "compute_container_exposure",
        lambda **_kwargs: {
            "exposure_flag": "BLOCK",
            "capital_deployment_ratio": 0.34,
            "deployment_flag": "WATCH",
            "dynamic_precommit": {
                "value_below_target_gbp": 18000.0,
                "pct_incoming_value_below_target": 0.2,
                "any_near_landing_hard_breach": False,
            },
            "overlap_window_details": {"sku_count": 0, "window_start": ""},
            "top_at_risk_incoming": [],
            "breakdown_top_incoming": [],
        },
    )
    monkeypatch.setattr(main_mod, "plain_english_summary", lambda *_args: ["Liquidity is tightening."])
    monkeypatch.setattr(main_mod, "build_released_value_trend", lambda _activity: [])
    monkeypatch.setattr(main_mod, "top_events_within", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        main_mod,
        "compute_landed_aging",
        lambda *_args: {
            "flag": "OK",
            "total_unsold_value": 0.0,
            "buckets": {"60_90": 0.0, "90_plus": 0.0},
            "top_cash_traps": [],
        },
    )
    monkeypatch.setattr(main_mod, "compute_drift_signals", lambda _out_dir: [])
    monkeypatch.setattr(
        main_mod,
        "compute_pinch_14d",
        lambda *_args, days=14: {
            "as_of": "2026-03-14",
            "window_days": days,
            "expected_in_gbp": 0.0,
            "expected_out_gbp": 0.0,
            "net_gbp": 0.0,
            "biggest_out": None,
            "biggest_in": None,
        },
    )
    monkeypatch.setattr(main_mod, "run_regression_guard", lambda *_args: [])
    monkeypatch.setattr(main_mod, "run_snapshot_check", lambda *_args: [])
    monkeypatch.setattr(main_mod, "compute_cash_risk_score", lambda _engine_input: {"cash_risk_score": 3, "score_band": "WATCH", "score_breakdown": {}})
    monkeypatch.setattr(main_mod, "evaluate_rules", lambda _engine_input: [])
    monkeypatch.setattr(main_mod, "write_dashboard_html", lambda path, payload: written_dashboard.append((Path(path), dict(payload))))
    monkeypatch.setattr(main_mod, "write_weekly_brief", lambda path, payload: written_weekly.append((Path(path), dict(payload))))

    monkeypatch.setattr(
        "sys.argv",
        ["mcop", "run", "--as-of", "2026-03-14"],
    )

    main()

    assert written_weekly
    weekly_path, weekly_payload = written_weekly[0]
    assert weekly_path.name == "WeeklyBrief_2026-03-14.html"
    assert weekly_payload["snapshot_date"] == "2026-03-14"
    assert weekly_payload["base"]["as_of"] == "2026-03-10"
    assert weekly_payload["cash_risk_score"] == 3
    assert weekly_payload["score_band"] == "WATCH"

    decision_pack = json.loads((paths.out_dir / "DecisionPack_2026-03-14.json").read_text(encoding="utf-8"))
    assert decision_pack["snapshot_date"] == "2026-03-14"
    assert decision_pack["as_of"] == "2026-03-10"
    assert decision_pack["cash_risk_score"] == 3
    assert decision_pack["score_band"] == "WATCH"

    assert written_dashboard
    _dashboard_path, dashboard_payload = written_dashboard[0]
    assert dashboard_payload["cash_risk_score"] == 3
    assert dashboard_payload["score_band"] == "WATCH"

    history = json.loads((paths.out_dir / "history.json").read_text(encoding="utf-8"))
    assert history[-1]["snapshot_date"] == "2026-03-14"
    assert history[-1]["as_of"] == "2026-03-10"


def test_run_calls_landed_aging_with_snapshot_date_and_does_not_skip_nameerror(monkeypatch, tmp_path: Path) -> None:
    from mcop import main as main_mod

    class _Paths:
        def __init__(self, root: Path) -> None:
            self.data_dir = root / "data"
            self.out_dir = root / "out"

    class _Inputs:
        def __init__(self) -> None:
            self.cash_position = object()
            self.costs = object()
            self.activity = object()
            self.products = []

    class _Snapshot:
        def __init__(self, as_of: str, cash_on_hand: float, liquidity_60: float, runway_days: float) -> None:
            self.as_of = as_of
            self.cash_on_hand = cash_on_hand
            self.receivables_60 = 22000.0
            self.payables_60 = 12000.0
            self.liquidity_60 = liquidity_60
            self.runway_days = runway_days

        def to_dict(self) -> dict:
            return {
                "as_of": self.as_of,
                "cash_on_hand": self.cash_on_hand,
                "receivables_30": 10000.0,
                "receivables_60": self.receivables_60,
                "payables_30": 5000.0,
                "payables_60": self.payables_60,
                "liquidity_30": 130000.0,
                "liquidity_60": self.liquidity_60,
                "runway_days": self.runway_days,
            }

    paths = _Paths(tmp_path)
    paths.data_dir.mkdir(parents=True)
    paths.out_dir.mkdir(parents=True)

    captured: dict[str, object] = {}
    written_weekly: list[tuple[Path, dict]] = []

    monkeypatch.setattr(main_mod, "get_paths", lambda: paths)
    monkeypatch.setattr(main_mod, "load_inputs", lambda _data_dir: _Inputs())
    monkeypatch.setattr(main_mod, "build_payables_from_costs", lambda _costs: [])
    monkeypatch.setattr(main_mod, "build_receivables_from_activity", lambda _activity, delay_buffer_days=7: [])
    monkeypatch.setattr(main_mod, "latest_as_of", lambda _cash_position: (main_mod.pd.Timestamp("2026-03-10"), 125000.0))
    monkeypatch.setattr(main_mod, "stress_receivables", lambda receivables, as_of, *_args: receivables)
    monkeypatch.setattr(main_mod, "compute_liquidity_snapshot", lambda *_args: _Snapshot("2026-03-10", 125000.0, 42000.0, 48.0))
    monkeypatch.setattr(main_mod, "governance_flag", lambda *_args: "WATCH")
    monkeypatch.setattr(main_mod, "build_product_reference_map", lambda _products: {})
    monkeypatch.setattr(
        main_mod,
        "compute_container_exposure",
        lambda **_kwargs: {
            "exposure_flag": "BLOCK",
            "capital_deployment_ratio": 0.34,
            "deployment_flag": "WATCH",
            "dynamic_precommit": {
                "value_below_target_gbp": 18000.0,
                "pct_incoming_value_below_target": 0.2,
                "any_near_landing_hard_breach": False,
            },
            "overlap_window_details": {"sku_count": 0, "window_start": ""},
            "top_at_risk_incoming": [],
            "breakdown_top_incoming": [],
        },
    )
    monkeypatch.setattr(main_mod, "plain_english_summary", lambda *_args: ["Liquidity is tightening."])
    monkeypatch.setattr(main_mod, "build_released_value_trend", lambda _activity: [])
    monkeypatch.setattr(main_mod, "top_events_within", lambda *_args, **_kwargs: [])

    def _compute_landed_aging(products, as_of_date, stress_liquidity_60d):
        captured["called"] = True
        captured["as_of_date"] = as_of_date
        captured["stress_liquidity_60d"] = stress_liquidity_60d
        captured["products"] = products
        return {
            "flag": "OK",
            "total_unsold_value": 321.0,
            "buckets": {"60_90": 100.0, "90_plus": 25.0},
            "top_cash_traps": [],
        }

    monkeypatch.setattr(main_mod, "compute_landed_aging", _compute_landed_aging)
    monkeypatch.setattr(main_mod, "compute_drift_signals", lambda _out_dir: [])
    monkeypatch.setattr(
        main_mod,
        "compute_pinch_14d",
        lambda *_args, days=14: {
            "as_of": "2026-03-14",
            "window_days": days,
            "expected_in_gbp": 0.0,
            "expected_out_gbp": 0.0,
            "net_gbp": 0.0,
            "biggest_out": None,
            "biggest_in": None,
        },
    )
    monkeypatch.setattr(main_mod, "run_regression_guard", lambda *_args: [])
    monkeypatch.setattr(main_mod, "run_snapshot_check", lambda *_args: [])
    monkeypatch.setattr(main_mod, "compute_cash_risk_score", lambda _engine_input: {"cash_risk_score": 3, "score_band": "WATCH", "score_breakdown": {}})
    monkeypatch.setattr(main_mod, "evaluate_rules", lambda _engine_input: [])
    monkeypatch.setattr(main_mod, "write_dashboard_html", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_mod, "write_weekly_brief", lambda path, payload: written_weekly.append((Path(path), dict(payload))))

    monkeypatch.setattr(
        "sys.argv",
        ["mcop", "run", "--as-of", "2026-03-14"],
    )

    main()

    assert captured["called"] is True
    assert captured["as_of_date"] == main_mod.pd.Timestamp("2026-03-14").date()

    assert written_weekly
    _weekly_path, weekly_payload = written_weekly[0]
    assert "landed_aging" in weekly_payload
    assert any(line == "Landed unsold stock: £321 (OK)." for line in weekly_payload["summary"])
    assert any(line == "Older than 60 days: £125." for line in weekly_payload["summary"])
    assert not any("Landed stock ageing skipped: NameError" in line for line in weekly_payload["summary"])

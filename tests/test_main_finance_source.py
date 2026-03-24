from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from mcop.main import main


@dataclass
class _Paths:
    data_dir: Path
    out_dir: Path
    xero_snapshot_path: Path


class _Inputs:
    def __init__(self, *, cash_position: pd.DataFrame, xero_sidecar=None) -> None:
        self.cash_position = cash_position
        self.costs = object()
        self.activity = object()
        self.products = pd.DataFrame(columns=["product_id", "product_reference"])
        self.xero_sidecar = xero_sidecar


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


def _common_monkeypatches(monkeypatch, tmp_path: Path, load_inputs_impl):
    from mcop import main as main_mod

    data_dir = tmp_path / "data"
    out_dir = tmp_path / "out"
    data_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    xero_snapshot_path = data_dir / "xero_snapshot_v1.json"
    xero_snapshot_path.write_text("{}", encoding="utf-8")

    paths = _Paths(
        data_dir=data_dir,
        out_dir=out_dir,
        xero_snapshot_path=xero_snapshot_path,
    )

    legacy_cash_position = pd.DataFrame([{"date": "2026-03-10", "cash_on_hand": 1500.0}])
    legacy_payables = pd.DataFrame([{"date": "2026-03-20", "amount": 500.0}])
    legacy_receivables = pd.DataFrame([{"date": "2026-03-21", "amount": 800.0}])

    monkeypatch.setattr(main_mod, "get_paths", lambda: paths)
    monkeypatch.setattr(main_mod, "load_inputs", load_inputs_impl)
    monkeypatch.setattr(main_mod, "build_payables_from_costs", lambda _costs: legacy_payables)
    monkeypatch.setattr(
        main_mod,
        "build_receivables_from_activity",
        lambda _activity, delay_buffer_days=7: legacy_receivables,
    )
    monkeypatch.setattr(
        main_mod,
        "latest_as_of",
        lambda cash_position: (main_mod.pd.Timestamp(str(cash_position.iloc[0]["date"])), float(cash_position.iloc[0]["cash_on_hand"])),
    )
    monkeypatch.setattr(main_mod, "stress_receivables", lambda receivables, as_of, *_args: receivables)
    monkeypatch.setattr(
        main_mod,
        "compute_liquidity_snapshot",
        lambda cash_position, _payables, _receivables: _Snapshot(
            str(cash_position.iloc[0]["date"]),
            float(cash_position.iloc[0]["cash_on_hand"]),
            float(cash_position.iloc[0]["cash_on_hand"]) + 1000.0,
            48.0,
        ),
    )
    monkeypatch.setattr(main_mod, "governance_flag", lambda *_args: "WATCH")
    monkeypatch.setattr(main_mod, "build_product_reference_map", lambda _products: {})
    monkeypatch.setattr(
        main_mod,
        "compute_container_exposure",
        lambda **_kwargs: {
            "exposure_flag": "OK",
            "capital_deployment_ratio": 0.1,
            "deployment_flag": "OK",
            "dynamic_precommit": {
                "value_below_target_gbp": 0.0,
                "pct_incoming_value_below_target": 0.0,
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
    monkeypatch.setattr(
        main_mod,
        "compute_cash_risk_score",
        lambda _engine_input: {"cash_risk_score": 3, "score_band": "WATCH", "score_breakdown": {}},
    )
    monkeypatch.setattr(main_mod, "evaluate_rules", lambda _engine_input: [])
    monkeypatch.setattr(main_mod, "write_dashboard_html", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_mod, "write_weekly_brief", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_mod, "build_xero_reporting_payload", lambda *_args, **_kwargs: {"available": True})
    monkeypatch.setattr("sys.argv", ["mcop", "run", "--as-of", "2026-03-14"])

    return main_mod, paths, legacy_cash_position


def test_main_uses_xero_finance_inputs_when_snapshot_is_usable(monkeypatch, tmp_path: Path) -> None:
    xero_cash_position = pd.DataFrame([{"date": "2026-03-17", "cash_on_hand": 25000.0}])
    xero_payables = pd.DataFrame([{"date": "2026-03-25", "amount": 500.0}])
    xero_receivables = pd.DataFrame([{"date": "2026-03-31", "amount": 800.0}])
    xero_sidecar = type(
        "XeroSidecarStub",
        (),
        {
            "currency_warning": None,
            "finance_cash_position_snapshot": xero_cash_position,
            "finance_payable_events": xero_payables,
            "finance_receivable_events": xero_receivables,
            "organisation": {"snapshot_date": "2026-03-17", "organisation_name": "Example Ltd"},
        },
    )()

    def _load_inputs(_data_dir, xero_path=None):
        return _Inputs(
            cash_position=pd.DataFrame([{"date": "2026-03-10", "cash_on_hand": 1500.0}]),
            xero_sidecar=xero_sidecar,
        )

    _, paths, _legacy_cash_position = _common_monkeypatches(monkeypatch, tmp_path, _load_inputs)

    main()

    payload = json.loads((paths.out_dir / "liquidity_report.json").read_text(encoding="utf-8"))
    assert payload["finance_source"]["selected"] == "xero"
    assert payload["finance_source"]["reason"] == "valid_xero_snapshot"
    assert payload["base"]["cash_on_hand"] == 25000.0
    assert any("Finance source: Xero snapshot (2026-03-17)." in line for line in payload["summary"])


def test_main_falls_back_to_legacy_when_xero_snapshot_has_mixed_currency(monkeypatch, tmp_path: Path) -> None:
    xero_sidecar = type(
        "XeroSidecarStub",
        (),
        {
            "currency_warning": "Mixed/non-GBP Xero values detected.",
            "finance_cash_position_snapshot": pd.DataFrame(columns=["date", "cash_on_hand"]),
            "finance_payable_events": pd.DataFrame([{"date": "2026-03-25", "amount": 500.0}]),
            "finance_receivable_events": pd.DataFrame([{"date": "2026-03-31", "amount": 800.0}]),
            "organisation": {"snapshot_date": "2026-03-17", "organisation_name": "Example Ltd"},
        },
    )()

    def _load_inputs(_data_dir, xero_path=None):
        return _Inputs(
            cash_position=pd.DataFrame([{"date": "2026-03-10", "cash_on_hand": 1500.0}]),
            xero_sidecar=xero_sidecar,
        )

    _, paths, _legacy_cash_position = _common_monkeypatches(monkeypatch, tmp_path, _load_inputs)

    main()

    payload = json.loads((paths.out_dir / "liquidity_report.json").read_text(encoding="utf-8"))
    assert payload["finance_source"]["selected"] == "legacy"
    assert payload["finance_source"]["reason"] == "xero_snapshot_not_usable_for_gbp_liquidity"
    assert payload["base"]["cash_on_hand"] == 1500.0
    assert any(
        "Xero snapshot includes non-GBP bank balances; those balances are excluded from the current GBP-only analysis."
        in line
        for line in payload["summary"]
    )


def test_main_falls_back_to_legacy_when_xero_snapshot_is_invalid(monkeypatch, tmp_path: Path) -> None:
    load_calls: list[Path | None] = []

    def _load_inputs(data_dir, xero_path=None):
        load_calls.append(xero_path)
        if xero_path is not None:
            raise ValueError("Unsupported schema_version: wrong_version")
        return _Inputs(
            cash_position=pd.DataFrame([{"date": "2026-03-10", "cash_on_hand": 1500.0}]),
            xero_sidecar=None,
        )

    _, paths, _legacy_cash_position = _common_monkeypatches(monkeypatch, tmp_path, _load_inputs)

    main()

    payload = json.loads((paths.out_dir / "liquidity_report.json").read_text(encoding="utf-8"))
    assert load_calls == [paths.xero_snapshot_path, None]
    assert payload["finance_source"]["selected"] == "legacy"
    assert payload["finance_source"]["reason"] == "xero_snapshot_invalid: Unsupported schema_version: wrong_version"
    assert payload["base"]["cash_on_hand"] == 1500.0
    assert any("Finance source: legacy finance inputs (Xero snapshot invalid)." in line for line in payload["summary"])

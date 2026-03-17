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
            self.products = object()

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

    decision_pack = json.loads((paths.out_dir / "DecisionPack_2026-03-14.json").read_text(encoding="utf-8"))
    assert decision_pack["snapshot_date"] == "2026-03-14"
    assert decision_pack["as_of"] == "2026-03-10"

    history = json.loads((paths.out_dir / "history.json").read_text(encoding="utf-8"))
    assert history[-1]["snapshot_date"] == "2026-03-14"
    assert history[-1]["as_of"] == "2026-03-10"

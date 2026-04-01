from __future__ import annotations

import base64
from pathlib import Path

from app.service.config import get_service_paths
from app.service.dataset_loader import save_uploaded_dataset
from app.service.dataset_validator import persist_dataset_status


def _encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def test_dataset_validator_reports_missing_required_uploads(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    paths = get_service_paths()
    payload = persist_dataset_status()

    assert payload["build_ready"] is False
    activity = next(row for row in payload["datasets"] if row["dataset_type"] == "activity")
    assert activity["uploaded"] is False
    assert "Dataset not uploaded." in activity["errors"]
    assert activity["blocks_build"] is True
    cash_position = next(row for row in payload["datasets"] if row["dataset_type"] == "cash_position")
    assert cash_position["uploaded"] is False
    assert cash_position["blocks_build"] is False
    assert cash_position["errors"] == []
    assert paths.validation_status_path.exists()


def test_dataset_validator_accepts_products_aliases_using_normalized_contract(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "products",
        "products.csv",
        _encode(
            "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date\n"
            "p1,REF-1,30,4,2,10.0,landed,2026-03-20\n"
        ),
    )

    payload = persist_dataset_status()
    products = next(row for row in payload["datasets"] if row["dataset_type"] == "products")

    assert products["is_valid"] is True
    assert products["blocks_build"] is False
    assert products["raw_columns"] == [
        "bag_size_kg",
        "bags",
        "bags_available",
        "landing_date",
        "landing_status",
        "price_per_kg",
        "product_id",
        "product_reference",
    ]
    assert products["recognized_columns"] == [
        "bag_size_kg",
        "bags",
        "bags_available",
        "bags_remaining",
        "landing_date",
        "landing_status",
        "price_per_kg",
        "product_id",
        "product_reference",
    ]


def test_dataset_validator_accepts_product_costs_aliases_without_blocking_build(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "product_costs_protected",
        "product_costs_protected.csv",
        _encode(
            "product_id,bag_size_kg,bags,cost_of_green_coffee_gbp_per_kg,cost_farm_to_port_gbp_per_kg,freight_cost_gbp_per_kg,cost_uk_port_to_warehouse_gbp_per_kg,initial_payment_pct,remaining_payment_pct,initial_payment_date,remaining_payment_date,harvest_date,landing_date\n"
            "p1,30,4,5.0,1.0,0.5,0.25,20,80,2026-01-01,2026-02-01,2025-12-01,2026-03-20\n"
        ),
    )

    payload = persist_dataset_status()
    costs = next(row for row in payload["datasets"] if row["dataset_type"] == "product_costs_protected")

    assert costs["is_valid"] is True
    assert costs["blocking_for_build"] is False
    assert costs["blocks_build"] is False
    assert costs["recognized_columns"] == [
        "bag_size",
        "bag_size_kg",
        "bags",
        "cost_farm_to_port_gbp_kg",
        "cost_of_green_coffee_gbp_kg",
        "cost_uk_port_to_warehouse_gbp_kg",
        "freight_cost_gbp_kg",
        "harvest_date",
        "initial_payment_date",
        "initial_payment_pct",
        "landing_date",
        "product_id",
        "remaining_payment_date",
        "remaining_payment_pct",
    ]


def test_dataset_validator_accepts_cash_position_xero_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "cash_position",
        "cash_position.json",
        _encode(
            """{"schema_version":"xero_snapshot_v1","snapshot_date":"2026-03-17","source_system":"xero","organisation":{"tenant_id":"tenant-1","organisation_name":"Example Ltd","base_currency":"GBP"},"receivables":[],"payables":[],"bank_balances":[{"account_id":"bank-1","account_code":"090","account_name":"Main Bank","account_type":"BANK","currency_code":"GBP","balance":25000.0}]}"""
        ),
    )

    payload = persist_dataset_status()
    cash_position = next(row for row in payload["datasets"] if row["dataset_type"] == "cash_position")

    assert cash_position["is_valid"] is True
    assert cash_position["blocking_for_build"] is False
    assert cash_position["raw_columns"] == [
        "bank_balances",
        "organisation",
        "payables",
        "receivables",
        "schema_version",
        "snapshot_date",
        "source_system",
    ]
    assert cash_position["recognized_columns"] == [
        "cash_on_hand",
        "currency_code",
        "date",
        "source_system",
    ]

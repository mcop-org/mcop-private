from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook

from mcop.ingest.loaders import load_inputs
from mcop.exposure.container import compute_container_exposure
from mcop.layer2_aging import compute_landed_aging
from mcop.liquidity.engine import latest_as_of
from mcop.main import build_released_value_trend


def test_load_inputs_falls_back_to_cp1252_for_products_csv_only(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_bytes(
        (
            "product_id,product_reference,cup_profile\n"
            '1,product_1,"Red fruits, boozy, piña colada"\n'
        ).encode("cp1252")
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "product_id,cost_per_kg\n1,10.0\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "cash_on_hand\n1000.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "id_request,product_id\n1,1\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert inputs.products.loc[0, "cup_profile"] == "Red fruits, boozy, piña colada"


def test_load_inputs_prefers_xlsx_when_xlsx_and_csv_both_exist(tmp_path: Path) -> None:
    pd.DataFrame(
        [
            {
                "product_id": "xlsx-1",
                "product_reference": "product_xlsx",
                "bag_size_kg": 24,
                "bags": 10,
                "bags_available": 6,
                "price_per_kg": 12.5,
                "landing_status": "landed",
                "landing_date": "15/01/2025",
                "status": "available",
            }
        ]
    ).to_excel(tmp_path / "products.xlsx", index=False)
    (tmp_path / "products.csv").write_text(
        "\n".join(
            [
                "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date,status",
                "csv-1,product_csv,24,10,6,12.5,landed,2025-01-14,available",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "product_id\nxlsx-1\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2025-01-20,1000.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "product_id\nxlsx-1\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert inputs.products.loc[0, "product_id"] == "xlsx-1"
    assert inputs.products.loc[0, "landing_date"] == "2025-01-15"


def test_load_inputs_aliases_products_bags_available_to_bags_remaining(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "\n".join(
            [
                "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date,status",
                "p1,product_1,24,10,4,12.5,landed,2025-01-15,available",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "\n".join(
            [
                "product_id,bag_size_kg,bags,cost_of_green_coffee_gbp_kg,cost_farm_to_port_gbp_kg,freight_cost_gbp_kg,cost_uk_port_to_warehouse_gbp_kg,initial_payment_pct,initial_payment_date,remaining_payment_pct,remaining_payment_date,harvest_date,landing_date",
                "p1,24,10,5.0,1.0,0.5,0.25,20,2024-12-01,80,2025-02-01,2024-10-01,2025-01-15",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2025-01-20,1000.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "product_id,request_type,request_status,bags,bags_remaining,bag_size_kg,price_per_kg,reservation_days,payment_days,landing_date\np1,Reservation,Created,2,2,24,12.5,30,14,2025-01-15\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert inputs.products.loc[0, "bags_available"] == 4
    assert inputs.products.loc[0, "bags_remaining"] == 4

    as_of, cash_on_hand = latest_as_of(inputs.cash_position)
    exposure = compute_container_exposure(
        products=inputs.products,
        costs=inputs.costs,
        activity=inputs.activity,
        as_of=as_of,
        cash_on_hand=cash_on_hand,
        liquidity_60=1000.0,
    )
    landed_aging = compute_landed_aging(
        inputs.products.to_dict(orient="records"),
        as_of.date(),
        1000.0,
    )

    assert exposure["landed_capital_unsold_gbp"] > 0
    assert landed_aging["total_unsold_value"] > 0


def test_load_inputs_normalises_product_id_to_string_for_runtime_merges(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "\n".join(
            [
                "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date,status",
                "101,product_101,24,10,4,12.5,landed,2025-01-15,available",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "\n".join(
            [
                "product_id,bag_size_kg,bags,cost_of_green_coffee_gbp_kg,cost_farm_to_port_gbp_kg,freight_cost_gbp_kg,cost_uk_port_to_warehouse_gbp_kg,initial_payment_pct,initial_payment_date,remaining_payment_pct,remaining_payment_date,harvest_date,landing_date",
                "101,24,10,5.0,1.0,0.5,0.25,20,2024-12-01,80,2025-02-01,2024-10-01,2025-01-15",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2025-01-20,1000.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "product_id,request_type,request_status,bags,bags_remaining,bag_size_kg,price_per_kg,reservation_days,payment_days,landing_date\n101,Reservation,Created,2,2,24,12.5,30,14,2025-01-15\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert inputs.products.loc[0, "product_id"] == "101"
    assert inputs.costs.loc[0, "product_id"] == "101"
    assert inputs.activity.loc[0, "product_id"] == "101"

    as_of, cash_on_hand = latest_as_of(inputs.cash_position)
    exposure = compute_container_exposure(
        products=inputs.products,
        costs=inputs.costs,
        activity=inputs.activity,
        as_of=as_of,
        cash_on_hand=cash_on_hand,
        liquidity_60=1000.0,
    )

    assert exposure["landed_capital_unsold_gbp"] > 0


def test_latest_as_of_preserves_iso_dates(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "product_id,product_reference\n1,product_1\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "product_id\n1\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2026-01-05,1000.0\n2026-01-12,1500.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "product_id\n1\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)
    as_of, cash_on_hand = latest_as_of(inputs.cash_position)

    assert as_of.date().isoformat() == "2026-01-12"
    assert cash_on_hand == 1500.0


def test_load_inputs_normalises_known_date_columns_to_iso(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "\n".join(
            [
                "product_id,product_reference,landing_date",
                "p1,product_1,15/01/2025",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "\n".join(
            [
                "product_id,harvest_date,landing_date,initial_payment_date,remaining_payment_date",
                "p1,01/10/2024,15/01/2025,2024-12-01,01/02/2025",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n12/01/2026,1500.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "\n".join(
            [
                "product_id,request_date,approval_date,amendment_date,dispatch_date,landing_date",
                "p1,01/03/2026,2026-03-03,04/03/2026,2026-03-05,15/01/2025",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert inputs.products.loc[0, "landing_date"] == "2025-01-15"
    assert inputs.costs.loc[0, "harvest_date"] == "2024-10-01"
    assert inputs.costs.loc[0, "landing_date"] == "2025-01-15"
    assert inputs.costs.loc[0, "initial_payment_date"] == "2024-12-01"
    assert inputs.costs.loc[0, "remaining_payment_date"] == "2025-02-01"
    assert inputs.cash_position.loc[0, "date"] == "2026-01-12"
    assert inputs.activity.loc[0, "request_date"] == "2026-03-01"
    assert inputs.activity.loc[0, "approval_date"] == "2026-03-03"
    assert inputs.activity.loc[0, "amendment_date"] == "2026-03-04"
    assert inputs.activity.loc[0, "dispatch_date"] == "2026-03-05"
    assert inputs.activity.loc[0, "landing_date"] == "2025-01-15"


def test_load_inputs_normalises_excel_serial_dates_from_xlsx(tmp_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "product_id",
            "harvest_date",
            "landing_date",
            "initial_payment_date",
            "remaining_payment_date",
        ]
    )
    sheet.append(["p1", 45566, 45672, 45627, 45689])
    workbook.save(tmp_path / "product_costs_protected.xlsx")

    (tmp_path / "products.csv").write_text(
        "product_id,product_reference\np1,product_1\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2026-01-12,1500.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "product_id\np1\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert inputs.costs.loc[0, "harvest_date"] == "2024-10-01"
    assert inputs.costs.loc[0, "landing_date"] == "2025-01-15"
    assert inputs.costs.loc[0, "initial_payment_date"] == "2024-12-01"
    assert inputs.costs.loc[0, "remaining_payment_date"] == "2025-02-01"


def test_load_inputs_treats_pending_as_empty_for_expected_date_columns(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "product_id,product_reference,landing_date\np1,product_1,Pending\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "product_id,initial_payment_date,remaining_payment_date\np1,Pending,Pending\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2026-01-12,1500.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "\n".join(
            [
                "product_id,request_date,approval_date,amendment_date,dispatch_date,landing_date",
                "p1,2026-03-01,Pending,Pending,Pending,Pending",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert pd.isna(inputs.products.loc[0, "landing_date"])
    assert pd.isna(inputs.costs.loc[0, "initial_payment_date"])
    assert pd.isna(inputs.costs.loc[0, "remaining_payment_date"])
    assert inputs.activity.loc[0, "request_date"] == "2026-03-01"
    assert pd.isna(inputs.activity.loc[0, "approval_date"])
    assert pd.isna(inputs.activity.loc[0, "amendment_date"])
    assert pd.isna(inputs.activity.loc[0, "dispatch_date"])
    assert pd.isna(inputs.activity.loc[0, "landing_date"])


def test_load_inputs_rejects_unknown_date_formats_in_expected_columns(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "product_id,product_reference,landing_date\np1,product_1,2025/01/15\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "product_id\np1\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2025-01-20,1000.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "product_id\np1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported date format"):
        load_inputs(tmp_path)


def test_build_released_value_trend_uses_normalised_ingest_dates(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "product_id,product_reference\np1,product_1\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "product_id\np1\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2026-01-12,1000.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "\n".join(
            [
                "product_id,request_type,bags,bag_size_kg,price_per_kg,request_date,approval_date,dispatch_date",
                "p1,release,2,24,12.5,01/03/2026,03/03/2026,05/03/2026",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)

    assert build_released_value_trend(inputs.activity) == [
        {"date": "2026-03-05", "value_gbp": 600.0}
    ]


def test_compute_container_exposure_uses_reservation_balance_for_incoming_coverage(tmp_path: Path) -> None:
    (tmp_path / "products.csv").write_text(
        "\n".join(
            [
                "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date,status",
                "p1,product_1,24,10,6,12.5,incoming,2026-03-31,incoming",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "product_costs_protected.csv").write_text(
        "\n".join(
            [
                "product_id,bag_size_kg,bags,cost_of_green_coffee_gbp_kg,cost_farm_to_port_gbp_kg,freight_cost_gbp_kg,cost_uk_port_to_warehouse_gbp_kg,initial_payment_pct,initial_payment_date,remaining_payment_pct,remaining_payment_date,harvest_date,landing_date",
                "p1,24,10,5.0,1.0,0.5,0.25,20,2026-01-01,80,2026-04-01,2025-10-01,2026-03-31",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "cash_position.csv").write_text(
        "date,cash_on_hand\n2026-01-12,1000.0\n",
        encoding="utf-8",
    )
    (tmp_path / "activity.csv").write_text(
        "\n".join(
            [
                "product_id,request_type,request_status,bags,bags_remaining,bag_size_kg,landing_date",
                "p1,Reservation,Created,4,4,24,2026-03-31",
                "p1,Samples,Approved,3,3,24,2026-03-31",
                "p1,Reservation,Rejected,2,2,24,2026-03-31",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    inputs = load_inputs(tmp_path)
    as_of, cash_on_hand = latest_as_of(inputs.cash_position)
    exposure = compute_container_exposure(
        products=inputs.products,
        costs=inputs.costs,
        activity=inputs.activity,
        as_of=as_of,
        cash_on_hand=cash_on_hand,
        liquidity_60=1000.0,
    )

    assert exposure["incoming_total_kg"] == 240.0
    assert exposure["incoming_reserved_kg"] == 96.0
    assert exposure["incoming_reserved_balance_pct"] == 0.4
    assert exposure["incoming_precommitted_pct"] == 0.4
    assert exposure["incoming_by_landing_date"] == [
        {
            "landing_date": "2026-03-31",
            "reserved_value_gbp": 648.0,
            "unreserved_value_gbp": 972.0,
            "total_value_gbp": 1620.0,
            "reserved_kg": 96.0,
            "unreserved_kg": 144.0,
            "total_kg": 240.0,
        }
    ]

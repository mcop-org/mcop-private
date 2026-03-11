from pathlib import Path

from mcop.ingest.loaders import load_inputs
from mcop.exposure.container import compute_container_exposure
from mcop.layer2_aging import compute_landed_aging
from mcop.liquidity.engine import latest_as_of


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

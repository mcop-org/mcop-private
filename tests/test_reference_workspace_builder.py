from __future__ import annotations

import pandas as pd

from mcop.reference_workspace.builder import RESERVATION_NOTE, build_reference_workspace_dataset


def test_builder_restores_phase1_reservation_contract_and_keeps_completed_visible() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-03-01",
                "approval_date": "",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "contact_first_name": "Ava",
                "contact_last_name": "Stone",
                "product_id": "p-1",
                "product_reference": "REF-1",
                "bags": 4,
                "bags_remaining": 4,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
            },
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-01",
                "approval_date": "2026-03-03",
                "amendment_date": "2026-03-05",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "contact_first_name": "Ava",
                "contact_last_name": "Stone",
                "product_id": "p-1",
                "product_reference": "REF-1",
                "bags": 4,
                "bags_remaining": 3,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
            },
            {
                "id_request": "ignore-rejected",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "rejected",
                "request_date": "2026-03-02",
                "approval_date": "",
                "amendment_date": "",
                "client_id": "c-x",
                "company_name": "Should Not Render",
                "contact_first_name": "",
                "contact_last_name": "",
                "product_id": "p-1",
                "product_reference": "REF-1",
                "bags": 2,
                "bags_remaining": 2,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
            },
            {
                "id_request": "original-row",
                "id_booking": "booking-2",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-03-04",
                "approval_date": "",
                "amendment_date": "",
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "contact_first_name": "Ben",
                "contact_last_name": "Hart",
                "product_id": "p-2",
                "product_reference": "REF-1",
                "bags": 2,
                "bags_remaining": 2,
                "bag_size_kg": 20,
                "price_per_kg": 12.5,
                "landing_status": "landed",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
            },
            {
                "id_request": "replacement-row",
                "id_booking": "booking-2",
                "request_type": "reservation",
                "request_status": "completed",
                "request_date": "2026-03-04",
                "approval_date": "2026-03-05",
                "amendment_date": "2026-03-07",
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "contact_first_name": "Ben",
                "contact_last_name": "Hart",
                "product_id": "p-2",
                "product_reference": "REF-1",
                "bags": 2,
                "bags_remaining": 1,
                "bag_size_kg": 20,
                "price_per_kg": 12.5,
                "landing_status": "landed",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
            },
        ]
    )
    products = pd.DataFrame(
        [
            {
                "product_id": "p-1",
                "product_reference": "REF-1",
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
                "bags": 4,
                "bag_size_kg": 30,
                "bags_available": 2,
            },
            {
                "product_id": "p-2",
                "product_reference": "REF-1",
                "landing_status": "landed",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
                "bags": 2,
                "bag_size_kg": 20,
                "bags_available": 1,
            },
            {
                "product_id": "p-3",
                "product_reference": "REF-2",
                "landing_status": "incoming",
                "landing_date": "2026-03-25",
                "warehouse": "Antwerp",
                "bags": 5,
                "bag_size_kg": "",
                "bags_available": 5,
            },
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert dataset["snapshot_date"] == "2026-03-07"
    assert dataset["default_reference"] == "REF-1"
    assert dataset["notes"] == [RESERVATION_NOTE]
    assert dataset["reference_options"] == [
        {"product_reference": "REF-1", "has_reservations": True, "landing_status": "Mixed"},
        {"product_reference": "REF-2", "has_reservations": False, "landing_status": "Incoming"},
    ]
    assert dataset["reference_summary"] == [
        {
            "product_reference": "REF-1",
            "landing_status": "Mixed",
            "is_landed": False,
            "reservation_row_count": 2,
            "client_count": 2,
            "reserved_bags": 4.0,
            "bags_available": 3.0,
            "reserved_pct": 0.5714,
            "reserved_kg": 110.0,
            "reserved_value_gbp": 1150.0,
        },
        {
            "product_reference": "REF-2",
            "landing_status": "Incoming",
            "is_landed": False,
            "reservation_row_count": 0,
            "client_count": 0,
            "reserved_bags": 0.0,
            "bags_available": 5.0,
            "reserved_pct": 0.0,
            "reserved_kg": 0.0,
            "reserved_value_gbp": 0.0,
        }
    ]
    assert dataset["reservation_details"] == [
        {
            "product_reference": "REF-1",
            "reservation_key": "r-1",
            "id_request": "r-1",
            "client_id": "c-1",
            "company_name": "Alpha Roasters",
            "contact_first_name": "Ava",
            "contact_last_name": "Stone",
            "request_status": "Approved",
            "request_date": "2026-03-01",
            "approval_date": "2026-03-03",
            "amendment_date": "2026-03-05",
            "landing_status": "Incoming",
            "landing_date": "2026-03-20",
            "warehouse": "London",
            "bags": 4.0,
            "bags_remaining": 3.0,
            "effective_bags": 3.0,
            "bag_size_kg": 30.0,
            "reserved_kg": 90.0,
            "price_per_kg": 10.0,
            "reserved_value_gbp": 900.0,
        },
        {
            "product_reference": "REF-1",
            "reservation_key": "booking-2",
            "id_request": "replacement-row",
            "client_id": "c-2",
            "company_name": "Bravo Coffee",
            "contact_first_name": "Ben",
            "contact_last_name": "Hart",
            "request_status": "Completed",
            "request_date": "2026-03-04",
            "approval_date": "2026-03-05",
            "amendment_date": "2026-03-07",
            "landing_status": "Landed",
            "landing_date": "2026-03-18",
            "warehouse": "Bristol",
            "bags": 2.0,
            "bags_remaining": 1.0,
            "effective_bags": 1.0,
            "bag_size_kg": 20.0,
            "reserved_kg": 20.0,
            "price_per_kg": 12.5,
            "reserved_value_gbp": 250.0,
        },
    ]
    assert dataset["product_reference_summary"] == [
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
            "incoming_bags": 5.0,
            "incoming_bags_available": True,
            "incoming_kg": 0.0,
            "incoming_kg_available": False,
            "landed_bags": 0.0,
            "landed_bags_available": True,
            "landed_kg": 0.0,
            "landed_kg_available": True,
            "landed_available_bags": 0.0,
            "landed_available_bags_available": True,
            "landed_available_kg": 0.0,
            "landed_available_kg_available": True,
            "stock_health": "Mostly Incoming",
        },
    ]
    assert dataset["product_landing_profile"] == [
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
        {
            "product_reference": "REF-2",
            "product_id": "p-3",
            "landing_status": "Incoming",
            "landing_date": "2026-03-25",
            "warehouse": "Antwerp",
            "bags": 5.0,
            "bag_size_kg": None,
            "total_kg": None,
            "bags_available": 5.0,
            "available_kg": None,
        },
    ]
    assert "reference_profiles" not in dataset
    assert "released_bags" not in dataset["reservation_details"][0]
    assert "open_value_gbp" not in dataset["reservation_details"][0]
    assert "released_bags" not in dataset["product_reference_summary"][0]
    assert "open_bags" not in dataset["product_reference_summary"][0]
    assert "sell_through_pct" not in dataset["product_reference_summary"][0]
    assert "product_linked_clients" not in dataset
    assert dataset["reference_summary"][0]["bags_available"] == 3.0
    assert dataset["reference_summary"][0]["reserved_pct"] == 0.5714


def test_builder_product_reference_intelligence_uses_stock_only_unavailable_fallbacks() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-10",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-03-01",
                "approval_date": "",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "product_id": "p-10",
                "product_reference": "REF-X",
            },
            {
                "id_request": "r-11",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-01",
                "approval_date": "2026-03-02",
                "amendment_date": "2026-03-03",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "product_id": "p-10",
                "product_reference": "REF-X",
            },
            {
                "id_request": "r-12",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "completed",
                "request_date": "2026-03-04",
                "approval_date": "2026-03-05",
                "amendment_date": "",
                "client_id": "",
                "company_name": "Bravo Coffee",
                "product_id": "p-11",
                "product_reference": "REF-X",
            },
        ]
    )
    products = pd.DataFrame(
        [
            {
                "product_id": "p-10",
                "product_reference": "REF-X",
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
                "bags": 5,
                "bag_size_kg": 30,
            },
            {
                "product_id": "p-11",
                "product_reference": "REF-X",
                "landing_status": "landed",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
                "bags": 2,
                "bag_size_kg": "",
            },
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert dataset["product_reference_summary"] == [
        {
            "product_reference": "REF-X",
            "incoming_bags": 5.0,
            "incoming_bags_available": True,
            "incoming_kg": 150.0,
            "incoming_kg_available": True,
            "landed_bags": 2.0,
            "landed_bags_available": True,
            "landed_kg": 0.0,
            "landed_kg_available": False,
            "landed_available_bags": 0.0,
            "landed_available_bags_available": False,
            "landed_available_kg": 0.0,
            "landed_available_kg_available": False,
            "stock_health": "Data Incomplete",
        }
    ]
    assert dataset["product_landing_profile"] == [
        {
            "product_reference": "REF-X",
            "product_id": "p-11",
            "landing_status": "Landed",
            "landing_date": "2026-03-18",
            "warehouse": "Bristol",
            "bags": 2.0,
            "bag_size_kg": None,
            "total_kg": None,
            "bags_available": None,
            "available_kg": None,
        },
        {
            "product_reference": "REF-X",
            "product_id": "p-10",
            "landing_status": "Incoming",
            "landing_date": "2026-03-20",
            "warehouse": "London",
            "bags": 5.0,
            "bag_size_kg": 30.0,
            "total_kg": 150.0,
            "bags_available": None,
            "available_kg": None,
        },
    ]
    assert "product_linked_clients" not in dataset


def test_builder_product_reference_intelligence_classifies_balanced_and_landed_build_up() -> None:
    activity = pd.DataFrame()
    products = pd.DataFrame(
        [
            {
                "product_id": "p-balanced-incoming",
                "product_reference": "REF-BAL",
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
                "bags": 2,
                "bag_size_kg": 30,
                "bags_available": 2,
            },
            {
                "product_id": "p-balanced-landed",
                "product_reference": "REF-BAL",
                "landing_status": "landed",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
                "bags": 4,
                "bag_size_kg": 20,
                "bags_available": 1,
            },
            {
                "product_id": "p-build-up-incoming",
                "product_reference": "REF-BUILD",
                "landing_status": "incoming",
                "landing_date": "2026-03-22",
                "warehouse": "Antwerp",
                "bags": 1,
                "bag_size_kg": 30,
                "bags_available": 1,
            },
            {
                "product_id": "p-build-up-landed",
                "product_reference": "REF-BUILD",
                "landing_status": "landed",
                "landing_date": "2026-03-17",
                "warehouse": "Bristol",
                "bags": 3,
                "bag_size_kg": 20,
                "bags_available": 2,
            },
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert dataset["product_reference_summary"] == [
        {
            "product_reference": "REF-BAL",
            "incoming_bags": 2.0,
            "incoming_bags_available": True,
            "incoming_kg": 60.0,
            "incoming_kg_available": True,
            "landed_bags": 4.0,
            "landed_bags_available": True,
            "landed_kg": 80.0,
            "landed_kg_available": True,
            "landed_available_bags": 1.0,
            "landed_available_bags_available": True,
            "landed_available_kg": 20.0,
            "landed_available_kg_available": True,
            "stock_health": "Balanced",
        },
        {
            "product_reference": "REF-BUILD",
            "incoming_bags": 1.0,
            "incoming_bags_available": True,
            "incoming_kg": 30.0,
            "incoming_kg_available": True,
            "landed_bags": 3.0,
            "landed_bags_available": True,
            "landed_kg": 60.0,
            "landed_kg_available": True,
            "landed_available_bags": 2.0,
            "landed_available_bags_available": True,
            "landed_available_kg": 40.0,
            "landed_available_kg_available": True,
            "stock_health": "Landed Build-Up",
        },
    ]

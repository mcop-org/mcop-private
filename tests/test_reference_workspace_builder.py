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
    assert dataset["default_landed_reference"] == "REF-1"
    assert dataset["notes"] == [RESERVATION_NOTE]
    assert dataset["reference_options"] == [
        {"product_reference": "REF-1", "has_reservations": True, "landing_status": "Mixed"},
        {"product_reference": "REF-2", "has_reservations": False, "landing_status": "Incoming"},
    ]
    assert dataset["landed_reference_options"] == [
        {"product_reference": "REF-1"},
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


def test_builder_landed_stock_intelligence_builds_aging_exposure_and_incomplete_fallbacks() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-01",
                "approval_date": "2026-03-03",
                "amendment_date": "2026-03-07",
                "product_reference": "REF-1",
            }
        ]
    )
    products = pd.DataFrame(
        [
            {
                "product_id": "p-1",
                "product_reference": "REF-OLD",
                "landing_status": "landed",
                "landing_date": "2025-06-01",
                "warehouse": "Bristol",
                "bags": 10,
                "bags_available": 4,
                "bag_size_kg": 30,
                "price_per_kg": 11.0,
            },
            {
                "product_id": "p-2",
                "product_reference": "REF-MID",
                "landing_status": "landed",
                "landing_date": "2025-12-15",
                "warehouse": "London",
                "bags": 8,
                "bags_available": 2,
                "bag_size_kg": 25,
                "price_per_kg": 12.0,
            },
            {
                "product_id": "p-3",
                "product_reference": "REF-NEW",
                "landing_status": "landed",
                "landing_date": "2026-02-20",
                "warehouse": "London",
                "bags": 5,
                "bags_available": 1,
                "bag_size_kg": 20,
                "price_per_kg": "",
            },
            {
                "product_id": "p-4",
                "product_reference": "REF-NODATE",
                "landing_status": "landed",
                "landing_date": "",
                "warehouse": "Antwerp",
                "bags": 6,
                "bags_available": "",
                "bag_size_kg": 25,
                "price_per_kg": 13.0,
            },
            {
                "product_id": "p-5",
                "product_reference": "REF-INCOMING",
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "Antwerp",
                "bags": 3,
                "bags_available": 3,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
            },
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert dataset["default_landed_reference"] == "REF-MID"
    assert dataset["landed_reference_options"] == [
        {"product_reference": "REF-MID"},
        {"product_reference": "REF-NEW"},
        {"product_reference": "REF-NODATE"},
        {"product_reference": "REF-OLD"},
    ]
    assert dataset["landed_stock_summary"] == {
        "as_of_date": "2026-03-07",
        "landed_bags": 29.0,
        "unsold_landed_bags": 7.0,
        "unsold_landed_kg": 190.0,
        "unsold_landed_kg_available": True,
        "aged_180_plus_bags": 4.0,
        "warehouses_exposed": 2,
        "unsold_landed_value_gbp": 1920.0,
        "unsold_landed_value_available": False,
        "value_completeness_status": "Unavailable on 1 unsold landed row(s) due to missing kg or price.",
    }
    assert dataset["landed_stock_aging"] == [
        {"aging_bucket": "0-30", "unsold_bags": 1.0},
        {"aging_bucket": "31-60", "unsold_bags": 0.0},
        {"aging_bucket": "61-90", "unsold_bags": 2.0},
        {"aging_bucket": "91-180", "unsold_bags": 0.0},
        {"aging_bucket": "181-270", "unsold_bags": 0.0},
        {"aging_bucket": "270+", "unsold_bags": 4.0},
    ]
    assert [row["aging_bucket"] for row in dataset["landed_stock_aging"]] == [
        "0-30",
        "31-60",
        "61-90",
        "91-180",
        "181-270",
        "270+",
    ]
    assert dataset["landed_stock_warehouse_exposure"] == [
        {"warehouse": "Bristol", "unsold_bags": 4.0, "unsold_kg": 120.0},
        {"warehouse": "London", "unsold_bags": 3.0, "unsold_kg": 70.0},
    ]
    assert dataset["landed_stock_reference_exposure"] == [
        {"product_reference": "REF-OLD", "unsold_bags": 4.0, "unsold_kg": 120.0},
        {"product_reference": "REF-MID", "unsold_bags": 2.0, "unsold_kg": 50.0},
        {"product_reference": "REF-NEW", "unsold_bags": 1.0, "unsold_kg": 20.0},
    ]
    assert dataset["landed_stock_details"] == [
        {
            "product_reference": "REF-OLD",
            "product_id": "p-1",
            "warehouse": "Bristol",
            "landing_date": "2025-06-01",
            "days_since_landing": 279,
            "aging_bucket": "270+",
            "landed_bags": 10.0,
            "unsold_bags": 4.0,
            "unsold_kg": 120.0,
            "unsold_value_gbp": 1320.0,
            "data_status": "Complete",
        },
        {
            "product_reference": "REF-MID",
            "product_id": "p-2",
            "warehouse": "London",
            "landing_date": "2025-12-15",
            "days_since_landing": 82,
            "aging_bucket": "61-90",
            "landed_bags": 8.0,
            "unsold_bags": 2.0,
            "unsold_kg": 50.0,
            "unsold_value_gbp": 600.0,
            "data_status": "Complete",
        },
        {
            "product_reference": "REF-NEW",
            "product_id": "p-3",
            "warehouse": "London",
            "landing_date": "2026-02-20",
            "days_since_landing": 15,
            "aging_bucket": "0-30",
            "landed_bags": 5.0,
            "unsold_bags": 1.0,
            "unsold_kg": 20.0,
            "unsold_value_gbp": None,
            "data_status": "Unsold value unavailable",
        },
        {
            "product_reference": "REF-NODATE",
            "product_id": "p-4",
            "warehouse": "Antwerp",
            "landing_date": "",
            "days_since_landing": None,
            "aging_bucket": "Date unavailable",
            "landed_bags": 6.0,
            "unsold_bags": None,
            "unsold_kg": None,
            "unsold_value_gbp": None,
            "data_status": "Unsold bags unavailable; Landing date unavailable",
        },
    ]


def test_builder_client_intelligence_keeps_current_exposure_and_safe_concentration_only() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-01",
                "approval_date": "2026-03-02",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
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
                "id_request": "r-2",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-01",
                "approval_date": "2026-03-02",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "product_id": "p-2",
                "product_reference": "REF-2",
                "bags": 2,
                "bags_remaining": 2,
                "bag_size_kg": 30,
                "price_per_kg": "",
                "landing_status": "landed",
                "landing_date": "2026-03-10",
                "warehouse": "Bristol",
            },
            {
                "id_request": "r-3",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "completed",
                "request_date": "2026-03-03",
                "approval_date": "2026-03-04",
                "amendment_date": "2026-03-07",
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "product_id": "p-3",
                "product_reference": "REF-3",
                "bags": 1,
                "bags_remaining": 1,
                "bag_size_kg": 20,
                "price_per_kg": 15.0,
                "landing_status": "landed",
                "landing_date": "2026-03-06",
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
                "bags": 2,
                "bag_size_kg": 30,
                "bags_available": 0,
            },
            {
                "product_id": "p-2",
                "product_reference": "REF-2",
                "landing_status": "landed",
                "landing_date": "2026-03-10",
                "warehouse": "Bristol",
                "bags": 2,
                "bag_size_kg": 30,
                "bags_available": 0,
            },
            {
                "product_id": "p-3",
                "product_reference": "REF-3",
                "landing_status": "landed",
                "landing_date": "2026-03-06",
                "warehouse": "Bristol",
                "bags": 1,
                "bag_size_kg": 20,
                "bags_available": 0,
            },
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert dataset["client_summary"] == {
        "clients_with_current_exposure": 2,
        "total_current_reserved_value_gbp": 900.0,
        "total_current_reserved_value_available": False,
        "largest_client_company_name": "Alpha Roasters",
        "largest_client_id": "c-1",
        "largest_client_reserved_value_gbp": 600.0,
        "largest_client_reserved_value_available": False,
        "clients_concentrated_in_one_reference": 1,
    }
    assert dataset["client_details"] == [
        {
            "company_name": "Alpha Roasters",
            "client_id": "c-1",
            "reservation_row_count": 2,
            "reserved_bags": 4.0,
            "reserved_kg": 120.0,
            "reserved_value_gbp": 600.0,
            "reserved_value_available": False,
            "distinct_reference_count": 2,
            "primary_reference": "REF-1",
            "primary_reference_share": 0.5,
            "primary_reference_share_available": True,
            "landing_mix": "Mixed",
        },
        {
            "company_name": "Bravo Coffee",
            "client_id": "c-2",
            "reservation_row_count": 1,
            "reserved_bags": 1.0,
            "reserved_kg": 20.0,
            "reserved_value_gbp": 300.0,
            "reserved_value_available": True,
            "distinct_reference_count": 1,
            "primary_reference": "REF-3",
            "primary_reference_share": 1.0,
            "primary_reference_share_available": True,
            "landing_mix": "Landed",
        },
    ]
    assert dataset["client_top_exposure"] == [
        {"company_name": "Alpha Roasters", "client_id": "c-1", "reserved_value_gbp": 600.0},
        {"company_name": "Bravo Coffee", "client_id": "c-2", "reserved_value_gbp": 300.0},
    ]
    assert dataset["client_reference_concentration"] == [
        {"company_name": "Alpha Roasters", "client_id": "c-1", "product_reference": "REF-1", "reserved_value_gbp": 600.0},
        {"company_name": "Alpha Roasters", "client_id": "c-1", "product_reference": "REF-2", "reserved_value_gbp": 0.0},
        {"company_name": "Bravo Coffee", "client_id": "c-2", "product_reference": "REF-3", "reserved_value_gbp": 300.0},
    ]
    assert dataset["client_activity_rows"] == [
        {
            "company_name": "Alpha Roasters",
            "client_id": "c-1",
            "client_key": "c-1",
            "product_reference": "REF-1",
            "request_date": "2026-03-01",
            "request_date_available": True,
            "landing_status": "Incoming",
            "effective_bags": 2.0,
            "reserved_kg": 60.0,
            "reserved_value_gbp": 600.0,
            "reserved_value_available": True,
        },
        {
            "company_name": "Alpha Roasters",
            "client_id": "c-1",
            "client_key": "c-1",
            "product_reference": "REF-2",
            "request_date": "2026-03-01",
            "request_date_available": True,
            "landing_status": "Landed",
            "effective_bags": 2.0,
            "reserved_kg": 60.0,
            "reserved_value_gbp": 0.0,
            "reserved_value_available": False,
        },
        {
            "company_name": "Bravo Coffee",
            "client_id": "c-2",
            "client_key": "c-2",
            "product_reference": "REF-3",
            "request_date": "2026-03-03",
            "request_date_available": True,
            "landing_status": "Landed",
            "effective_bags": 1.0,
            "reserved_kg": 20.0,
            "reserved_value_gbp": 300.0,
            "reserved_value_available": True,
        },
    ]


def test_builder_client_activity_rows_keep_missing_request_date_for_default_client_view() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "",
                "approval_date": "2026-07-30",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "product_id": "p-1",
                "product_reference": "REF-1",
                "bags": 2,
                "bags_remaining": 2,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "incoming",
            },
            {
                "id_request": "r-2",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-08-02",
                "approval_date": "2026-08-03",
                "amendment_date": "",
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "product_id": "p-2",
                "product_reference": "REF-2",
                "bags": 1,
                "bags_remaining": 1,
                "bag_size_kg": 20,
                "price_per_kg": 12.0,
                "landing_status": "landed",
            },
        ]
    )
    products = pd.DataFrame(
        [
            {"product_id": "p-1", "product_reference": "REF-1", "landing_status": "incoming"},
            {"product_id": "p-2", "product_reference": "REF-2", "landing_status": "landed"},
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert dataset["client_summary"]["clients_with_current_exposure"] == 2
    assert dataset["client_activity_rows"] == [
        {
            "company_name": "Alpha Roasters",
            "client_id": "c-1",
            "client_key": "c-1",
            "product_reference": "REF-1",
            "request_date": "",
            "request_date_available": False,
            "landing_status": "Incoming",
            "effective_bags": 2.0,
            "reserved_kg": 60.0,
            "reserved_value_gbp": 600.0,
            "reserved_value_available": True,
        },
        {
            "company_name": "Bravo Coffee",
            "client_id": "c-2",
            "client_key": "c-2",
            "product_reference": "REF-2",
            "request_date": "2026-08-02",
            "request_date_available": True,
            "landing_status": "Landed",
            "effective_bags": 1.0,
            "reserved_kg": 20.0,
            "reserved_value_gbp": 240.0,
            "reserved_value_available": True,
        },
    ]


def test_builder_reservation_action_queue_uses_strict_open_rows_and_safe_expiry_logic() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-01",
                "approval_date": "2026-03-02",
                "amendment_date": "2026-03-10",
                "reservation_days": 7,
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "product_id": "p-1",
                "product_reference": "REF-1",
                "bags": 5,
                "bags_remaining": 3,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "landed",
                "landing_date": "2026-03-08",
                "warehouse": "London",
            },
            {
                "id_request": "r-2",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-04",
                "approval_date": "2026-03-05",
                "amendment_date": "2026-03-10",
                "reservation_days": 10,
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "product_id": "p-2",
                "product_reference": "REF-2",
                "bags": 4,
                "bags_remaining": 2,
                "bag_size_kg": 20,
                "price_per_kg": 11.0,
                "landing_status": "incoming",
                "landing_date": "2026-03-18",
                "warehouse": "Bristol",
            },
            {
                "id_request": "r-3",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "completed",
                "request_date": "2026-03-06",
                "approval_date": "",
                "amendment_date": "2026-03-10",
                "reservation_days": "",
                "client_id": "c-3",
                "company_name": "Charlie Coffee",
                "product_id": "p-3",
                "product_reference": "REF-3",
                "bags": 6,
                "bags_remaining": 1,
                "bag_size_kg": 25,
                "price_per_kg": "",
                "landing_status": "landed",
                "landing_date": "2026-03-09",
                "warehouse": "Antwerp",
            },
            {
                "id_request": "r-4",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-07",
                "approval_date": "2026-03-07",
                "amendment_date": "2026-03-09",
                "reservation_days": 5,
                "client_id": "c-4",
                "company_name": "Delta Coffee",
                "product_id": "p-4",
                "product_reference": "REF-4",
                "bags": 2,
                "bags_remaining": 0,
                "bag_size_kg": 20,
                "price_per_kg": 9.0,
                "landing_status": "landed",
                "landing_date": "2026-03-07",
                "warehouse": "London",
            },
        ]
    )
    products = pd.DataFrame(
        [
            {"product_id": "p-1", "product_reference": "REF-1", "landing_status": "landed", "landing_date": "2026-03-08", "warehouse": "London", "bags": 5, "bag_size_kg": 30, "bags_available": 2},
            {"product_id": "p-2", "product_reference": "REF-2", "landing_status": "incoming", "landing_date": "2026-03-18", "warehouse": "Bristol", "bags": 4, "bag_size_kg": 20, "bags_available": 2},
            {"product_id": "p-3", "product_reference": "REF-3", "landing_status": "landed", "landing_date": "2026-03-09", "warehouse": "Antwerp", "bags": 6, "bag_size_kg": 25, "bags_available": 1},
            {"product_id": "p-4", "product_reference": "REF-4", "landing_status": "landed", "landing_date": "2026-03-07", "warehouse": "London", "bags": 2, "bag_size_kg": 20, "bags_available": 0},
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)
    queue = dataset["reservation_action_queue"]

    assert dataset["snapshot_date"] == "2026-03-10"
    assert queue["summary"] == {
        "as_of_date": "2026-03-10",
        "near_expiry_threshold_days": 7,
        "open_reservation_rows": 3,
        "open_reserved_bags": 6.0,
        "near_expiry_rows": 1,
        "breached_rows": 1,
        "landed_not_released_value_gbp": 900.0,
        "landed_not_released_value_available": False,
        "landed_not_released_value_status": "Unavailable on one or more landed open reservation rows due to missing kg or price.",
        "action_now_rows": 3,
    }
    assert queue["action_bucket_counts"] == [
        {"action_bucket": "Breached", "row_count": 1},
        {"action_bucket": "Near Expiry", "row_count": 1},
        {"action_bucket": "Landed Not Approved", "row_count": 0},
        {"action_bucket": "Landed Not Released", "row_count": 1},
        {"action_bucket": "Open Exposure", "row_count": 0},
    ]
    assert queue["open_bags_by_expiry_bucket"] == [
        {"expiry_bucket": "Breached", "open_bags": 3.0},
        {"expiry_bucket": "0-7 days", "open_bags": 2.0},
        {"expiry_bucket": "8+ days", "open_bags": 0.0},
        {"expiry_bucket": "No expiry data", "open_bags": 1.0},
    ]
    assert queue["top_landed_references"] == {
        "metric": "open_bags",
        "metric_label": "Landed Not Released Bags",
        "value_available": False,
        "status": "Value incomplete for one or more landed open reservation rows; showing bags instead.",
        "rows": [
            {
                "product_reference": "REF-1",
                "open_bags": 3.0,
                "remaining_kg": 90.0,
                "remaining_value_gbp": 900.0,
            },
            {
                "product_reference": "REF-3",
                "open_bags": 1.0,
                "remaining_kg": 25.0,
                "remaining_value_gbp": 0.0,
            },
        ],
    }
    assert queue["details"][0]["action_priority"] == "P1 Breached"
    assert queue["details"][0]["action_bucket"] == "Breached"
    assert queue["details"][0]["days_to_expiry"] == -1
    assert queue["details"][0]["remaining_value_gbp"] == 900.0
    assert queue["details"][1]["action_priority"] == "P2 Near Expiry"
    assert queue["details"][1]["days_to_expiry"] == 5
    assert queue["details"][2]["action_priority"] == "P4 Landed Not Released"
    assert queue["details"][2]["request_status"] == "Completed"
    assert queue["details"][2]["remaining_value_gbp"] is None
    assert queue["details"][2]["data_status"] == "Approval date unavailable; Reservation days unavailable; Remaining value unavailable"


def test_builder_splits_landed_not_approved_from_landed_not_released() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-03-10",
                "approval_date": "",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "product_id": "p-1",
                "product_reference": "REF-1",
                "bags": 3,
                "bags_remaining": 3,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "landed",
                "landing_date": "2026-03-08",
                "warehouse": "London",
            },
            {
                "id_request": "r-2",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-10",
                "approval_date": "2026-03-10",
                "amendment_date": "",
                "reservation_days": 30,
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "product_id": "p-2",
                "product_reference": "REF-2",
                "bags": 2,
                "bags_remaining": 2,
                "bag_size_kg": 20,
                "price_per_kg": 12.0,
                "landing_status": "landed",
                "landing_date": "2026-03-07",
                "warehouse": "Bristol",
            },
        ]
    )
    products = pd.DataFrame(
        [
            {"product_id": "p-1", "product_reference": "REF-1", "landing_status": "landed", "landing_date": "2026-03-08", "warehouse": "London", "bags": 3, "bag_size_kg": 30, "bags_available": 0},
            {"product_id": "p-2", "product_reference": "REF-2", "landing_status": "landed", "landing_date": "2026-03-07", "warehouse": "Bristol", "bags": 2, "bag_size_kg": 20, "bags_available": 0},
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)
    queue = dataset["reservation_action_queue"]

    assert queue["action_bucket_counts"] == [
        {"action_bucket": "Breached", "row_count": 0},
        {"action_bucket": "Near Expiry", "row_count": 0},
        {"action_bucket": "Landed Not Approved", "row_count": 1},
        {"action_bucket": "Landed Not Released", "row_count": 1},
        {"action_bucket": "Open Exposure", "row_count": 0},
    ]
    assert queue["details"][0]["action_bucket"] == "Landed Not Approved"
    assert queue["details"][0]["action_priority"] == "P3 Landed Not Approved"
    assert queue["details"][0]["request_status"] == "Created"
    assert queue["details"][1]["action_bucket"] == "Landed Not Released"
    assert queue["details"][1]["action_priority"] == "P4 Landed Not Released"

from __future__ import annotations

import pandas as pd

from mcop.reference_workspace.builder import RESERVATION_NOTE, build_reference_workspace_dataset


def test_builder_uses_latest_non_rejected_reservation_row_per_key_and_keeps_completed_visible() -> None:
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
            {"product_id": "p-1", "product_reference": "REF-1", "landing_status": "incoming"},
            {"product_id": "p-2", "product_reference": "REF-1", "landing_status": "landed"},
            {"product_id": "p-3", "product_reference": "REF-2", "landing_status": "incoming"},
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
            "reserved_kg": 110.0,
            "reserved_value_gbp": 1150.0,
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


def test_builder_keeps_latest_row_per_reservation_product_combination() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "678",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-01-27",
                "approval_date": "",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "contact_first_name": "Ava",
                "contact_last_name": "Stone",
                "product_id": "130",
                "product_reference": "product_134",
                "bags": 4,
                "bags_remaining": 4,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "incoming",
                "landing_date": "2026-03-31",
                "warehouse": "London",
            },
            {
                "id_request": "678",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-01-27",
                "approval_date": "",
                "amendment_date": "",
                "client_id": "c-1",
                "company_name": "Alpha Roasters",
                "contact_first_name": "Ava",
                "contact_last_name": "Stone",
                "product_id": "78",
                "product_reference": "product_11",
                "bags": 1,
                "bags_remaining": 1,
                "bag_size_kg": 60,
                "price_per_kg": 8.0,
                "landing_status": "landed",
                "landing_date": "2026-02-15",
                "warehouse": "Bristol",
            },
            {
                "id_request": "731",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-02-10",
                "approval_date": "",
                "amendment_date": "2026-03-07",
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "contact_first_name": "Ben",
                "contact_last_name": "Hart",
                "product_id": "130",
                "product_reference": "product_134",
                "bags": 4,
                "bags_remaining": 4,
                "bag_size_kg": 30,
                "price_per_kg": 10.0,
                "landing_status": "incoming",
                "landing_date": "2026-03-31",
                "warehouse": "London",
            },
            {
                "id_request": "731",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "created",
                "request_date": "2026-02-10",
                "approval_date": "",
                "amendment_date": "2026-03-07",
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "contact_first_name": "Ben",
                "contact_last_name": "Hart",
                "product_id": "127",
                "product_reference": "product_128",
                "bags": 2,
                "bags_remaining": 2,
                "bag_size_kg": 30,
                "price_per_kg": 12.0,
                "landing_status": "incoming",
                "landing_date": "2026-03-20",
                "warehouse": "London",
            },
        ]
    )
    products = pd.DataFrame(
        [
            {"product_id": "130", "product_reference": "product_134", "landing_status": "incoming"},
            {"product_id": "78", "product_reference": "product_11", "landing_status": "landed"},
            {"product_id": "127", "product_reference": "product_128", "landing_status": "incoming"},
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert [row for row in dataset["reference_options"] if row["product_reference"] == "product_134"] == [
        {
            "product_reference": "product_134",
            "has_reservations": True,
            "landing_status": "Incoming",
        }
    ]
    assert [row for row in dataset["reference_summary"] if row["product_reference"] == "product_134"] == [
        {
            "product_reference": "product_134",
            "landing_status": "Incoming",
            "is_landed": False,
            "reservation_row_count": 2,
            "client_count": 2,
            "reserved_bags": 8.0,
            "reserved_kg": 240.0,
            "reserved_value_gbp": 2400.0,
        }
    ]
    assert [row["reservation_key"] for row in dataset["reservation_details"] if row["product_reference"] == "product_134"] == [
        "678",
        "731",
    ]


def test_builder_uses_product_landing_status_only_when_activity_row_blank() -> None:
    activity = pd.DataFrame(
        [
            {
                "id_request": "r-1",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-01",
                "approval_date": "2026-03-03",
                "amendment_date": "",
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
                "landing_status": "",
                "landing_date": "2026-03-20",
                "warehouse": "London",
            },
            {
                "id_request": "r-2",
                "id_booking": "",
                "request_type": "reservation",
                "request_status": "approved",
                "request_date": "2026-03-02",
                "approval_date": "2026-03-04",
                "amendment_date": "",
                "client_id": "c-2",
                "company_name": "Bravo Coffee",
                "contact_first_name": "Ben",
                "contact_last_name": "Hart",
                "product_id": "p-2",
                "product_reference": "REF-2",
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
            {"product_id": "p-1", "product_reference": "REF-1", "landing_status": "incoming"},
            {"product_id": "p-2", "product_reference": "REF-2", "landing_status": "incoming"},
        ]
    )

    dataset = build_reference_workspace_dataset(activity, products)

    assert [row for row in dataset["reference_summary"] if row["product_reference"] == "REF-1"] == [
        {
            "product_reference": "REF-1",
            "landing_status": "Incoming",
            "is_landed": False,
            "reservation_row_count": 1,
            "client_count": 1,
            "reserved_bags": 3.0,
            "reserved_kg": 90.0,
            "reserved_value_gbp": 900.0,
        }
    ]
    assert [row for row in dataset["reference_summary"] if row["product_reference"] == "REF-2"] == [
        {
            "product_reference": "REF-2",
            "landing_status": "Landed",
            "is_landed": True,
            "reservation_row_count": 1,
            "client_count": 1,
            "reserved_bags": 1.0,
            "reserved_kg": 20.0,
            "reserved_value_gbp": 250.0,
        }
    ]

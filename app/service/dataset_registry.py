from __future__ import annotations


DATASET_DEFINITIONS: tuple[dict[str, object], ...] = (
    {
        "dataset_type": "activity",
        "label": "Activity",
        "description": "Reservation, sample, and release activity events.",
        "required": True,
        "blocking_for_build": True,
        "validation_kind": "tabular",
        "accepted_extensions": (".csv", ".xlsx"),
        "required_columns": (
            "product_id",
            "bag_size_kg",
            "bags",
            "price_per_kg",
            "reservation_days",
            "payment_days",
            "landing_date",
        ),
    },
    {
        "dataset_type": "products",
        "label": "Products",
        "description": "Current stock and landed status by product.",
        "required": True,
        "blocking_for_build": True,
        "validation_kind": "tabular",
        "accepted_extensions": (".csv", ".xlsx"),
        "required_columns": (
            "product_id",
            "product_reference",
            "bag_size_kg",
            "bags",
            "bags_remaining",
            "price_per_kg",
            "landing_status",
            "landing_date",
        ),
    },
    {
        "dataset_type": "product_costs_protected",
        "label": "Product Costs Protected",
        "description": "Protected cost dataset accepted by the app, but non-blocking for the current slice.",
        "required": False,
        "blocking_for_build": False,
        "validation_kind": "tabular",
        "accepted_extensions": (".csv", ".xlsx"),
        "required_columns": (
            "product_id",
            "bag_size",
            "bags",
            "cost_of_green_coffee_gbp_kg",
            "cost_farm_to_port_gbp_kg",
            "freight_cost_gbp_kg",
            "cost_uk_port_to_warehouse_gbp_kg",
            "initial_payment_pct",
            "remaining_payment_pct",
            "initial_payment_date",
            "remaining_payment_date",
            "harvest_date",
            "landing_date",
        ),
    },
    {
        "dataset_type": "cash_position",
        "label": "Cash Position",
        "description": "Cash position history or Xero snapshot accepted by the app, but non-blocking for the current slice.",
        "required": False,
        "blocking_for_build": False,
        "validation_kind": "cash_position",
        "accepted_extensions": (".csv", ".xlsx", ".json"),
        "required_columns": ("date", "cash_on_hand"),
    },
    {
        "dataset_type": "clients",
        "label": "Clients",
        "description": "Optional client master data used for richer client and draft workflow context.",
        "required": False,
        "blocking_for_build": False,
        "validation_kind": "tabular",
        "accepted_extensions": (".csv", ".xlsx"),
        "required_columns": ("client_id", "company_name"),
    },
)


def get_dataset_definition(dataset_type: str) -> dict[str, object]:
    for definition in DATASET_DEFINITIONS:
        if definition["dataset_type"] == dataset_type:
            return definition
    raise KeyError(f"Unsupported dataset type: {dataset_type}")

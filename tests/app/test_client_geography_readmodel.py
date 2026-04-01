from __future__ import annotations

from app.readmodels.client_geography import build_client_geography_readmodel


def test_build_client_geography_readmodel_preserves_trusted_outputs_and_derives_filters() -> None:
    dataset = {
        "snapshot_date": "2026-03-07",
        "client_geography_summary": {
            "mapped_clients": 2,
            "unmapped_clients": 1,
            "map_status": "Plotting 1 deterministically resolved client markers; 1 mapped clients remain unplotted.",
        },
        "client_geography_locations": [
            {
                "country": "United Kingdom",
                "city": "Bristol",
                "postcode": "BS1 4DJ",
                "client_count": 1,
                "exposed_client_count": 1,
            },
            {
                "country": "Netherlands",
                "city": "Amsterdam",
                "postcode": "1012 JS",
                "client_count": 1,
                "exposed_client_count": 0,
            },
        ],
        "client_geography_map_clients": [
            {"marker_id": "c-1", "country": "United Kingdom", "city": "Bristol"},
        ],
        "client_geography_unmapped_clients": [
            {"client_id": "", "company_name": "No ID Coffee", "reason": "Missing client_id on activity rows"},
        ],
        "client_geography_top_countries": [{"country": "United Kingdom"}],
        "client_geography_top_cities": [{"city": "Bristol"}],
    }

    payload = build_client_geography_readmodel(dataset)

    assert payload["snapshot_date"] == "2026-03-07"
    assert payload["summary"]["mapped_clients"] == 2
    assert payload["locations"] == dataset["client_geography_locations"]
    assert payload["map_clients"] == dataset["client_geography_map_clients"]
    assert payload["unmapped_clients"] == dataset["client_geography_unmapped_clients"]
    assert payload["filters"] == {
        "countries": ["Netherlands", "United Kingdom"],
        "cities": ["Amsterdam", "Bristol"],
        "exposure_states": ["all", "exposed", "no-exposure"],
    }

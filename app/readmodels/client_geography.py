from __future__ import annotations


def build_client_geography_readmodel(dataset: dict[str, object]) -> dict[str, object]:
    locations = list(dataset.get("client_geography_locations") or [])
    map_clients = list(dataset.get("client_geography_map_clients") or [])
    unmapped_clients = list(dataset.get("client_geography_unmapped_clients") or [])

    countries = sorted(
        {
            str(row.get("country") or "").strip()
            for row in locations
            if str(row.get("country") or "").strip()
        }
    )
    cities = sorted(
        {
            str(row.get("city") or "").strip()
            for row in locations
            if str(row.get("city") or "").strip()
        }
    )

    return {
        "snapshot_date": str(dataset.get("snapshot_date") or ""),
        "summary": dict(dataset.get("client_geography_summary") or {}),
        "locations": locations,
        "map_clients": map_clients,
        "unmapped_clients": unmapped_clients,
        "top_countries": list(dataset.get("client_geography_top_countries") or []),
        "top_cities": list(dataset.get("client_geography_top_cities") or []),
        "filters": {
            "countries": countries,
            "cities": cities,
            "exposure_states": ["all", "exposed", "no-exposure"],
        },
    }

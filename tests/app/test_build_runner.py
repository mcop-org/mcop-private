from __future__ import annotations

import base64
import json
from pathlib import Path
from urllib import error

from app.service.build_runner import run_build
from app.service.config import get_service_paths
from app.service.dataset_loader import save_uploaded_dataset
from app.service.routes_modules import get_module_artifacts
from mcop.reference_workspace import uk_postcode_service


def _encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class _FakeHTTPResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def _install_mock_postcodes_io_urlopen(
    monkeypatch,
    postcode_rows: dict[str, dict[str, object]],
    requests_seen: list[str],
) -> None:
    def fake_urlopen(http_request, timeout=0):  # type: ignore[no-untyped-def]
        full_url = http_request.full_url
        requests_seen.append(full_url)
        postcode = full_url.rsplit("/postcodes/", 1)[-1].replace("%20", " ")
        row = postcode_rows.get(postcode)
        if row is None:
            raise error.HTTPError(full_url, 404, "Invalid postcode", hdrs=None, fp=None)
        return _FakeHTTPResponse({"status": 200, "result": row})

    monkeypatch.setattr(uk_postcode_service.request, "urlopen", fake_urlopen)


def test_run_build_materializes_readmodels(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "products",
        "products.csv",
        _encode(
            "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date\n"
            "p1,REF-1,30,4,2,10.0,incoming,2026-03-20\n"
        ),
    )
    save_uploaded_dataset(
        "activity",
        "activity.csv",
        _encode(
            "id_request,product_id,request_type,request_status,request_date,approval_date,amendment_date,reservation_days,payment_days,client_id,company_name,product_reference,bags,bags_remaining,bag_size_kg,price_per_kg,landing_status,landing_date,warehouse\n"
            "r1,p1,reservation,approved,2026-03-01,2026-03-02,2026-03-03,14,30,c1,Alpha,REF-1,4,2,30,10.0,incoming,2026-03-20,London\n"
        ),
    )
    save_uploaded_dataset(
        "clients",
        "clients.csv",
        _encode("client_id,company_name,contact_email\nc1,Alpha,alpha@example.test\n"),
    )

    payload = run_build()
    paths = get_service_paths()

    assert payload["state"] == "ready"
    assert payload["artifacts"] == get_module_artifacts()
    for artifact_name in payload["artifacts"].values():
        assert (paths.readmodels_dir / artifact_name).exists()

    landed_stock = json.loads(
        (paths.readmodels_dir / "landed_stock_intelligence.json").read_text(encoding="utf-8")
    )
    assert "aging" in landed_stock
    assert "warehouse_exposure" in landed_stock
    assert "reference_exposure" in landed_stock


def test_run_build_succeeds_when_optional_contracts_are_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "products",
        "products.csv",
        _encode(
            "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date\n"
            "p1,REF-1,30,4,2,10.0,incoming,2026-03-20\n"
        ),
    )
    save_uploaded_dataset(
        "activity",
        "activity.csv",
        _encode(
            "id_request,product_id,request_type,request_status,request_date,approval_date,amendment_date,reservation_days,payment_days,client_id,company_name,product_reference,bags,bags_remaining,bag_size_kg,price_per_kg,landing_status,landing_date,warehouse\n"
            "r1,p1,reservation,approved,2026-03-01,2026-03-02,2026-03-03,14,30,c1,Alpha,REF-1,4,2,30,10.0,incoming,2026-03-20,London\n"
        ),
    )

    payload = run_build()

    assert payload["state"] == "ready"


def test_run_build_blocks_only_on_current_slice_required_datasets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "activity",
        "activity.csv",
        _encode(
            "id_request,product_id,request_type,request_status,request_date,approval_date,amendment_date,reservation_days,payment_days,client_id,company_name,product_reference,bags,bags_remaining,bag_size_kg,price_per_kg,landing_status,landing_date,warehouse\n"
            "r1,p1,reservation,approved,2026-03-01,2026-03-02,2026-03-03,14,30,c1,Alpha,REF-1,4,2,30,10.0,incoming,2026-03-20,London\n"
        ),
    )

    payload = run_build()

    assert payload["state"] == "blocked"
    assert "Products" in payload["message"]


def test_run_build_can_enable_uk_postcode_service_and_reuse_cache(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "products",
        "products.csv",
        _encode(
            "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date\n"
            "p1,REF-1,30,4,2,10.0,incoming,2026-03-20\n"
        ),
    )
    save_uploaded_dataset(
        "activity",
        "activity.csv",
        _encode(
            "id_request,product_id,request_type,request_status,request_date,approval_date,amendment_date,reservation_days,payment_days,client_id,company_name,product_reference,bags,bags_remaining,bag_size_kg,price_per_kg,landing_status,landing_date,warehouse\n"
            "r1,p1,reservation,approved,2026-03-01,2026-03-02,2026-03-03,14,30,c1,Hebden Bridge Coffee,REF-1,4,2,30,10.0,incoming,2026-03-20,London\n"
        ),
    )
    save_uploaded_dataset(
        "clients",
        "clients.csv",
        _encode(
            "client_id,company_name,country,city,postcode,contact_email\n"
            "c1,Hebden Bridge Coffee,United Kingdom,Hebden Bridge,HX7 7ZZ,alpha@example.test\n"
        ),
    )

    monkeypatch.delenv("MCOP_APP_ENABLE_UK_POSTCODE_SERVICE", raising=False)
    monkeypatch.delenv("MCOP_APP_UK_POSTCODE_SERVICE_URL", raising=False)
    monkeypatch.delenv("MCOP_APP_UK_POSTCODE_SERVICE_TIMEOUT_SECONDS", raising=False)

    payload = run_build()
    paths = get_service_paths()
    dataset = json.loads((paths.readmodels_dir / "reference_workspace_dataset.json").read_text(encoding="utf-8"))
    assert payload["state"] == "ready"
    assert dataset["client_geography_summary"]["resolved_map_clients"] == 0
    assert dataset["client_geography_summary"]["unresolved_map_clients"] == 1
    assert dataset["client_geography_plot_diagnostics"]["grouped_exclusion_stages"] == [
        {"failure_stage": "gb postcode miss", "row_count": 1}
    ]

    requests_seen: list[str] = []
    _install_mock_postcodes_io_urlopen(
        monkeypatch,
        {
            "HX7 7ZZ": {
                "postcode": "HX7 7ZZ",
                "latitude": 53.742811,
                "longitude": -2.013076,
                "admin_district": "Hebden Bridge",
            }
        },
        requests_seen,
    )
    monkeypatch.setenv("MCOP_APP_ENABLE_UK_POSTCODE_SERVICE", "1")
    monkeypatch.setenv("MCOP_APP_UK_POSTCODE_SERVICE_URL", "http://internal-postcodes.test")
    monkeypatch.setenv("MCOP_APP_UK_POSTCODE_SERVICE_TIMEOUT_SECONDS", "1.5")

    payload = run_build()
    dataset = json.loads((paths.readmodels_dir / "reference_workspace_dataset.json").read_text(encoding="utf-8"))
    geography = json.loads((paths.readmodels_dir / "client_geography.json").read_text(encoding="utf-8"))
    assert payload["state"] == "ready"
    assert dataset["client_geography_summary"]["resolved_map_clients"] == 1
    assert dataset["client_geography_summary"]["unresolved_map_clients"] == 0
    assert dataset["client_geography_map_clients"][0]["latitude"] == 53.742811
    assert dataset["client_geography_map_clients"][0]["longitude"] == -2.013076
    assert dataset["client_geography_plot_diagnostics"]["resolver_cache_summary"] == {
        "resolver_version": "offline-geography-gb-v1",
        "entry_count": 1,
        "datasets": ["uk-postcode-service-v1"],
        "country_sources": ["uk-postcodes-io-internal"],
    }
    assert geography["map_clients"][0]["city"] == "Hebden Bridge"
    assert requests_seen == ["http://internal-postcodes.test/postcodes/HX7%207ZZ"]

    monkeypatch.setenv("MCOP_APP_UK_POSTCODE_SERVICE_URL", "http://127.0.0.1:1")
    payload = run_build()
    dataset = json.loads((paths.readmodels_dir / "reference_workspace_dataset.json").read_text(encoding="utf-8"))
    cache_payload = json.loads((paths.builds_dir / "client_geography_service_cache.json").read_text(encoding="utf-8"))
    assert payload["state"] == "ready"
    assert dataset["client_geography_summary"]["resolved_map_clients"] == 1
    assert dataset["client_geography_summary"]["unresolved_map_clients"] == 0
    assert dataset["client_geography_plot_diagnostics"]["resolver_cache_summary"] == {
        "resolver_version": "offline-geography-gb-v1",
        "entry_count": 1,
        "datasets": ["mcop-uk-postcode-cache-v1"],
        "country_sources": ["mcop-uk-postcode-cache"],
    }
    assert cache_payload == {
        "dataset_version": "mcop-uk-postcode-cache-v1",
        "rows": [
            {
                "city": "Hebden Bridge",
                "latitude": 53.742811,
                "longitude": -2.013076,
                "postcode": "HX7 7ZZ",
            }
        ],
        "source": "MCOP cached successful UK postcode service resolutions",
    }


def test_run_build_keeps_non_uk_behavior_unchanged_when_uk_service_enabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    save_uploaded_dataset(
        "products",
        "products.csv",
        _encode(
            "product_id,product_reference,bag_size_kg,bags,bags_available,price_per_kg,landing_status,landing_date\n"
            "p1,REF-1,30,4,2,10.0,incoming,2026-03-20\n"
        ),
    )
    save_uploaded_dataset(
        "activity",
        "activity.csv",
        _encode(
            "id_request,product_id,request_type,request_status,request_date,approval_date,amendment_date,reservation_days,payment_days,client_id,company_name,product_reference,bags,bags_remaining,bag_size_kg,price_per_kg,landing_status,landing_date,warehouse\n"
            "r1,p1,reservation,approved,2026-03-01,2026-03-02,2026-03-03,14,30,c1,Berlin Coffee,REF-1,4,2,30,10.0,incoming,2026-03-20,London\n"
        ),
    )
    save_uploaded_dataset(
        "clients",
        "clients.csv",
        _encode(
            "client_id,company_name,country,city,postcode,contact_email\n"
            "c1,Berlin Coffee,Germany,Berlin,10115,alpha@example.test\n"
        ),
    )

    requests_seen: list[str] = []
    _install_mock_postcodes_io_urlopen(monkeypatch, {}, requests_seen)
    monkeypatch.setenv("MCOP_APP_ENABLE_UK_POSTCODE_SERVICE", "1")
    monkeypatch.setenv("MCOP_APP_UK_POSTCODE_SERVICE_URL", "http://internal-postcodes.test")
    payload = run_build()
    paths = get_service_paths()
    dataset = json.loads((paths.readmodels_dir / "reference_workspace_dataset.json").read_text(encoding="utf-8"))
    assert payload["state"] == "ready"
    assert dataset["client_geography_summary"]["resolved_map_clients"] == 0
    assert dataset["client_geography_summary"]["unresolved_map_clients"] == 1
    assert dataset["client_geography_plot_diagnostics"]["grouped_exclusion_stages"] == [
        {"failure_stage": "offline dataset miss", "row_count": 1}
    ]
    assert dataset["client_geography_plot_diagnostics"]["grouped_exclusion_reasons"] == [
        {"reason": "No offline postcode dataset coverage for delivery country", "row_count": 1}
    ]
    assert requests_seen == []

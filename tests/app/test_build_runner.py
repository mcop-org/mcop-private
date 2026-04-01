from __future__ import annotations

import base64
from pathlib import Path

from app.service.build_runner import run_build
from app.service.config import get_service_paths
from app.service.dataset_loader import save_uploaded_dataset


def _encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


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
    assert (paths.readmodels_dir / "reservation_intelligence.json").exists()
    assert (paths.readmodels_dir / "action_queue.json").exists()
    assert (paths.readmodels_dir / "client_geography.json").exists()
    assert payload["artifacts"]["client_geography"] == "client_geography.json"


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

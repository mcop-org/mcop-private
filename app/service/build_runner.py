from __future__ import annotations

import json

from app.readmodels.action_queue import build_action_queue_readmodel
from app.readmodels.client_intelligence import build_client_intelligence_readmodel
from app.readmodels.client_geography import build_client_geography_readmodel
from app.readmodels.contracts import write_canonical_json
from app.readmodels.landed_stock_intelligence import build_landed_stock_intelligence_readmodel
from app.readmodels.product_reference_intelligence import (
    build_product_reference_intelligence_readmodel,
)
from app.readmodels.reservation_intelligence import build_reservation_intelligence_readmodel
from app.service.config import get_geography_service_settings, get_service_paths
from app.service.dataset_loader import prepare_build_data_dir
from app.service.dataset_validator import persist_dataset_status
from app.service.routes_modules import get_module_artifacts
from mcop.ingest.loaders import load_inputs
from mcop.reference_workspace.builder import build_reference_workspace_dataset
from mcop.reference_workspace.uk_postcode_service import UKPostcodeServiceConfig


def _build_status_payload(state: str, message: str, snapshot_date: str = "") -> dict[str, object]:
    return {
        "state": state,
        "message": message,
        "snapshot_date": snapshot_date,
        "artifacts": get_module_artifacts(),
    }


def run_build() -> dict[str, object]:
    paths = get_service_paths()
    geography_service_settings = get_geography_service_settings()
    dataset_status = persist_dataset_status()
    if not bool(dataset_status.get("build_ready")):
        blocking_rows = [
            row for row in list(dataset_status.get("datasets") or [])
            if bool(row.get("blocks_build"))
        ]
        blocking_message = "Required dataset contracts for the current slice are not satisfied."
        if blocking_rows:
            reasons = [
                f"{row.get('label')}: {row.get('build_blocking_reason') or 'Invalid dataset.'}"
                for row in blocking_rows
            ]
            blocking_message = " ".join(reasons)
        payload = _build_status_payload(
            "blocked",
            blocking_message,
        )
        write_canonical_json(paths.build_status_path, payload)
        return payload

    build_data_dir = prepare_build_data_dir()
    inputs = load_inputs(build_data_dir)
    dataset = build_reference_workspace_dataset(
        inputs.activity,
        inputs.products,
        inputs.clients,
        enable_uk_postcode_service=geography_service_settings.enable_uk_postcode_service,
        uk_postcode_service_cache_path=geography_service_settings.uk_postcode_service_cache_path,
        uk_postcode_service_config=UKPostcodeServiceConfig(
            enabled=geography_service_settings.enable_uk_postcode_service,
            base_url=geography_service_settings.uk_postcode_service_base_url,
            timeout_seconds=geography_service_settings.uk_postcode_service_timeout_seconds,
        ),
    )
    product_reference_readmodel = build_product_reference_intelligence_readmodel(dataset)
    reservation_readmodel = build_reservation_intelligence_readmodel(dataset)
    action_queue_readmodel = build_action_queue_readmodel(dataset)
    client_intelligence_readmodel = build_client_intelligence_readmodel(dataset)
    client_geography_readmodel = build_client_geography_readmodel(dataset)
    landed_stock_readmodel = build_landed_stock_intelligence_readmodel(dataset)
    write_canonical_json(
        paths.readmodels_dir / "product_reference_intelligence.json",
        product_reference_readmodel,
    )
    write_canonical_json(paths.readmodels_dir / "reservation_intelligence.json", reservation_readmodel)
    write_canonical_json(paths.readmodels_dir / "action_queue.json", action_queue_readmodel)
    write_canonical_json(
        paths.readmodels_dir / "client_intelligence.json",
        client_intelligence_readmodel,
    )
    write_canonical_json(paths.readmodels_dir / "client_geography.json", client_geography_readmodel)
    write_canonical_json(paths.readmodels_dir / "landed_stock_intelligence.json", landed_stock_readmodel)
    dataset_snapshot_path = paths.readmodels_dir / "reference_workspace_dataset.json"
    write_canonical_json(dataset_snapshot_path, dataset)
    payload = _build_status_payload(
        "ready",
        "Build completed successfully.",
        str(dataset.get("snapshot_date") or ""),
    )
    write_canonical_json(paths.build_status_path, payload)
    return payload


def get_build_status() -> dict[str, object]:
    paths = get_service_paths()
    if not paths.build_status_path.exists():
        return _build_status_payload("idle", "No build has been run yet.")
    return json.loads(paths.build_status_path.read_text(encoding="utf-8"))

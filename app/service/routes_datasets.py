from __future__ import annotations

from app.readmodels.datasets import build_dataset_contracts_readmodel
from app.service.contracts import Response
from app.service.dataset_loader import save_uploaded_dataset
from app.service.dataset_registry import DATASET_DEFINITIONS
from app.service.dataset_validator import persist_dataset_status


def handle_get_contracts() -> Response:
    return Response(
        status_code=200,
        payload=build_dataset_contracts_readmodel(DATASET_DEFINITIONS),
    )


def handle_load_dataset(body: dict[str, object]) -> Response:
    dataset_type = str(body.get("dataset_type") or "").strip()
    filename = str(body.get("filename") or "").strip()
    content_base64 = str(body.get("content_base64") or "").strip()
    if not dataset_type or not filename or not content_base64:
        return Response(
            status_code=400,
            payload={"error": "dataset_type, filename, and content_base64 are required."},
        )
    try:
        upload_result = save_uploaded_dataset(dataset_type, filename, content_base64)
        status_payload = persist_dataset_status()
    except Exception as exc:
        return Response(status_code=400, payload={"error": str(exc)})
    return Response(
        status_code=200,
        payload={
            "upload": upload_result,
            "status": status_payload,
        },
    )


def handle_get_status() -> Response:
    return Response(status_code=200, payload=persist_dataset_status())

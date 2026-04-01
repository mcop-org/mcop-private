from __future__ import annotations

from app.service.contracts import Response
from app.service.readmodel_store import load_readmodel


def handle_get_product_reference_intelligence() -> Response:
    payload = load_readmodel("product_reference_intelligence")
    if not payload:
        return Response(
            status_code=404,
            payload={"error": "Product reference read-model not available. Run a build first."},
        )
    return Response(status_code=200, payload=payload)


def handle_get_reservations() -> Response:
    payload = load_readmodel("reservation_intelligence")
    if not payload:
        return Response(
            status_code=404,
            payload={"error": "Reservation read-model not available. Run a build first."},
        )
    return Response(status_code=200, payload=payload)


def handle_get_action_queue() -> Response:
    payload = load_readmodel("action_queue")
    if not payload:
        return Response(
            status_code=404,
            payload={"error": "Action queue read-model not available. Run a build first."},
        )
    return Response(status_code=200, payload=payload)


def handle_get_client_geography() -> Response:
    payload = load_readmodel("client_geography")
    if not payload:
        return Response(
            status_code=404,
            payload={"error": "Client geography read-model not available. Run a build first."},
        )
    return Response(status_code=200, payload=payload)

from __future__ import annotations

from app.service.contracts import Response


def handle_health() -> Response:
    return Response(
        status_code=200,
        payload={
            "status": "ok",
            "service": "mcop-advanced-ui-local-service",
        },
    )

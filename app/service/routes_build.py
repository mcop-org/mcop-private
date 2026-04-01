from __future__ import annotations

from app.service.build_runner import get_build_status, run_build
from app.service.contracts import Response


def handle_run_build() -> Response:
    payload = run_build()
    status_code = 200 if payload.get("state") != "blocked" else 400
    return Response(status_code=status_code, payload=payload)


def handle_get_build_status() -> Response:
    return Response(status_code=200, payload=get_build_status())

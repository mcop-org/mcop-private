from __future__ import annotations

from pathlib import Path

from app.service.app import _dispatch
from app.service.routes_build import handle_get_build_status
from app.service.routes_health import handle_health
from app.service.routes_modules import (
    handle_get_action_queue,
    handle_get_client_geography,
    handle_get_product_reference_intelligence,
    handle_get_reservations,
)


def test_health_route_is_available() -> None:
    response = handle_health()
    assert response.status_code == 200
    assert response.payload["status"] == "ok"


def test_module_routes_return_not_found_before_build(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    product_reference = handle_get_product_reference_intelligence()
    reservations = handle_get_reservations()
    action_queue = handle_get_action_queue()
    geography = handle_get_client_geography()
    build_status = handle_get_build_status()

    assert product_reference.status_code == 404
    assert reservations.status_code == 404
    assert action_queue.status_code == 404
    assert geography.status_code == 404
    assert build_status.payload["state"] == "idle"


def test_module_dispatch_normalizes_duplicate_and_trailing_slashes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))

    product_reference = _dispatch("GET", "/modules/product-reference-intelligence/", None)
    geography = _dispatch("GET", "//modules/client-geography/", None)
    reservations = _dispatch("GET", "/modules/reservations/", None)
    action_queue = _dispatch("GET", "//modules/action-queue", None)

    assert product_reference.status_code == 404
    assert product_reference.payload["error"] != "Route not found."
    assert geography.status_code == 404
    assert geography.payload["error"] != "Route not found."
    assert reservations.status_code == 404
    assert reservations.payload["error"] != "Route not found."
    assert action_queue.status_code == 404
    assert action_queue.payload["error"] != "Route not found."


def test_module_dispatch_resolves_canonical_module_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MCOP_APP_WORKSPACE_ROOT", str(tmp_path / "workspace"))

    product_reference = _dispatch("GET", "/modules/product-reference-intelligence", None)
    geography = _dispatch("GET", "/modules/client-geography", None)
    reservations = _dispatch("GET", "/modules/reservations", None)
    action_queue = _dispatch("GET", "/modules/action-queue", None)

    assert product_reference.status_code == 404
    assert product_reference.payload["error"] != "Route not found."
    assert geography.status_code == 404
    assert geography.payload["error"] != "Route not found."
    assert reservations.status_code == 404
    assert reservations.payload["error"] != "Route not found."
    assert action_queue.status_code == 404
    assert action_queue.payload["error"] != "Route not found."

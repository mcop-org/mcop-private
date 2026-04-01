from __future__ import annotations

from app.service.build_runner import _build_status_payload


def test_build_status_payload_includes_product_reference_artifact() -> None:
    payload = _build_status_payload("ready", "ok", "2026-03-07")

    assert payload["artifacts"]["product_reference_intelligence"] == "product_reference_intelligence.json"

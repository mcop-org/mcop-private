from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlparse

from app.service.config import get_service_paths
from app.service.contracts import Response
from app.service.routes_build import handle_get_build_status, handle_run_build
from app.service.routes_datasets import (
    handle_get_contracts,
    handle_get_status,
    handle_load_dataset,
)
from app.service.routes_health import handle_health
from app.service.routes_modules import (
    handle_get_action_queue,
    handle_get_client_geography,
    handle_get_product_reference_intelligence,
    handle_get_reservations,
)

MODULE_GET_ROUTES = {
    "/modules/product-reference-intelligence": handle_get_product_reference_intelligence,
    "/modules/reservations": handle_get_reservations,
    "/modules/action-queue": handle_get_action_queue,
    "/modules/client-geography": handle_get_client_geography,
}


def _json_response(handler: BaseHTTPRequestHandler, response: Response) -> None:
    payload = json.dumps(response.payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    handler.send_response(response.status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(payload)


def _not_found() -> Response:
    return Response(status_code=404, payload={"error": "Route not found."})


def _bad_request(message: str) -> Response:
    return Response(status_code=400, payload={"error": message})


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    parts = [part for part in path.split("/") if part]
    if not parts:
        return "/"
    return "/" + "/".join(parts)


def _dispatch(method: str, path: str, body: dict[str, object] | None) -> Response:
    normalized_path = _normalize_path(path)
    if method == "GET" and normalized_path == "/health":
        return handle_health()
    if method == "GET" and normalized_path == "/datasets/contracts":
        return handle_get_contracts()
    if method == "GET" and normalized_path == "/datasets/status":
        return handle_get_status()
    if method == "POST" and normalized_path == "/datasets/load":
        return handle_load_dataset(body or {})
    if method == "POST" and normalized_path == "/build/run":
        return handle_run_build()
    if method == "GET" and normalized_path == "/build/status":
        return handle_get_build_status()
    if method == "GET" and normalized_path in MODULE_GET_ROUTES:
        return MODULE_GET_ROUTES[normalized_path]()
    return _not_found()


class AppRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:  # noqa: N802
        _json_response(self, Response(status_code=200, payload={"ok": True}))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        response = _dispatch("GET", parsed.path, None)
        _json_response(self, response)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length") or "0")
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            _json_response(self, _bad_request("Invalid JSON body."))
            return
        response = _dispatch("POST", parsed.path, body)
        _json_response(self, response)

    def log_message(self, format: str, *args: object) -> None:
        return


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    get_service_paths()
    server = ThreadingHTTPServer((host, port), AppRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    run_server()

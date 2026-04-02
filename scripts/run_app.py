from __future__ import annotations

import argparse
from collections.abc import Sequence
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_URL = "http://127.0.0.1:8765/health"
FRONTEND_URL = "http://127.0.0.1:5173"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the local MCOP advanced UI backend and frontend together."
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the browser automatically after both services are ready.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for each local service to become ready.",
    )
    return parser.parse_args(argv)


def backend_command(python_executable: str) -> list[str]:
    return [python_executable, "-m", "app.service.app"]


def frontend_command(npm_executable: str) -> list[str]:
    return [npm_executable, "run", "dev:local"]


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def wait_for_url(url: str, timeout_seconds: float, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Process exited before {url} became ready.")
        try:
            with urlopen(url, timeout=1.0) as response:  # noqa: S310
                if 200 <= response.status < 500:
                    return
        except URLError:
            pass
        time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for {url}.")


def terminate_process(process: subprocess.Popen[str], name: str) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    print(f"Stopped {name}.")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    python_executable = sys.executable
    npm_executable = shutil.which("npm")
    if not npm_executable:
        print("Could not find `npm` on PATH.", file=sys.stderr)
        return 1
    if port_in_use("127.0.0.1", 8765):
        print("Port 8765 is already in use. Stop the existing backend or app instance first.", file=sys.stderr)
        return 1
    if port_in_use("127.0.0.1", 5173):
        print("Port 5173 is already in use. Stop the existing frontend or app instance first.", file=sys.stderr)
        return 1

    backend = subprocess.Popen(
        backend_command(python_executable),
        cwd=REPO_ROOT,
        text=True,
        env=os.environ.copy(),
    )
    frontend: subprocess.Popen[str] | None = None

    def shutdown(*_: object) -> None:
        if frontend is not None:
            terminate_process(frontend, "frontend")
        terminate_process(backend, "backend")
        raise SystemExit(0)

    previous_sigint = signal.signal(signal.SIGINT, shutdown)
    previous_sigterm = signal.signal(signal.SIGTERM, shutdown)
    try:
        print("Starting backend on http://127.0.0.1:8765")
        wait_for_url(BACKEND_URL, args.timeout, backend)

        frontend = subprocess.Popen(
            frontend_command(npm_executable),
            cwd=REPO_ROOT / "app/frontend",
            text=True,
            env=os.environ.copy(),
        )
        print("Starting frontend on http://127.0.0.1:5173")
        wait_for_url(FRONTEND_URL, args.timeout, frontend)

        if not args.no_browser:
            webbrowser.open(FRONTEND_URL)

        print("Advanced UI is ready.")
        print("Press Ctrl+C to stop both backend and frontend.")

        while True:
            if backend.poll() is not None:
                raise RuntimeError("Backend exited unexpectedly.")
            if frontend.poll() is not None:
                raise RuntimeError("Frontend exited unexpectedly.")
            time.sleep(0.5)
    except (RuntimeError, TimeoutError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except SystemExit as exit_signal:
        return int(exit_signal.code)
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
        signal.signal(signal.SIGTERM, previous_sigterm)
        if frontend is not None:
            terminate_process(frontend, "frontend")
        terminate_process(backend, "backend")


if __name__ == "__main__":
    raise SystemExit(main())

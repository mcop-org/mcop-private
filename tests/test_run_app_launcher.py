from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch


def load_launcher_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_app.py"
    spec = importlib.util.spec_from_file_location("run_app", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _AliveProcess:
    def poll(self) -> None:
        return None


class _ReadyResponse:
    status = 200

    def __enter__(self) -> "_ReadyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_run_app_commands_use_expected_entrypoints() -> None:
    launcher = load_launcher_module()

    assert launcher.backend_command("/usr/bin/python3") == [
        "/usr/bin/python3",
        "-m",
        "app.service.app",
    ]
    assert launcher.frontend_command("/opt/homebrew/bin/npm") == [
        "/opt/homebrew/bin/npm",
        "run",
        "dev:local",
    ]


def test_run_app_wait_for_url_accepts_ready_response() -> None:
    launcher = load_launcher_module()
    with patch.object(launcher, "urlopen", return_value=_ReadyResponse()):
        launcher.wait_for_url(
            "http://127.0.0.1:9999",
            timeout_seconds=2.0,
            process=_AliveProcess(),
        )


def test_run_app_main_exits_when_expected_port_is_already_in_use() -> None:
    launcher = load_launcher_module()
    with patch.object(launcher, "port_in_use", side_effect=[True]):
        assert launcher.main(["--no-browser"]) == 1

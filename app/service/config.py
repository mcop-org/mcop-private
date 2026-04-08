from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class ServicePaths:
    repo_root: Path
    workspace_root: Path
    runtime_root: Path
    frontend_runtime_dir: Path
    frontend_runtime_index_path: Path
    uploads_dir: Path
    validation_dir: Path
    builds_dir: Path
    readmodels_dir: Path
    build_data_dir: Path
    validation_status_path: Path
    build_status_path: Path


@dataclass(frozen=True)
class GeographyServiceSettings:
    enable_uk_postcode_service: bool
    uk_postcode_service_base_url: str
    uk_postcode_service_timeout_seconds: float
    uk_postcode_service_cache_path: Path


def get_service_paths() -> ServicePaths:
    repo_root = Path(__file__).resolve().parents[2]
    workspace_override = os.environ.get("MCOP_APP_WORKSPACE_ROOT", "").strip()
    workspace_root = (
        Path(workspace_override).resolve()
        if workspace_override
        else repo_root / "app" / "workspace"
    )
    runtime_root = repo_root / "app" / "runtime"
    frontend_runtime_dir = runtime_root / "frontend"
    uploads_dir = workspace_root / "uploads"
    validation_dir = workspace_root / "validation"
    builds_dir = workspace_root / "builds"
    readmodels_dir = workspace_root / "readmodels"
    build_data_dir = builds_dir / "current" / "data"
    validation_status_path = validation_dir / "dataset_status.json"
    build_status_path = builds_dir / "build_status.json"
    for path in (
        uploads_dir,
        validation_dir,
        builds_dir,
        readmodels_dir,
        build_data_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return ServicePaths(
        repo_root=repo_root,
        workspace_root=workspace_root,
        runtime_root=runtime_root,
        frontend_runtime_dir=frontend_runtime_dir,
        frontend_runtime_index_path=frontend_runtime_dir / "index.html",
        uploads_dir=uploads_dir,
        validation_dir=validation_dir,
        builds_dir=builds_dir,
        readmodels_dir=readmodels_dir,
        build_data_dir=build_data_dir,
        validation_status_path=validation_status_path,
        build_status_path=build_status_path,
    )


def get_geography_service_settings() -> GeographyServiceSettings:
    paths = get_service_paths()
    enabled_value = os.environ.get("MCOP_APP_ENABLE_UK_POSTCODE_SERVICE", "").strip().lower()
    enable_uk_postcode_service = enabled_value in {"1", "true", "yes", "on"}
    base_url = os.environ.get("MCOP_APP_UK_POSTCODE_SERVICE_URL", "").strip() or "http://127.0.0.1:8000"
    timeout_raw = os.environ.get("MCOP_APP_UK_POSTCODE_SERVICE_TIMEOUT_SECONDS", "").strip()
    try:
        timeout_seconds = float(timeout_raw) if timeout_raw else 2.0
    except ValueError:
        timeout_seconds = 2.0
    return GeographyServiceSettings(
        enable_uk_postcode_service=enable_uk_postcode_service,
        uk_postcode_service_base_url=base_url,
        uk_postcode_service_timeout_seconds=timeout_seconds,
        uk_postcode_service_cache_path=paths.builds_dir / "client_geography_service_cache.json",
    )

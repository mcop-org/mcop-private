from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class ServicePaths:
    repo_root: Path
    workspace_root: Path
    uploads_dir: Path
    validation_dir: Path
    builds_dir: Path
    readmodels_dir: Path
    build_data_dir: Path
    validation_status_path: Path
    build_status_path: Path


def get_service_paths() -> ServicePaths:
    repo_root = Path(__file__).resolve().parents[2]
    workspace_override = os.environ.get("MCOP_APP_WORKSPACE_ROOT", "").strip()
    workspace_root = (
        Path(workspace_override).resolve()
        if workspace_override
        else repo_root / "app" / "workspace"
    )
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
        uploads_dir=uploads_dir,
        validation_dir=validation_dir,
        builds_dir=builds_dir,
        readmodels_dir=readmodels_dir,
        build_data_dir=build_data_dir,
        validation_status_path=validation_status_path,
        build_status_path=build_status_path,
    )

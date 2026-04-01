from __future__ import annotations

import base64
from pathlib import Path
import shutil

from app.service.config import get_service_paths
from app.service.dataset_registry import DATASET_DEFINITIONS, get_dataset_definition


def _normalise_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def save_uploaded_dataset(dataset_type: str, filename: str, content_base64: str) -> dict[str, object]:
    definition = get_dataset_definition(dataset_type)
    extension = _normalise_extension(filename)
    accepted_extensions = tuple(definition["accepted_extensions"])
    if extension not in accepted_extensions:
        raise ValueError(
            f"Unsupported file extension for {dataset_type}: {extension or '<none>'}"
        )
    raw_bytes = base64.b64decode(content_base64.encode("ascii"))
    paths = get_service_paths()
    target_path = paths.uploads_dir / f"{dataset_type}{extension}"
    target_path.write_bytes(raw_bytes)
    return {
        "dataset_type": dataset_type,
        "filename": target_path.name,
        "path": str(target_path),
    }


def get_uploaded_dataset_path(dataset_type: str) -> Path | None:
    paths = get_service_paths()
    definition = get_dataset_definition(dataset_type)
    for extension in definition["accepted_extensions"]:
        candidate = paths.uploads_dir / f"{dataset_type}{extension}"
        if candidate.exists():
            return candidate
    return None


def prepare_build_data_dir() -> Path:
    paths = get_service_paths()
    if paths.build_data_dir.exists():
        shutil.rmtree(paths.build_data_dir)
    paths.build_data_dir.mkdir(parents=True, exist_ok=True)
    for definition in DATASET_DEFINITIONS:
        dataset_type = str(definition["dataset_type"])
        if dataset_type in {"product_costs_protected", "cash_position"}:
            continue
        source = get_uploaded_dataset_path(dataset_type)
        if source is None:
            continue
        target = paths.build_data_dir / f"{dataset_type}{source.suffix.lower()}"
        shutil.copy2(source, target)

    _ensure_optional_placeholder(paths.build_data_dir, "product_costs_protected.csv", "product_id,bag_size,bags,cost_of_green_coffee_gbp_kg,cost_farm_to_port_gbp_kg,freight_cost_gbp_kg,cost_uk_port_to_warehouse_gbp_kg,initial_payment_pct,remaining_payment_pct,initial_payment_date,remaining_payment_date,harvest_date,landing_date\n")
    _ensure_optional_placeholder(paths.build_data_dir, "cash_position.csv", "date,cash_on_hand\n")
    return paths.build_data_dir


def _ensure_optional_placeholder(build_data_dir: Path, filename: str, contents: str) -> None:
    xlsx_candidate = build_data_dir / filename.replace(".csv", ".xlsx")
    csv_candidate = build_data_dir / filename
    if xlsx_candidate.exists() or csv_candidate.exists():
        return
    csv_candidate.write_text(contents, encoding="utf-8")

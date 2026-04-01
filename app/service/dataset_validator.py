from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from app.readmodels.contracts import write_canonical_json
from app.readmodels.datasets import build_dataset_status_readmodel
from app.service.config import get_service_paths
from app.service.dataset_loader import get_uploaded_dataset_path
from app.service.dataset_registry import DATASET_DEFINITIONS
from mcop.ingest.loaders import _normalise_columns as normalise_loader_columns
from mcop.ingest.normalise import normalise_costs
from mcop.ingest.xero_v1 import load_xero_snapshot


def _read_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        if path.name != "products.csv":
            raise
        return pd.read_csv(path, encoding="cp1252")


def _normalise_frame(dataset_type: str, frame: pd.DataFrame) -> pd.DataFrame:
    if dataset_type == "product_costs_protected":
        return normalise_costs(frame)
    return normalise_loader_columns(frame)


def _read_cash_position_json(path: Path) -> tuple[pd.DataFrame, list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("cash_position JSON root must be an object")
    sidecar = load_xero_snapshot(path)
    return sidecar.finance_cash_position_snapshot.copy(), sorted(str(key) for key in raw.keys())


def _sorted_columns(columns: object) -> list[str]:
    return sorted({str(column).strip().lower() for column in columns if str(column).strip()})


def validate_datasets() -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for definition in DATASET_DEFINITIONS:
        dataset_type = str(definition["dataset_type"])
        path = get_uploaded_dataset_path(dataset_type)
        result: dict[str, object] = {
            "dataset_type": dataset_type,
            "uploaded": path is not None,
            "is_valid": False,
            "filename": path.name if path is not None else "",
            "row_count": 0,
            "column_count": 0,
            "raw_columns": [],
            "recognized_columns": [],
            "missing_columns": [],
            "errors": [],
            "blocking_for_build": bool(definition.get("blocking_for_build")),
            "blocks_build": False,
            "build_blocking_reason": "",
        }
        if path is None:
            if bool(definition.get("blocking_for_build")):
                result["errors"] = ["Dataset not uploaded."]
                result["blocks_build"] = True
                result["build_blocking_reason"] = "Required dataset for the current slice is not uploaded."
            results[dataset_type] = result
            continue
        try:
            raw_columns: list[str]
            if str(path.suffix).lower() == ".json" and dataset_type == "cash_position":
                frame, raw_columns = _read_cash_position_json(path)
            else:
                frame = _read_frame(path)
                raw_columns = _sorted_columns(frame.columns)
            frame = _normalise_frame(dataset_type, frame)
            frame.columns = [str(column).strip().lower() for column in frame.columns]
            required_columns = [str(column).strip().lower() for column in definition["required_columns"]]
            missing_columns = sorted(
                [column for column in required_columns if column not in set(frame.columns)]
            )
            result["row_count"] = int(len(frame.index))
            result["column_count"] = int(len(frame.columns))
            result["raw_columns"] = raw_columns
            result["recognized_columns"] = _sorted_columns(frame.columns)
            result["missing_columns"] = missing_columns
            result["is_valid"] = len(missing_columns) == 0
            if missing_columns:
                result["errors"] = [
                    "Missing normalized required columns: " + ", ".join(missing_columns)
                ]
            if bool(definition.get("blocking_for_build")) and not bool(result["is_valid"]):
                result["blocks_build"] = True
                result["build_blocking_reason"] = (
                    "Required dataset for the current slice is invalid."
                )
        except Exception as exc:
            result["errors"] = [str(exc)]
            if bool(definition.get("blocking_for_build")):
                result["blocks_build"] = True
                result["build_blocking_reason"] = (
                    "Required dataset for the current slice could not be validated."
                )
        results[dataset_type] = result
    return results


def persist_dataset_status() -> dict[str, object]:
    paths = get_service_paths()
    validations = validate_datasets()
    payload = build_dataset_status_readmodel(DATASET_DEFINITIONS, validations)
    write_canonical_json(paths.validation_status_path, payload)
    return payload


def load_dataset_status() -> dict[str, object]:
    paths = get_service_paths()
    if not paths.validation_status_path.exists():
        return persist_dataset_status()
    return json.loads(paths.validation_status_path.read_text(encoding="utf-8"))

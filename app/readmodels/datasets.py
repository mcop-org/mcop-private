from __future__ import annotations

from collections.abc import Iterable


def build_dataset_contracts_readmodel(dataset_definitions: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = []
    for definition in dataset_definitions:
        rows.append(
            {
                "dataset_type": definition["dataset_type"],
                "label": definition["label"],
                "description": definition["description"],
                "required": bool(definition["required"]),
                "blocking_for_build": bool(definition.get("blocking_for_build")),
                "accepted_extensions": list(definition["accepted_extensions"]),
                "required_columns": list(definition["required_columns"]),
            }
        )
    rows.sort(key=lambda row: row["dataset_type"])
    return {"datasets": rows}


def build_dataset_status_readmodel(
    dataset_definitions: Iterable[dict[str, object]],
    validations: dict[str, dict[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    build_ready = True
    for definition in dataset_definitions:
        dataset_type = str(definition["dataset_type"])
        validation = validations.get(dataset_type, {})
        is_ready = bool(validation.get("is_valid"))
        if bool(validation.get("blocks_build")):
            build_ready = False
        rows.append(
            {
                "dataset_type": dataset_type,
                "label": definition["label"],
                "required": bool(definition["required"]),
                "blocking_for_build": bool(validation.get("blocking_for_build", definition.get("blocking_for_build"))),
                "blocks_build": bool(validation.get("blocks_build")),
                "uploaded": bool(validation.get("uploaded")),
                "is_valid": bool(validation.get("is_valid")),
                "filename": str(validation.get("filename") or ""),
                "row_count": int(validation.get("row_count") or 0),
                "column_count": int(validation.get("column_count") or 0),
                "raw_columns": list(validation.get("raw_columns") or []),
                "recognized_columns": list(validation.get("recognized_columns") or []),
                "missing_columns": list(validation.get("missing_columns") or []),
                "errors": list(validation.get("errors") or []),
                "build_blocking_reason": str(validation.get("build_blocking_reason") or ""),
            }
        )
    rows.sort(key=lambda row: row["dataset_type"])
    return {"build_ready": build_ready, "datasets": rows}

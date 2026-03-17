from dataclasses import dataclass
from pathlib import Path
import math
import re

import pandas as pd

from mcop.ingest.xero_v1 import XeroSidecar, load_xero_snapshot


DATE_COLUMNS_BY_INPUT = {
    "products": ("landing_date",),
    "costs": (
        "harvest_date",
        "landing_date",
        "initial_payment_date",
        "remaining_payment_date",
    ),
    "cash_position": ("date",),
    "activity": (
        "request_date",
        "approval_date",
        "amendment_date",
        "dispatch_date",
        "landing_date",
    ),
}

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DAY_FIRST_DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")
NULL_DATE_SENTINELS = {"pending"}


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        if path.name != "products.csv":
            raise
        return pd.read_csv(path, encoding="cp1252")


def _read_xlsx(path: Path) -> pd.DataFrame:
    return pd.read_excel(path)


def _resolve_input_path(data_dir: Path, logical_name: str) -> Path:
    xlsx_path = data_dir / f"{logical_name}.xlsx"
    if xlsx_path.exists():
        return xlsx_path

    csv_path = data_dir / f"{logical_name}.csv"
    return csv_path


def _read_input(data_dir: Path, logical_name: str) -> tuple[pd.DataFrame, str]:
    path = _resolve_input_path(data_dir, logical_name)
    if path.suffix.lower() == ".xlsx":
        return _read_xlsx(path), "xlsx"
    return _read_csv(path), "csv"


def _normalise_date_value(value, column_name: str, source_type: str):
    if value is None or pd.isna(value):
        return pd.NA

    if isinstance(value, pd.Timestamp):
        return value.normalize().date().isoformat()

    if source_type == "xlsx" and isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isfinite(float(value)):
            parsed = pd.to_datetime(value, unit="D", origin="1899-12-30")
            return parsed.normalize().date().isoformat()

    text = str(value).strip()
    if not text:
        return pd.NA
    if text.lower() in NULL_DATE_SENTINELS:
        return pd.NA

    if ISO_DATE_PATTERN.match(text):
        parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="raise")
        return parsed.date().isoformat()

    if DAY_FIRST_DATE_PATTERN.match(text):
        parsed = pd.to_datetime(text, format="%d/%m/%Y", errors="raise")
        return parsed.date().isoformat()

    raise ValueError(f"Unsupported date format in column '{column_name}': {text}")


def _normalise_dates(df: pd.DataFrame, date_columns: tuple[str, ...], source_type: str) -> pd.DataFrame:
    out = df.copy()
    for column in date_columns:
        if column not in out.columns:
            continue
        out[column] = out[column].apply(
            lambda value: _normalise_date_value(value, column, source_type)
        )
    return out


def _normalise_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    aliases = {
        "bag_size": "bag_size_kg",
        "bag_sizekg": "bag_size_kg",
        "price_gbp_kg": "price_per_kg",
        "price_per_kg ": "price_per_kg",
        "price ¬£/kg": "price_per_kg",
        "price /kg": "price_per_kg",
        "product id": "product_id",
        "product reference": "product_reference",
        "landing status": "landing_status",
        "landing date": "landing_date",
    }

    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
    if "product_id" in df.columns:
        df["product_id"] = df["product_id"].astype(str).str.strip()
    if "bags_available" in df.columns and "bags_remaining" not in df.columns:
        df["bags_remaining"] = df["bags_available"]
    return df


@dataclass(frozen=True)
class Inputs:
    products: pd.DataFrame
    costs: pd.DataFrame
    cash_position: pd.DataFrame
    activity: pd.DataFrame
    xero_sidecar: XeroSidecar | None


def load_inputs(data_dir: Path, xero_snapshot_path: Path | None = None) -> Inputs:
    products_df, products_source = _read_input(data_dir, "products")
    costs_df, costs_source = _read_input(data_dir, "product_costs_protected")
    cash_df, cash_source = _read_input(data_dir, "cash_position")
    activity_df, activity_source = _read_input(data_dir, "activity")
    xero_sidecar = None
    if xero_snapshot_path is not None and xero_snapshot_path.exists():
        xero_sidecar = load_xero_snapshot(xero_snapshot_path)

    return Inputs(
        products=_normalise_dates(
            _normalise_columns(products_df),
            DATE_COLUMNS_BY_INPUT["products"],
            products_source,
        ),
        costs=_normalise_dates(
            _normalise_columns(costs_df),
            DATE_COLUMNS_BY_INPUT["costs"],
            costs_source,
        ),
        cash_position=_normalise_dates(
            _normalise_columns(cash_df),
            DATE_COLUMNS_BY_INPUT["cash_position"],
            cash_source,
        ),
        activity=_normalise_dates(
            _normalise_columns(activity_df),
            DATE_COLUMNS_BY_INPUT["activity"],
            activity_source,
        ),
        xero_sidecar=xero_sidecar,
    )

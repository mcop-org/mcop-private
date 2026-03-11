from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from mcop.ingest.normalise import normalise_activity, normalise_products, normalise_costs


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        if path.name != "products.csv":
            raise
        return pd.read_csv(path, encoding="cp1252")


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

def load_inputs(data_dir: Path) -> Inputs:
    return Inputs(
        products=_normalise_columns(_read_csv(data_dir / "products.csv")),
        costs=_normalise_columns(_read_csv(data_dir / "product_costs_protected.csv")),
        cash_position=_normalise_columns(_read_csv(data_dir / "cash_position.csv")),
        activity=_normalise_columns(_read_csv(data_dir / "activity.csv")),
    )

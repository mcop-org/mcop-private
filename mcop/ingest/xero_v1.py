from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd


REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "snapshot_date",
    "source_system",
    "organisation",
    "receivables",
    "payables",
    "bank_balances",
}
REQUIRED_ORGANISATION_KEYS = {"tenant_id", "organisation_name", "base_currency"}
REQUIRED_RECEIVABLE_KEYS = {
    "invoice_id",
    "invoice_number",
    "contact_id",
    "contact_name",
    "status",
    "currency_code",
    "invoice_date",
    "due_date",
    "amount_total",
    "amount_paid",
    "amount_credited",
    "amount_due",
    "updated_date",
}
REQUIRED_PAYABLE_KEYS = {
    "bill_id",
    "bill_number",
    "contact_id",
    "contact_name",
    "status",
    "currency_code",
    "invoice_date",
    "due_date",
    "amount_total",
    "amount_paid",
    "amount_credited",
    "amount_due",
    "updated_date",
}
REQUIRED_BANK_BALANCE_KEYS = {
    "account_id",
    "account_code",
    "account_name",
    "account_type",
    "currency_code",
    "balance",
}
REQUIRED_DATE_FIELDS = {
    "snapshot_date",
    "invoice_date",
    "due_date",
    "updated_date",
}
REQUIRED_MONEY_FIELDS = {
    "amount_total",
    "amount_paid",
    "amount_credited",
    "amount_due",
    "balance",
}
EXPECTED_SCHEMA_VERSION = "xero_snapshot_v1"
EXPECTED_SOURCE_SYSTEM = "xero"


@dataclass(frozen=True)
class XeroSidecar:
    organisation: dict
    xero_receivables_open: pd.DataFrame
    xero_payables_open: pd.DataFrame
    xero_bank_balances: pd.DataFrame
    finance_receivable_events: pd.DataFrame
    finance_payable_events: pd.DataFrame
    finance_cash_position_snapshot: pd.DataFrame
    currency_warning: str | None


def _require_keys(obj: dict, required: set[str], label: str) -> None:
    missing = required - set(obj.keys())
    if missing:
        raise ValueError(f"{label} missing keys: {sorted(missing)}")


def _require_iso_date(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty ISO date")
    parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"{label} must be ISO YYYY-MM-DD: {text}")
    return parsed.date().isoformat()


def _require_numeric(value: object, label: str) -> float:
    parsed = pd.to_numeric([value], errors="coerce")[0]
    if pd.isna(parsed):
        raise ValueError(f"{label} must be numeric")
    return float(parsed)


def _validate_line_items(rows: object, required: set[str], label: str) -> list[dict]:
    if not isinstance(rows, list):
        raise ValueError(f"{label} must be a list")

    normalised_rows: list[dict] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label}[{index}] must be an object")
        _require_keys(row, required, f"{label}[{index}]")

        clean = dict(row)
        for key in sorted(REQUIRED_DATE_FIELDS & required):
            clean[key] = _require_iso_date(clean[key], f"{label}[{index}].{key}")
        for key in sorted(REQUIRED_MONEY_FIELDS & required):
            clean[key] = _require_numeric(clean[key], f"{label}[{index}].{key}")
        normalised_rows.append(clean)
    return normalised_rows


def _sum_by_currency(df: pd.DataFrame, amount_col: str) -> list[dict]:
    if df.empty:
        return []

    grouped = (
        df.assign(currency_code=df["currency_code"].astype(str).str.strip().str.upper())
        .groupby("currency_code", as_index=False)[amount_col]
        .sum()
        .sort_values(["currency_code"], kind="stable")
    )
    return [
        {"currency_code": row["currency_code"], "amount": round(float(row[amount_col]), 2)}
        for _, row in grouped.iterrows()
    ]


def _build_open_documents(
    rows: list[dict],
    *,
    dataset_name: str,
    id_field: str,
    number_field: str,
) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "source_system",
                "tenant_id",
                "as_of_date",
                id_field,
                number_field,
                "contact_id",
                "contact_name",
                "status",
                "currency_code",
                "invoice_date",
                "due_date",
                "amount_total",
                "amount_paid",
                "amount_credited",
                "amount_due",
                "updated_date",
            ]
        )

    out = frame.copy()
    out["currency_code"] = out["currency_code"].astype(str).str.strip().str.upper()
    out = out.sort_values([number_field, id_field], kind="stable").reset_index(drop=True)
    return out


def _build_event_frame(
    rows: pd.DataFrame,
    *,
    id_field: str,
    number_field: str,
    event_type: str,
) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "amount",
                "event_type",
                "source_id",
                "source_doc_no",
                "counterparty_name",
                "source_system",
                "currency_code",
            ]
        )

    out = pd.DataFrame(
        {
            "date": rows["due_date"],
            "amount": rows["amount_due"],
            "event_type": event_type,
            "source_id": rows[id_field],
            "source_doc_no": rows[number_field],
            "counterparty_name": rows["contact_name"],
            "source_system": rows["source_system"],
            "currency_code": rows["currency_code"],
        }
    )
    out = out[out["amount"] > 0].copy()
    return out.sort_values(["date", "source_doc_no", "source_id"], kind="stable").reset_index(drop=True)


def _build_cash_snapshot(bank_balances: pd.DataFrame, snapshot_date: str) -> tuple[pd.DataFrame, str | None]:
    if bank_balances.empty:
        return pd.DataFrame(columns=["date", "cash_on_hand", "source_system", "currency_code"]), None

    currencies = sorted({str(v).strip().upper() for v in bank_balances["currency_code"].tolist()})
    if currencies == ["GBP"]:
        total_cash = round(float(bank_balances["balance"].sum()), 2)
        return (
            pd.DataFrame(
                [
                    {
                        "date": snapshot_date,
                        "cash_on_hand": total_cash,
                        "source_system": "xero",
                        "currency_code": "GBP",
                    }
                ]
            ),
            None,
        )

    warning = (
        "Mixed/non-GBP Xero values detected; totals shown by native currency only and not "
        "comparable to legacy GBP liquidity figures."
    )
    return pd.DataFrame(columns=["date", "cash_on_hand", "source_system", "currency_code"]), warning


def load_xero_snapshot(path: Path) -> XeroSidecar:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("xero_snapshot_v1 root must be an object")

    _require_keys(raw, REQUIRED_TOP_LEVEL_KEYS, "xero_snapshot_v1")
    if raw["schema_version"] != EXPECTED_SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version: {raw['schema_version']}")
    if raw["source_system"] != EXPECTED_SOURCE_SYSTEM:
        raise ValueError(f"Unsupported source_system: {raw['source_system']}")

    snapshot_date = _require_iso_date(raw["snapshot_date"], "snapshot_date")

    organisation = raw["organisation"]
    if not isinstance(organisation, dict):
        raise ValueError("organisation must be an object")
    _require_keys(organisation, REQUIRED_ORGANISATION_KEYS, "organisation")
    organisation_out = {
        "tenant_id": str(organisation["tenant_id"]).strip(),
        "organisation_name": str(organisation["organisation_name"]).strip(),
        "base_currency": str(organisation["base_currency"]).strip().upper(),
        "source_system": EXPECTED_SOURCE_SYSTEM,
        "snapshot_date": snapshot_date,
    }

    receivables = _validate_line_items(raw["receivables"], REQUIRED_RECEIVABLE_KEYS, "receivables")
    payables = _validate_line_items(raw["payables"], REQUIRED_PAYABLE_KEYS, "payables")
    bank_balances = _validate_line_items(raw["bank_balances"], REQUIRED_BANK_BALANCE_KEYS, "bank_balances")

    receivables_frame = _build_open_documents(
        receivables,
        dataset_name="xero_receivables_open",
        id_field="invoice_id",
        number_field="invoice_number",
    )
    if not receivables_frame.empty:
        receivables_frame.insert(0, "source_system", EXPECTED_SOURCE_SYSTEM)
        receivables_frame.insert(1, "tenant_id", organisation_out["tenant_id"])
        receivables_frame.insert(2, "as_of_date", snapshot_date)

    payables_frame = _build_open_documents(
        payables,
        dataset_name="xero_payables_open",
        id_field="bill_id",
        number_field="bill_number",
    )
    if not payables_frame.empty:
        payables_frame.insert(0, "source_system", EXPECTED_SOURCE_SYSTEM)
        payables_frame.insert(1, "tenant_id", organisation_out["tenant_id"])
        payables_frame.insert(2, "as_of_date", snapshot_date)

    bank_frame = pd.DataFrame(bank_balances)
    if bank_frame.empty:
        bank_frame = pd.DataFrame(
            columns=[
                "source_system",
                "tenant_id",
                "as_of_date",
                "account_id",
                "account_code",
                "account_name",
                "account_type",
                "currency_code",
                "balance",
            ]
        )
    else:
        bank_frame["currency_code"] = bank_frame["currency_code"].astype(str).str.strip().str.upper()
        bank_frame.insert(0, "source_system", EXPECTED_SOURCE_SYSTEM)
        bank_frame.insert(1, "tenant_id", organisation_out["tenant_id"])
        bank_frame.insert(2, "as_of_date", snapshot_date)
        bank_frame = bank_frame.sort_values(["account_code", "account_id"], kind="stable").reset_index(drop=True)

    finance_receivable_events = _build_event_frame(
        receivables_frame,
        id_field="invoice_id",
        number_field="invoice_number",
        event_type="xero_receivable_due",
    )
    finance_payable_events = _build_event_frame(
        payables_frame,
        id_field="bill_id",
        number_field="bill_number",
        event_type="xero_payable_due",
    )
    finance_cash_position_snapshot, currency_warning = _build_cash_snapshot(bank_frame, snapshot_date)

    if currency_warning is None:
        doc_currencies = {
            str(v).strip().upper()
            for frame in (receivables_frame, payables_frame)
            for v in (frame["currency_code"].tolist() if not frame.empty else [])
        }
        if any(currency != "GBP" for currency in sorted(doc_currencies)):
            currency_warning = (
                "Mixed/non-GBP Xero values detected; totals shown by native currency only and not "
                "comparable to legacy GBP liquidity figures."
            )

    return XeroSidecar(
        organisation=organisation_out,
        xero_receivables_open=receivables_frame,
        xero_payables_open=payables_frame,
        xero_bank_balances=bank_frame,
        finance_receivable_events=finance_receivable_events,
        finance_payable_events=finance_payable_events,
        finance_cash_position_snapshot=finance_cash_position_snapshot,
        currency_warning=currency_warning,
    )


def build_xero_reporting_payload(
    sidecar: XeroSidecar,
    *,
    legacy_cash_on_hand: float | None,
    legacy_receivables_60: float | None,
    legacy_payables_60: float | None,
) -> dict:
    receivables = sidecar.xero_receivables_open
    payables = sidecar.xero_payables_open
    bank_balances = sidecar.xero_bank_balances

    def _top_rows(rows: pd.DataFrame, id_field: str, number_field: str) -> list[dict]:
        if rows.empty:
            return []
        ordered = rows.sort_values(["due_date", "amount_due", number_field], ascending=[True, False, True], kind="stable")
        out: list[dict] = []
        for _, row in ordered.head(5).iterrows():
            out.append(
                {
                    "source_id": row[id_field],
                    "source_doc_no": row[number_field],
                    "counterparty_name": row["contact_name"],
                    "due_date": row["due_date"],
                    "amount_due": round(float(row["amount_due"]), 2),
                    "currency_code": row["currency_code"],
                }
            )
        return out

    comparisons: list[str] = []
    if sidecar.currency_warning is None and not sidecar.finance_cash_position_snapshot.empty:
        xero_cash = float(sidecar.finance_cash_position_snapshot.iloc[0]["cash_on_hand"])
        comparisons.append(f"Legacy cash on hand: £{float(legacy_cash_on_hand or 0.0):,.2f} vs Xero bank total: £{xero_cash:,.2f}")
        comparisons.append(
            f"Legacy receivables (60d): £{float(legacy_receivables_60 or 0.0):,.2f} vs Xero open receivables: £{float(receivables['amount_due'].sum() if not receivables.empty else 0.0):,.2f}"
        )
        comparisons.append(
            f"Legacy payables (60d): £{float(legacy_payables_60 or 0.0):,.2f} vs Xero open payables: £{float(payables['amount_due'].sum() if not payables.empty else 0.0):,.2f}"
        )

    return {
        "available": True,
        "snapshot_date": sidecar.organisation["snapshot_date"],
        "organisation_name": sidecar.organisation["organisation_name"],
        "tenant_id": sidecar.organisation["tenant_id"],
        "base_currency": sidecar.organisation["base_currency"],
        "currency_warning": sidecar.currency_warning,
        "bank_totals_by_currency": _sum_by_currency(bank_balances, "balance"),
        "receivables_totals_by_currency": _sum_by_currency(receivables, "amount_due"),
        "payables_totals_by_currency": _sum_by_currency(payables, "amount_due"),
        "top_receivables": _top_rows(receivables, "invoice_id", "invoice_number"),
        "top_payables": _top_rows(payables, "bill_id", "bill_number"),
        "comparison_lines": comparisons,
    }

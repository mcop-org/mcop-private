import json
from pathlib import Path

import pytest

from mcop.ingest.xero_v1 import build_xero_reporting_payload, load_xero_snapshot


def _write_snapshot(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_xero_snapshot_normalises_open_documents_and_events(tmp_path: Path) -> None:
    snapshot = {
        "schema_version": "xero_snapshot_v1",
        "snapshot_date": "2026-03-17",
        "source_system": "xero",
        "organisation": {
            "tenant_id": "tenant-1",
            "organisation_name": "Example Ltd",
            "base_currency": "GBP",
        },
        "receivables": [
            {
                "invoice_id": "inv-2",
                "invoice_number": "INV-2",
                "contact_id": "contact-2",
                "contact_name": "Customer B",
                "status": "AUTHORISED",
                "currency_code": "GBP",
                "invoice_date": "2026-03-02",
                "due_date": "2026-04-05",
                "amount_total": 400.0,
                "amount_paid": 0.0,
                "amount_credited": 0.0,
                "amount_due": 400.0,
                "updated_date": "2026-03-17",
            },
            {
                "invoice_id": "inv-1",
                "invoice_number": "INV-1",
                "contact_id": "contact-1",
                "contact_name": "Customer A",
                "status": "AUTHORISED",
                "currency_code": "GBP",
                "invoice_date": "2026-03-01",
                "due_date": "2026-03-31",
                "amount_total": 1000.0,
                "amount_paid": 200.0,
                "amount_credited": 0.0,
                "amount_due": 800.0,
                "updated_date": "2026-03-17",
            },
        ],
        "payables": [
            {
                "bill_id": "bill-1",
                "bill_number": "BILL-1",
                "contact_id": "supplier-1",
                "contact_name": "Supplier A",
                "status": "AUTHORISED",
                "currency_code": "GBP",
                "invoice_date": "2026-03-03",
                "due_date": "2026-03-25",
                "amount_total": 500.0,
                "amount_paid": 0.0,
                "amount_credited": 0.0,
                "amount_due": 500.0,
                "updated_date": "2026-03-17",
            }
        ],
        "bank_balances": [
            {
                "account_id": "bank-1",
                "account_code": "090",
                "account_name": "Main Bank",
                "account_type": "BANK",
                "currency_code": "GBP",
                "balance": 25000.0,
            }
        ],
    }

    sidecar = load_xero_snapshot(_write_snapshot(tmp_path / "xero_snapshot_v1.json", snapshot))

    assert list(sidecar.xero_receivables_open["invoice_number"]) == ["INV-1", "INV-2"]
    assert list(sidecar.finance_receivable_events["source_doc_no"]) == ["INV-1", "INV-2"]
    assert list(sidecar.finance_receivable_events["date"]) == ["2026-03-31", "2026-04-05"]
    assert list(sidecar.finance_payable_events["amount"]) == [500.0]
    assert list(sidecar.finance_cash_position_snapshot["cash_on_hand"]) == [25000.0]
    assert sidecar.currency_warning is None

    report = build_xero_reporting_payload(
        sidecar,
        legacy_cash_on_hand=1500.0,
        legacy_receivables_60=800.0,
        legacy_payables_60=500.0,
    )

    assert report["bank_totals_by_currency"] == [{"currency_code": "GBP", "amount": 25000.0}]
    assert report["receivables_totals_by_currency"] == [{"currency_code": "GBP", "amount": 1200.0}]
    assert report["payables_totals_by_currency"] == [{"currency_code": "GBP", "amount": 500.0}]
    assert len(report["comparison_lines"]) == 3


def test_load_xero_snapshot_rejects_invalid_schema_version(tmp_path: Path) -> None:
    snapshot = {
        "schema_version": "wrong_version",
        "snapshot_date": "2026-03-17",
        "source_system": "xero",
        "organisation": {
            "tenant_id": "tenant-1",
            "organisation_name": "Example Ltd",
            "base_currency": "GBP",
        },
        "receivables": [],
        "payables": [],
        "bank_balances": [],
    }

    with pytest.raises(ValueError, match="Unsupported schema_version"):
        load_xero_snapshot(_write_snapshot(tmp_path / "xero_snapshot_v1.json", snapshot))


def test_load_xero_snapshot_surfaces_mixed_currency_ambiguity(tmp_path: Path) -> None:
    snapshot = {
        "schema_version": "xero_snapshot_v1",
        "snapshot_date": "2026-03-17",
        "source_system": "xero",
        "organisation": {
            "tenant_id": "tenant-1",
            "organisation_name": "Example Ltd",
            "base_currency": "GBP",
        },
        "receivables": [],
        "payables": [],
        "bank_balances": [
            {
                "account_id": "bank-1",
                "account_code": "090",
                "account_name": "Main Bank",
                "account_type": "BANK",
                "currency_code": "GBP",
                "balance": 25000.0,
            },
            {
                "account_id": "bank-2",
                "account_code": "091",
                "account_name": "USD Bank",
                "account_type": "BANK",
                "currency_code": "USD",
                "balance": 1000.0,
            },
        ],
    }

    sidecar = load_xero_snapshot(_write_snapshot(tmp_path / "xero_snapshot_v1.json", snapshot))

    assert sidecar.finance_cash_position_snapshot.empty
    assert sidecar.currency_warning is not None

    report = build_xero_reporting_payload(
        sidecar,
        legacy_cash_on_hand=1500.0,
        legacy_receivables_60=0.0,
        legacy_payables_60=0.0,
    )

    assert report["comparison_lines"] == []
    assert report["bank_totals_by_currency"] == [
        {"currency_code": "GBP", "amount": 25000.0},
        {"currency_code": "USD", "amount": 1000.0},
    ]

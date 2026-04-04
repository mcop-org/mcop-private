from __future__ import annotations

import subprocess

from app.service.app import _dispatch
from app.service.outlook_drafts import (
    DraftExportBlockedError,
    OutlookDraftExportError,
    _build_plaintext_body,
    _outlook_applescript,
    _run_outlook_draft_export,
    export_action_queue_outlook_draft,
)
from app.service.routes_outlook_drafts import handle_export_outlook_draft


def test_outlook_draft_export_uses_current_action_queue_draft(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "app.service.outlook_drafts.load_readmodel",
        lambda name: {
            "expired_draft_workflow": {
                "drafts": [
                    {
                        "draft_key": "::alpha::444|436",
                        "subject": "Legacy company subject",
                        "email_subject": "Reservation reminder - Reservations 444 and 436 expired",
                        "body_intro": "Legacy intro",
                        "email_body_intro": "Hi Alpha,\n\nWe are writing to remind you that the reservation(s) below are now past their expiry date.",
                        "body_closing": "Legacy closing",
                        "email_body_closing": "Please review the reservations above.\n\nKind regards,\nMi Cafe Trading Co.",
                        "email_body_table_rows": [
                            {
                                "reservation": "444",
                                "reference": "REF-1",
                                "bags_remaining": 3,
                                "expired_on": "2026-03-08",
                                "days_expired": 4,
                                "kg_remaining": 60,
                                "value": 720,
                            },
                            {
                                "reservation": "436",
                                "reference": "REF-2",
                                "bags_remaining": 1,
                                "expired_on": "2026-03-09",
                                "days_expired": 3,
                                "kg_remaining": 20,
                                "value": None,
                            },
                        ],
                        "to_emails": ["alpha@test.example"],
                        "cc_emails": ["ops@test.example"],
                        "can_export": True,
                        "export_block_reason": "",
                    }
                ]
            }
        },
    )

    def fake_run(subject: str, body: str, to_emails: list[str], cc_emails: list[str]) -> None:
        captured["subject"] = subject
        captured["body"] = body
        captured["to_emails"] = to_emails
        captured["cc_emails"] = cc_emails

    monkeypatch.setattr("app.service.outlook_drafts._run_outlook_draft_export", fake_run)

    payload = export_action_queue_outlook_draft("::alpha::444|436")

    assert payload == {
        "draft_key": "::alpha::444|436",
        "exported": True,
        "status": "Exported to Outlook draft",
        "subject": "Reservation reminder - Reservations 444 and 436 expired",
    }
    assert captured["subject"] == "Reservation reminder - Reservations 444 and 436 expired"
    assert captured["to_emails"] == ["alpha@test.example"]
    assert captured["cc_emails"] == ["ops@test.example"]
    assert "<table" in str(captured["body"])
    assert "<th" in str(captured["body"])
    assert "Reservations requiring review" in str(captured["body"])
    assert ">444</td>" in str(captured["body"])
    assert ">REF-1</td>" in str(captured["body"])


def test_outlook_draft_export_blocks_missing_primary_recipient(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.service.outlook_drafts.load_readmodel",
        lambda name: {
            "expired_draft_workflow": {
                "drafts": [
                    {
                        "draft_key": "::bravo::421",
                        "subject": "Reservation reminder - Reservation 421 expired",
                        "body_intro": "Hi Bravo,",
                        "body_closing": "Kind regards,\nMi Cafe Trading Co.",
                        "body_table_rows": [],
                        "to_emails": [],
                        "cc_emails": [],
                        "can_export": False,
                        "export_block_reason": "Primary recipient email missing. Draft is review-only and cannot be exported.",
                    }
                ]
            }
        },
    )

    try:
        export_action_queue_outlook_draft("::bravo::421")
    except DraftExportBlockedError as exc:
        assert str(exc) == "Primary recipient email missing. Draft is review-only and cannot be exported."
    else:
        raise AssertionError("Expected missing-recipient export to be blocked.")


def test_outlook_draft_plaintext_body_formats_table_rows() -> None:
    body = _build_plaintext_body(
        {
            "email_body_intro": "Hi Alpha,\n\nWe are writing to remind you that the reservation(s) below are now past their expiry date.",
            "email_body_closing": "Please review the reservations above and let us know how you would like to proceed with release planning.\n\nKind regards,\nMi Cafe Trading Co.",
            "email_body_table_rows": [
                {
                    "reservation": "444",
                    "reference": "REF-1",
                    "bags_remaining": 3,
                    "expired_on": "2026-03-08",
                    "days_expired": 4,
                    "kg_remaining": 60,
                    "value": 720,
                }
            ],
        }
    )

    assert "<html>" in body
    assert "<table" in body
    assert "Reservations requiring review" in body
    assert ">Reservation</th>" in body
    assert ">Reference</th>" in body
    assert ">Bags Remaining</th>" in body
    assert ">444</td>" in body
    assert ">REF-1</td>" in body
    assert ">£720.00</td>" in body
    assert (
        body.count(
            "Please review the reservations above and let us know how you would like to proceed with release planning."
        )
        == 1
    )
    assert "Kind regards," in body


def test_outlook_draft_body_formats_money_with_pound_commas_and_two_decimals() -> None:
    body = _build_plaintext_body(
        {
            "email_body_intro": "Hi Alpha,",
            "email_body_closing": "Kind regards,\nMi Cafe Trading Co.",
            "email_body_table_rows": [
                {
                    "reservation": "275",
                    "reference": "REF-1",
                    "bags_remaining": 3,
                    "expired_on": "2026-03-08",
                    "days_expired": 4,
                    "kg_remaining": 60,
                    "value": 3131.1,
                },
                {
                    "reservation": "276",
                    "reference": "REF-2",
                    "bags_remaining": 2,
                    "expired_on": "2026-03-09",
                    "days_expired": 3,
                    "kg_remaining": 40,
                    "value": 1260,
                },
            ],
        }
    )

    assert ">£3,131.10</td>" in body
    assert ">£1,260.00</td>" in body


def test_outlook_subject_deduplicates_repeated_reservation_numbers(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "app.service.outlook_drafts.load_readmodel",
        lambda name: {
            "expired_draft_workflow": {
                "drafts": [
                    {
                        "draft_key": "::alpha::449",
                        "email_body_table_rows": [
                            {"reservation": "449", "reference": "REF-1"},
                            {"reservation": "449", "reference": "REF-2"},
                        ],
                        "to_emails": ["alpha@test.example"],
                    }
                ]
            }
        },
    )

    monkeypatch.setattr(
        "app.service.outlook_drafts._run_outlook_draft_export",
        lambda subject, body, to_emails, cc_emails: captured.update({"subject": subject}),
    )

    payload = export_action_queue_outlook_draft("::alpha::449")

    assert payload["subject"] == "Reservation reminder - Reservation 449 expired"
    assert captured["subject"] == "Reservation reminder - Reservation 449 expired"


def test_outlook_subject_ignores_stale_explicit_subject_and_uses_unique_reservations(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "app.service.outlook_drafts.load_readmodel",
        lambda name: {
            "expired_draft_workflow": {
                "drafts": [
                    {
                        "draft_key": "::alpha::275|276",
                        "email_subject": "Reservation reminder - 4 expired reservations",
                        "email_body_table_rows": [
                            {"reservation": "275", "reference": "REF-1"},
                            {"reservation": "275", "reference": "REF-2"},
                            {"reservation": "276", "reference": "REF-3"},
                            {"reservation": "276", "reference": "REF-4"},
                        ],
                        "to_emails": ["alpha@test.example"],
                    }
                ]
            }
        },
    )

    monkeypatch.setattr(
        "app.service.outlook_drafts._run_outlook_draft_export",
        lambda subject, body, to_emails, cc_emails: captured.update({"subject": subject}),
    )

    payload = export_action_queue_outlook_draft("::alpha::275|276")

    assert payload["subject"] == "Reservation reminder - Reservations 275 and 276 expired"
    assert captured["subject"] == "Reservation reminder - Reservations 275 and 276 expired"


def test_outlook_applescript_creates_messages_in_drafts_folder() -> None:
    script = _outlook_applescript()

    assert "normalizedRecipientAddresses" in script
    assert "normalizeComparisonText" in script
    assert "make new outgoing message with properties" in script
    assert "make new recipient at newMessage" in script
    assert "open newMessage" in script
    assert "Outlook draft recipients did not match the reviewed draft." in script
    assert 'return "persisted"' in script


def test_run_outlook_draft_export_requires_creation_confirmation(monkeypatch) -> None:
    monkeypatch.setattr("app.service.outlook_drafts.sys.platform", "darwin")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="not-created\n", stderr="")

    monkeypatch.setattr("app.service.outlook_drafts.subprocess.run", fake_run)

    try:
        _run_outlook_draft_export("Subject", "Body", ["alpha@test.example"], [])
    except OutlookDraftExportError as exc:
        assert str(exc) == "Outlook draft export did not confirm persisted draft creation."
    else:
        raise AssertionError("Expected missing creation confirmation to fail export.")


def test_outlook_draft_export_allows_visible_to_recipient_even_if_stale_flag_says_missing(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "app.service.outlook_drafts.load_readmodel",
        lambda name: {
            "expired_draft_workflow": {
                "drafts": [
                    {
                        "draft_key": "::alpha::444",
                        "to_emails": ["company_18@mail.com"],
                        "missing_primary_email": True,
                        "line_items": [{"reservation_key": "444"}],
                    }
                ]
            }
        },
    )

    monkeypatch.setattr(
        "app.service.outlook_drafts._run_outlook_draft_export",
        lambda subject, body, to_emails, cc_emails: captured.update({"to_emails": to_emails, "subject": subject}),
    )

    payload = export_action_queue_outlook_draft("::alpha::444")

    assert payload["exported"] is True
    assert captured["to_emails"] == ["company_18@mail.com"]
    assert captured["subject"] == "Reservation reminder - Reservation 444 expired"


def test_outlook_draft_export_derives_canonical_subject_when_only_legacy_subject_is_present(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "app.service.outlook_drafts.load_readmodel",
        lambda name: {
            "expired_draft_workflow": {
                "drafts": [
                    {
                        "draft_key": "::alpha::444|436|421",
                        "subject": "Alpha Roasters expired reservation reminder",
                        "line_items": [
                            {"reservation_key": "444"},
                            {"reservation_key": "436"},
                            {"reservation_key": "421"},
                        ],
                        "to_emails": ["alpha@test.example"],
                        "cc_emails": [],
                        "can_export": True,
                    }
                ]
            }
        },
    )

    monkeypatch.setattr(
        "app.service.outlook_drafts._run_outlook_draft_export",
        lambda subject, body, to_emails, cc_emails: captured.update({"subject": subject, "body": body}),
    )

    payload = export_action_queue_outlook_draft("::alpha::444|436|421")

    assert payload["subject"] == "Reservation reminder - Reservations 444, 436 and 421 expired"
    assert captured["subject"] == "Reservation reminder - Reservations 444, 436 and 421 expired"


def test_handle_export_outlook_draft_returns_success_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.service.routes_outlook_drafts.export_action_queue_outlook_draft",
        lambda draft_key: {
            "draft_key": draft_key,
            "exported": True,
            "status": "Exported to Outlook draft",
            "subject": "Reservation reminder - Reservation 444 expired",
        },
    )

    response = handle_export_outlook_draft({"draft_key": "::alpha::444"})

    assert response.status_code == 200
    assert response.payload["status"] == "Exported to Outlook draft"


def test_dispatch_routes_outlook_export_requests(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.service.routes_outlook_drafts.export_action_queue_outlook_draft",
        lambda draft_key: {
            "draft_key": draft_key,
            "exported": True,
            "status": "Exported to Outlook draft",
            "subject": "Reservation reminder - Reservation 444 expired",
        },
    )

    response = _dispatch("POST", "/actions/outlook-draft/export", {"draft_key": "::alpha::444"})

    assert response.status_code == 200
    assert response.payload["draft_key"] == "::alpha::444"

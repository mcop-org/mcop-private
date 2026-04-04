from __future__ import annotations

from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path
import subprocess
import sys
import tempfile

from app.service.readmodel_store import load_readmodel


class DraftNotFoundError(LookupError):
    pass


class DraftExportBlockedError(ValueError):
    pass


class OutlookDraftExportError(RuntimeError):
    pass


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _format_reservation_identifier(value: object) -> str:
    text = _clean_text(value)
    if not text:
        return "-"
    if text.endswith(".0") and text.replace(".", "", 1).replace("-", "", 1).isdigit():
        return text[:-2]
    try:
        numeric = float(text)
    except ValueError:
        return text
    if numeric.is_integer():
        return str(int(numeric))
    return text


def _reservation_ids_from_draft(draft: dict[str, object]) -> list[str]:
    ids: list[str] = []
    for row in list(draft.get("email_body_table_rows") or []):
        reservation = _format_reservation_identifier(dict(row or {}).get("reservation"))
        if reservation != "-":
            ids.append(reservation)
    if ids:
        unique_ids: list[str] = []
        for reservation in ids:
            if reservation not in unique_ids:
                unique_ids.append(reservation)
        return unique_ids
    for item in list(draft.get("line_items") or []):
        reservation = _format_reservation_identifier(dict(item or {}).get("reservation_key"))
        if reservation != "-":
            ids.append(reservation)
    unique_ids: list[str] = []
    for reservation in ids:
        if reservation not in unique_ids:
            unique_ids.append(reservation)
    return unique_ids


def _canonical_subject(draft: dict[str, object]) -> str:
    reservation_ids = _reservation_ids_from_draft(draft)
    if len(reservation_ids) == 1:
        return f"Reservation reminder - Reservation {reservation_ids[0]} expired"
    if 1 < len(reservation_ids) <= 3:
        if len(reservation_ids) == 2:
            joined = f"{reservation_ids[0]} and {reservation_ids[1]}"
        else:
            joined = f"{', '.join(reservation_ids[:-1])} and {reservation_ids[-1]}"
        return f"Reservation reminder - Reservations {joined} expired"
    if len(reservation_ids) > 3:
        return f"Reservation reminder - {len(reservation_ids)} expired reservations"
    return "Reservation reminder - Expired reservations"


def _canonical_body_intro(draft: dict[str, object]) -> str:
    explicit = _clean_text(draft.get("email_body_intro"))
    if explicit:
        return explicit
    greeting_name = _clean_text(draft.get("greeting_name")) or _clean_text(draft.get("company_name")) or "there"
    return (
        f"Hi {greeting_name},\n\n"
        "We are writing to remind you that the reservation(s) below are now past their expiry date."
    )


def _canonical_body_closing(draft: dict[str, object]) -> str:
    explicit = _clean_text(draft.get("email_body_closing"))
    if explicit:
        return explicit
    return (
        "Please review the reservations above and let us know how you would like to proceed with release planning.\n\n"
        "Kind regards,\n"
        "Mi Cafe Trading Co."
    )


def _canonical_body_rows(draft: dict[str, object]) -> list[dict[str, object]]:
    rows = [dict(row or {}) for row in list(draft.get("email_body_table_rows") or [])]
    if rows:
        return rows
    derived_rows = []
    for item in list(draft.get("line_items") or []):
        line_item = dict(item or {})
        derived_rows.append(
            {
                "reservation": _format_reservation_identifier(line_item.get("reservation_key")),
                "reference": _clean_text(line_item.get("product_reference")) or "-",
                "bags_remaining": line_item.get("bags_remaining"),
                "expired_on": _clean_text(line_item.get("expiry_date")) or "",
                "days_expired": line_item.get("days_expired"),
                "kg_remaining": line_item.get("remaining_kg"),
                "value": line_item.get("remaining_value_gbp"),
            }
        )
    return derived_rows


def _canonical_export_block_reason(draft: dict[str, object]) -> str:
    explicit = _clean_text(draft.get("export_block_reason"))
    if explicit:
        return explicit
    return "Primary recipient email missing. Draft is review-only and cannot be exported."


def _to_emails(draft: dict[str, object]) -> list[str]:
    to_emails = [_clean_text(value) for value in list(draft.get("to_emails") or []) if _clean_text(value)]
    if to_emails:
        return to_emails
    primary = _clean_text(draft.get("contact_email"))
    return [primary] if primary else []


def _primary_recipient_present(draft: dict[str, object]) -> bool:
    return bool(_to_emails(draft))


def _format_decimal(value: object, suffix: str = "", money: bool = False) -> str:
    if value in (None, ""):
        return "-"
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "-"
    normalized = decimal_value.quantize(Decimal("0.01"))
    if money:
        return f"£{normalized:,.2f}"
    text = format(normalized.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"{text}{suffix}" if text else f"0{suffix}"


def _format_date(value: object) -> str:
    text = _clean_text(value)
    return text or "-"


def _load_action_queue_draft(draft_key: str) -> dict[str, object]:
    payload = load_readmodel("action_queue")
    workflow = dict(payload.get("expired_draft_workflow") or {})
    for raw_draft in list(workflow.get("drafts") or []):
        draft = dict(raw_draft or {})
        if _clean_text(draft.get("draft_key")) == draft_key:
            return draft
    raise DraftNotFoundError("Expired draft not found in the current action queue workspace.")


def _build_html_table_rows(draft: dict[str, object]) -> str:
    rows = _canonical_body_rows(draft)
    if not rows:
        return (
            "<tr>"
            "<td colspan=\"7\" style=\"padding:12px 14px;border:1px solid #d9e0e6;color:#4a5560;\">"
            "No reservation rows available."
            "</td>"
            "</tr>"
        )

    html_rows: list[str] = []
    for row in rows:
        item = dict(row or {})
        row_cells = [
            escape(_clean_text(item.get("reservation")) or "-"),
            escape(_clean_text(item.get("reference")) or "-"),
            escape(_format_decimal(item.get("bags_remaining"))),
            escape(_format_date(item.get("expired_on"))),
            escape(_format_decimal(item.get("days_expired"))),
            escape(_format_decimal(item.get("kg_remaining"), suffix=" kg")),
            escape(_format_decimal(item.get("value"), money=True)),
        ]
        html_rows.append(
            "<tr>"
            + "".join(
                [
                    (
                        "<td style=\"padding:10px 12px;border:1px solid #d9e0e6;"
                        "vertical-align:top;color:#1f2933;font-size:14px;\">"
                        f"{cell}</td>"
                    )
                    for cell in row_cells
                ]
            )
            + "</tr>"
        )
    return "".join(html_rows)


def _build_plaintext_body(draft: dict[str, object]) -> str:
    intro = escape(_canonical_body_intro(draft)).replace("\n", "<br>")
    review_sentence_text = (
        "Please review the reservations above and let us know how you would like to proceed with release planning."
    )
    raw_closing = _canonical_body_closing(draft).lstrip()
    if raw_closing.startswith(review_sentence_text):
        raw_closing = raw_closing[len(review_sentence_text) :].lstrip()
    closing = escape(raw_closing).replace("\n", "<br>")
    review_sentence = escape(review_sentence_text)
    table_rows = _build_html_table_rows(draft)
    return (
        "<html>"
        "<body style=\"margin:0;padding:0;background:#ffffff;color:#1f2933;"
        "font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:1.5;\">"
        "<div style=\"max-width:900px;padding:24px;\">"
        f"<p style=\"margin:0 0 18px 0;\">{intro}</p>"
        "<p style=\"margin:0 0 14px 0;font-weight:600;color:#1f2933;\">Reservations requiring review</p>"
        "<table style=\"border-collapse:collapse;width:100%;margin:0 0 18px 0;"
        "font-size:14px;\">"
        "<thead>"
        "<tr>"
        "<th style=\"text-align:left;padding:10px 12px;border:1px solid #cbd2d9;background:#f5f7fa;\">Reservation</th>"
        "<th style=\"text-align:left;padding:10px 12px;border:1px solid #cbd2d9;background:#f5f7fa;\">Reference</th>"
        "<th style=\"text-align:left;padding:10px 12px;border:1px solid #cbd2d9;background:#f5f7fa;\">Bags Remaining</th>"
        "<th style=\"text-align:left;padding:10px 12px;border:1px solid #cbd2d9;background:#f5f7fa;\">Expired On</th>"
        "<th style=\"text-align:left;padding:10px 12px;border:1px solid #cbd2d9;background:#f5f7fa;\">Days Expired</th>"
        "<th style=\"text-align:left;padding:10px 12px;border:1px solid #cbd2d9;background:#f5f7fa;\">KG Remaining</th>"
        "<th style=\"text-align:left;padding:10px 12px;border:1px solid #cbd2d9;background:#f5f7fa;\">Value</th>"
        "</tr>"
        "</thead>"
        f"<tbody>{table_rows}</tbody>"
        "</table>"
        f"<p style=\"margin:0 0 18px 0;\">{review_sentence}</p>"
        f"<p style=\"margin:0;\">{closing}</p>"
        "</div>"
        "</body>"
        "</html>"
    )


def _outlook_applescript() -> str:
    return """
on splitRecipients(recipientText)
  if recipientText is "" then
    return {}
  end if
  set AppleScript's text item delimiters to "||"
  set recipientItems to text items of recipientText
  set AppleScript's text item delimiters to ""
  return recipientItems
end splitRecipients

on normalizedRecipientAddresses(recipientList)
  set normalizedAddresses to {}
  repeat with candidateRecipient in recipientList
    set addressText to ""
    try
      set addressText to address of candidateRecipient
    on error
      set addressText to ""
    end try
    set end of normalizedAddresses to normalizeComparisonText(addressText)
  end repeat
  return normalizedAddresses
end normalizedRecipientAddresses

on replaceText(sourceText, searchText, replacementText)
  if searchText is "" then
    return sourceText
  end if
  set AppleScript's text item delimiters to searchText
  set textItems to text items of sourceText
  set AppleScript's text item delimiters to replacementText
  set replacedText to textItems as text
  set AppleScript's text item delimiters to ""
  return replacedText
end replaceText

on normalizeComparisonText(sourceText)
  set normalizedText to sourceText as text
  set normalizedText to replaceText(normalizedText, return, linefeed)
  set normalizedText to replaceText(normalizedText, linefeed, " ")
  repeat while normalizedText contains "  "
    set normalizedText to replaceText(normalizedText, "  ", " ")
  end repeat
  repeat while normalizedText begins with " "
    if (length of normalizedText) is 1 then
      return ""
    end if
    set normalizedText to text 2 thru -1 of normalizedText
  end repeat
  repeat while normalizedText ends with " "
    if (length of normalizedText) is 1 then
      return ""
    end if
    set normalizedText to text 1 thru -2 of normalizedText
  end repeat
  return normalizedText
end normalizeComparisonText

on run argv
  set draftSubject to item 1 of argv
  set draftBody to item 2 of argv
  set toRecipientsText to item 3 of argv
  set ccRecipientsText to item 4 of argv
  set toRecipients to splitRecipients(toRecipientsText)
  set ccRecipients to splitRecipients(ccRecipientsText)

  tell application "Microsoft Outlook"
    activate
    set newMessage to make new outgoing message with properties {subject:draftSubject}
    set content of newMessage to draftBody
    repeat with recipientAddress in toRecipients
      make new recipient at newMessage with properties {email address:{address:(recipientAddress as text)}}
    end repeat
    repeat with recipientAddress in ccRecipients
      make new recipient at newMessage with properties {email address:{address:(recipientAddress as text)}}
    end repeat
    set actualRecipientCount to count of every recipient of newMessage
    set expectedRecipientCount to (count of toRecipients) + (count of ccRecipients)
    if actualRecipientCount is not expectedRecipientCount then
      error "Outlook draft recipients did not match the reviewed draft."
    end if
    open newMessage
  end tell

  return "persisted"
end run
""".strip()


def _run_outlook_draft_export(subject: str, body: str, to_emails: list[str], cc_emails: list[str]) -> None:
    if sys.platform != "darwin":
        raise OutlookDraftExportError("Outlook draft export is only available on macOS.")

    script_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".applescript", encoding="utf-8", delete=False) as handle:
            handle.write(_outlook_applescript())
            script_path = Path(handle.name)
        result = subprocess.run(
            [
                "osascript",
                str(script_path),
                subject,
                body,
                "||".join(to_emails),
                "||".join(cc_emails),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise OutlookDraftExportError(f"Unable to run Outlook draft export: {exc}") from exc
    finally:
        if script_path is not None:
            script_path.unlink(missing_ok=True)

    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip() or "Outlook draft export failed."
        raise OutlookDraftExportError(message)
    if (result.stdout or "").strip() != "persisted":
        raise OutlookDraftExportError("Outlook draft export did not confirm persisted draft creation.")


def export_action_queue_outlook_draft(draft_key: str) -> dict[str, object]:
    draft = _load_action_queue_draft(draft_key)
    if not _primary_recipient_present(draft):
        raise DraftExportBlockedError(_canonical_export_block_reason(draft))

    to_emails = _to_emails(draft)
    cc_emails = [_clean_text(value) for value in list(draft.get("cc_emails") or []) if _clean_text(value)]
    if not to_emails:
        raise DraftExportBlockedError("Primary recipient email missing. Draft is review-only and cannot be exported.")

    subject = _canonical_subject(draft)
    body = _build_plaintext_body(draft)
    _run_outlook_draft_export(subject, body, to_emails, cc_emails)
    return {
        "draft_key": draft_key,
        "exported": True,
        "status": "Exported to Outlook draft",
        "subject": subject,
    }

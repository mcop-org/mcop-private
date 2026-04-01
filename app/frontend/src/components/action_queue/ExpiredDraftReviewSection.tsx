import type { ActionQueueReadModel } from "../../lib/contracts";
import { formatReservationKey, getStatusChipClass } from "../../lib/presentation";

type ExpiredDraftReviewSectionProps = {
  workflow: ActionQueueReadModel["expired_draft_workflow"];
};

function formatNumber(value: number, maximumFractionDigits = 0) {
  return new Intl.NumberFormat("en-GB", {
    maximumFractionDigits,
    minimumFractionDigits: maximumFractionDigits,
  }).format(value);
}

function formatMoney(value: number | null | undefined) {
  if (typeof value !== "number") {
    return "";
  }
  return `, value GBP ${formatNumber(value, 2)}`;
}

type DraftLineItem = {
  bags_remaining?: number;
  days_expired?: number;
  expiry_date?: string;
  product_reference?: string;
  remaining_kg?: number | null;
  remaining_value_gbp?: number | null;
  reservation_key?: string;
};

type DraftRecord = {
  company_name?: string;
  client_id?: string;
  contact_email?: string;
  subject?: string;
  to_emails?: string[];
  cc_emails?: string[];
  breached_reservation_count?: number;
  breached_row_count?: number;
  missing_primary_email?: boolean;
  greeting_name?: string;
  line_items?: DraftLineItem[];
};

function formatDraftLineItem(item: DraftLineItem): string {
  const bags = typeof item.bags_remaining === "number" ? formatNumber(item.bags_remaining, 0) : "-";
  const daysExpired = typeof item.days_expired === "number" ? formatNumber(item.days_expired, 0) : "-";
  const remainingKg = typeof item.remaining_kg === "number" ? formatNumber(item.remaining_kg, 0) : "-";

  return `Reservation ${formatReservationKey(item.reservation_key)} | ${item.product_reference || "-"} | ${bags} bags remaining | expired on ${item.expiry_date || "-"} | ${daysExpired} days expired | ${remainingKg} kg remaining${formatMoney(item.remaining_value_gbp)}`;
}

function renderDraftBody(draft: DraftRecord) {
  const greetingName = draft.greeting_name || draft.company_name || "there";
  const lineItems = (draft.line_items || []).map((item, index) => (
    <li key={`${item.reservation_key || "reservation"}-${index}`}>{formatDraftLineItem(item)}</li>
  ));

  return (
    <div className="draft-body-rich">
      <p>Hi {greetingName},</p>
      <p>We hope you are well.</p>
      <p>We are writing to remind you that the reservations below are now past their expiry date.</p>
      <ul className="draft-line-list">{lineItems}</ul>
      <p>Please review these reservations and let us know how you would like to proceed with release planning.</p>
      <p>Kind regards,<br />Mi Cafe Trading Co.</p>
    </div>
  );
}

export function ExpiredDraftReviewSection({ workflow }: ExpiredDraftReviewSectionProps) {
  const summary = workflow.summary || {};
  const drafts = ((workflow.drafts || []) as DraftRecord[]).slice();

  return (
    <section className="card">
      <div className="section-head">
        <div>
          <h4>Expired Reservation Draft Review</h4>
          <p>Grouped by client from breached reservations only. Drafts are review-only and are not sent from MCOP.</p>
        </div>
      </div>
      <div className="card-grid three-up">
        <section className="stat-card">
          <span className="stat-label">Draft Clients</span>
          <strong>{formatNumber(Number(summary.draft_client_count || 0), 0)}</strong>
        </section>
        <section className="stat-card">
          <span className="stat-label">Breached Reservations In Drafts</span>
          <strong>{formatNumber(Number(summary.breached_reservations || 0), 0)}</strong>
        </section>
        <section className="stat-card">
          <span className="stat-label">Missing Primary Email</span>
          <strong>{formatNumber(Number(summary.drafts_missing_primary_email || 0), 0)}</strong>
          <span className="stat-label">{String(summary.status || "-")}</span>
        </section>
      </div>
      {drafts.length ? (
        <div className="draft-review-list">
          {drafts.map((draft, index) => (
            <article className="stat-card draft-card" key={`${draft.client_id || draft.company_name || "draft"}-${index}`}>
              <div className="section-head">
                <div>
                  <h4>{draft.company_name || "Unknown client"}</h4>
                  <p>
                    Client ID: {draft.client_id || "-"} | To: {(draft.to_emails || []).join(", ") || draft.contact_email || "-"}
                  </p>
                </div>
                <span className={getStatusChipClass(draft.missing_primary_email ? "Missing Primary Email" : "Completed")}>
                  {draft.missing_primary_email ? "Missing primary email" : "Ready for review"}
                </span>
              </div>
              <p>
                Breached reservations: {formatNumber(Number(draft.breached_reservation_count || 0), 0)} | Breached rows:{" "}
                {formatNumber(Number(draft.breached_row_count || 0), 0)}
              </p>
              <p><strong>Subject:</strong> {draft.subject || "-"}</p>
              {renderDraftBody(draft)}
            </article>
          ))}
        </div>
      ) : (
        <p>No expired reservation drafts are available in the current workspace snapshot.</p>
      )}
    </section>
  );
}

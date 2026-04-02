import type { ClientIntelligenceSummary } from "../../lib/contracts";
import { formatCount, formatMoney, formatPercent } from "../../lib/presentation";

function formatShare(value: number | null) {
  if (value === null || !Number.isFinite(value)) {
    return "Unavailable";
  }
  return formatPercent(value);
}

type ClientIntelligenceSummaryCardsProps = {
  summary: ClientIntelligenceSummary & {
    concentration_top_five_share: number | null;
    concentration_top_ten_share: number | null;
    concentration_rest_share: number | null;
    concentration_share_available: boolean;
  };
};

export function ClientIntelligenceSummaryCards({ summary }: ClientIntelligenceSummaryCardsProps) {
  const largestClientLabel = [summary.largest_client_company_name, summary.largest_client_id]
    .filter(Boolean)
    .join(" · ");

  return (
    <section className="client-kpi-grid">
      <article className="card client-kpi-card">
        <div className="eyebrow">Clients With Reservation Activity</div>
        <strong>{formatCount(summary.clients_with_current_exposure)}</strong>
      </article>
      <article className="card client-kpi-card">
        <div className="eyebrow">Recorded Reservation Value</div>
        <strong>
          {summary.total_current_reserved_value_available
            ? formatMoney(summary.total_current_reserved_value_gbp)
            : "Unavailable"}
        </strong>
        <span className="meta-note">
          {summary.total_current_reserved_value_available
            ? "Complete across recorded client rows in the selected request-date range."
            : "Unavailable on one or more recorded client rows due to missing kg or price."}
        </span>
      </article>
      <article className="card client-kpi-card">
        <div className="eyebrow">Largest Recorded Reservation Value</div>
        <strong>
          {summary.largest_client_reserved_value_available
            ? formatMoney(summary.largest_client_reserved_value_gbp)
            : "Unavailable"}
        </strong>
        <span className="meta-note">
          {largestClientLabel || "No client activity in the selected date range."}
        </span>
      </article>
      <article className="card client-kpi-card">
        <div className="eyebrow">Clients Concentrated In One Reference</div>
        <strong>{formatCount(summary.clients_concentrated_in_one_reference)}</strong>
        <span className="meta-note">Primary reference share at or above 80%.</span>
      </article>
      <article className="card client-kpi-card">
        <div className="eyebrow">Client Concentration</div>
        <strong>
          {summary.concentration_share_available
            ? formatShare(summary.concentration_top_five_share)
            : "No concentration view"}
        </strong>
        <span className="meta-note">
          {summary.concentration_share_available
            ? `Top 10: ${formatShare(summary.concentration_top_ten_share)}`
            : "Top 10: unavailable for this range"}
        </span>
        <span className="meta-note">
          {summary.concentration_share_available
            ? `Rest: ${formatShare(summary.concentration_rest_share)}`
            : "Rest: unavailable for this range"}
        </span>
      </article>
    </section>
  );
}

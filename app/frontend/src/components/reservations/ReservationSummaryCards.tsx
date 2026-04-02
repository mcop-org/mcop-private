import type { ReservationDetailRow, ReservationSummaryRow } from "../../lib/contracts";
import {
  formatCount,
  formatIsoDate,
  formatKg,
  formatMoney,
  getStatusChipClass,
} from "../../lib/presentation";

type ReservationSummaryCardsProps = {
  snapshotDate: string;
  summary?: ReservationSummaryRow;
  rows: ReservationDetailRow[];
};

function formatPercent(value: number) {
  return `${formatCount(value * 100, 1)}%`;
}

function landingSupportText(
  summary: ReservationSummaryRow | undefined,
  rows: ReservationDetailRow[],
  snapshotDate: string,
) {
  if (!summary) {
    return "Landing date not available for this reference.";
  }

  const uniqueDates = [...new Set(rows.map((row) => row.landing_date || "").filter((value) => /^\d{4}-\d{2}-\d{2}$/.test(value)))].sort();
  if (uniqueDates.length !== 1) {
    return "Landing date not available for this reference.";
  }

  const landingDate = uniqueDates[0];
  const landingLabel = formatIsoDate(landingDate);

  const snapshot = snapshotDate ? new Date(`${snapshotDate}T00:00:00Z`) : null;
  const landing = new Date(`${landingDate}T00:00:00Z`);
  const diff =
    snapshot && Number.isFinite(snapshot.getTime())
      ? Math.round((landing.getTime() - snapshot.getTime()) / 86_400_000)
      : null;

  if (summary.landing_status.toLowerCase() === "incoming") {
    if (diff === null) {
      return `Expected on ${landingLabel}.`;
    }
    if (diff > 0) {
      return `Expected on ${landingLabel}, in ${formatCount(diff)} days.`;
    }
    if (diff === 0) {
      return `Expected to land today, ${landingLabel}.`;
    }
    return `Expected on ${landingLabel}.`;
  }

  if (summary.landing_status.toLowerCase() === "landed") {
    if (diff === null || diff >= 0) {
      return `Recorded as landed on ${landingLabel}.`;
    }
    return `Recorded as landed on ${landingLabel}, ${formatCount(Math.abs(diff))} days ago.`;
  }

  return "Landing date not available for this reference.";
}

export function ReservationSummaryCards({ snapshotDate, summary, rows }: ReservationSummaryCardsProps) {
  return (
    <div className="card-grid reservation-kpi-grid">
      <section className="card stat-card-strong">
        <span className="stat-label">Reserved KG</span>
        <strong>{summary ? formatKg(summary.reserved_kg) : "0 kg"}</strong>
        <span className="stat-label">{summary ? `${formatCount(summary.reserved_bags)} reserved bags` : "0 reserved bags"}</span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Reserved Value</span>
        <strong>{summary ? formatMoney(summary.reserved_value_gbp) : "£0"}</strong>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Reserved %</span>
        <strong>{summary ? formatPercent(summary.reserved_pct) : "0.0%"}</strong>
        <span className="stat-label">{summary ? `${formatCount(summary.bags_available)} bags still available` : "0 bags still available"}</span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Clients</span>
        <strong>{summary ? formatCount(summary.client_count) : "0"}</strong>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Landing Status</span>
        <div className="card-chip-row">
          <span className={getStatusChipClass(summary?.landing_status || "Unknown")}>
            {summary?.landing_status || "No reservations"}
          </span>
        </div>
        <span className="stat-label">{landingSupportText(summary, rows, snapshotDate)}</span>
      </section>
    </div>
  );
}

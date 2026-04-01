import type { ProductReferenceSummaryRow } from "../../lib/contracts";

type ProductReferenceSummaryCardsProps = {
  summary: ProductReferenceSummaryRow | null;
};

function formatBags(value: number) {
  return `${new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value)} bags`;
}

function formatKg(value: number) {
  return `${new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value)} kg`;
}

function statusTone(value: string) {
  const status = value.trim().toLowerCase();
  if (status === "balanced") {
    return "tone-good";
  }
  if (status === "mostly incoming") {
    return "tone-warm";
  }
  if (status === "landed build-up") {
    return "tone-danger";
  }
  return "tone-neutral";
}

export function ProductReferenceSummaryCards({
  summary,
}: ProductReferenceSummaryCardsProps) {
  const incomingBags = summary?.incoming_bags_available ? formatBags(Number(summary.incoming_bags || 0)) : "Unavailable";
  const incomingKg = summary?.incoming_kg_available ? formatKg(Number(summary.incoming_kg || 0)) : "Unavailable";
  const landedBags = summary?.landed_bags_available ? formatBags(Number(summary.landed_bags || 0)) : "Unavailable";
  const landedKg = summary?.landed_kg_available ? formatKg(Number(summary.landed_kg || 0)) : "Unavailable";
  const availableBags = summary?.landed_available_bags_available ? formatBags(Number(summary.landed_available_bags || 0)) : "Unavailable";
  const availableKg = summary?.landed_available_kg_available ? formatKg(Number(summary.landed_available_kg || 0)) : "Unavailable";
  const stockHealth = summary?.stock_health || "Data Incomplete";

  return (
    <div className="card-grid reservation-kpi-grid">
      <section className="card stat-card-strong">
        <span className="stat-label">Incoming Stock</span>
        <strong>{incomingBags}</strong>
        <span className="stat-label">{incomingKg}</span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Landed Stock</span>
        <strong>{landedBags}</strong>
        <span className="stat-label">{landedKg}</span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Landed Available</span>
        <strong>{availableBags}</strong>
        <span className="stat-label">{availableKg}</span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Stock Health</span>
        <div className="card-chip-row">
          <span className={`status-chip ${statusTone(stockHealth)}`}>{stockHealth}</span>
        </div>
        <span className="stat-label">Safe stock-state classification only.</span>
      </section>
    </div>
  );
}

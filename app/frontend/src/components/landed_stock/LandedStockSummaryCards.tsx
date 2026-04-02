import type { LandedStockSummary } from "../../lib/contracts";
import { formatCount, formatIsoDate, formatKg, formatMoney } from "../../lib/presentation";

type LandedStockSummaryCardsProps = {
  summary?: LandedStockSummary;
};

export function LandedStockSummaryCards({ summary }: LandedStockSummaryCardsProps) {
  const asOfLabel = summary?.as_of_date ? `As of ${formatIsoDate(summary.as_of_date)}` : "As of date unavailable";
  const valueStatus = summary?.value_completeness_status || "No landed stock rows.";

  return (
    <div className="card-grid reservation-kpi-grid">
      <section className="card stat-card-strong">
        <span className="stat-label">Unsold Landed Bags</span>
        <strong>{formatCount(Number(summary?.unsold_landed_bags || 0))}</strong>
        <span className="stat-label">
          {formatCount(Number(summary?.landed_bags || 0))} landed bags in total
        </span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Unsold Landed KG</span>
        <strong>{formatKg(Number(summary?.unsold_landed_kg || 0))}</strong>
        <span className="stat-label">
          {summary?.unsold_landed_kg_available ? "Complete" : "Unavailable on some unsold landed rows."}
        </span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Aged 180+ Bags</span>
        <strong>{formatCount(Number(summary?.aged_180_plus_bags || 0))}</strong>
        <span className="stat-label">Unsold landed bags aged 181 days or more</span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Warehouses Exposed</span>
        <strong>{formatCount(Number(summary?.warehouses_exposed || 0))}</strong>
        <span className="stat-label">{asOfLabel}</span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Unsold Landed Value</span>
        <strong>{formatMoney(Number(summary?.unsold_landed_value_gbp || 0))}</strong>
        <span className="stat-label">{valueStatus}</span>
      </section>
    </div>
  );
}

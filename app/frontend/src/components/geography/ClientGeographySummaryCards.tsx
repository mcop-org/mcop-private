import type {
  ClientGeographyLocationRow,
  ClientGeographySummary,
} from "../../lib/contracts";

type ClientGeographySummaryCardsProps = {
  summary: ClientGeographySummary;
  filteredLocations: ClientGeographyLocationRow[];
};

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value);
}

export function ClientGeographySummaryCards({
  summary,
  filteredLocations,
}: ClientGeographySummaryCardsProps) {
  const mappedClients = filteredLocations.reduce((sum, row) => sum + Number(row.client_count || 0), 0);
  const countries = new Set(filteredLocations.map((row) => row.country).filter(Boolean));
  const cities = new Set(filteredLocations.map((row) => `${row.country}||${row.city}`).filter((value) => !value.endsWith("||")));
  const exposedLocations = filteredLocations.filter((row) => Number(row.exposed_client_count || 0) > 0).length;

  return (
    <section className="card-grid geography-kpi-grid">
      <section className="card stat-card-strong">
        <span className="stat-label">Mapped Clients</span>
        <strong>{formatNumber(mappedClients)}</strong>
        <span className="stat-label">
          {formatNumber(filteredLocations.length)} mapped delivery locations in the current view.
        </span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Unmapped Clients</span>
        <strong>{formatNumber(Number(summary.unmapped_clients || 0))}</strong>
        <span className="stat-label">
          {formatNumber(Number(summary.unresolved_map_clients || 0))} mapped clients remain unresolved for plotting.
        </span>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Countries Covered</span>
        <strong>{formatNumber(countries.size)}</strong>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Cities Covered</span>
        <strong>{formatNumber(cities.size)}</strong>
      </section>
      <section className="card stat-card-strong">
        <span className="stat-label">Exposed Client Locations</span>
        <strong>{formatNumber(exposedLocations)}</strong>
        <span className="stat-label">{summary.map_status || "No plotted client markers available."}</span>
      </section>
    </section>
  );
}

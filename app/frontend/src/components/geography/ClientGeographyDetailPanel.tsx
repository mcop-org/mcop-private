import type { ClientGeographyMapClientRow } from "../../lib/contracts";
import { formatCount, formatKg, formatMoney } from "../../lib/presentation";

type ClientGeographyDetailPanelProps = {
  selectedClient: ClientGeographyMapClientRow | null;
};

export function ClientGeographyDetailPanel({
  selectedClient,
}: ClientGeographyDetailPanelProps) {
  if (!selectedClient) {
    return (
      <aside className="card geography-detail-card">
        <div className="eyebrow">Selection Context</div>
        <h4>Client Detail</h4>
        <p className="meta-note">
          Select a resolved client marker to inspect the delivery geography and reservation footprint.
        </p>
      </aside>
    );
  }

  const primaryReference =
    String(selectedClient.primary_reference || "").trim() || "No current reservation reference";
  const reservedValue = selectedClient.reserved_value_available
    ? formatMoney(Number(selectedClient.reserved_value_gbp || 0))
    : "Unavailable";

  return (
    <aside className="card geography-detail-card">
      <div className="eyebrow">Selection Context</div>
      <div className="section-head">
        <div>
          <h4>{selectedClient.company_name || "Unknown Client"}</h4>
          <p className="meta-note">
            {[selectedClient.city, selectedClient.postcode, selectedClient.country].filter(Boolean).join(", ") ||
              "Unknown delivery geography"}
          </p>
        </div>
        <span className={`status-chip ${selectedClient.has_exposure ? "tone-good" : "tone-warm"}`}>
          {selectedClient.has_exposure ? "With Current Exposure" : "Zero Exposure"}
        </span>
      </div>
      <div className="stat-grid geography-detail-grid">
        <div className="stat-card">
          <span className="stat-label">Reservation Value</span>
          <strong>{reservedValue}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Reserved Bags</span>
          <strong>{formatCount(Number(selectedClient.reserved_bags || 0), 2)}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Reserved KG</span>
          <strong>{formatKg(Number(selectedClient.reserved_kg || 0))}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Linked References</span>
          <strong>{formatCount(Number(selectedClient.distinct_reference_count || 0))}</strong>
        </div>
      </div>
      <div className="metadata geography-detail-meta">
        <span>Client ID: {selectedClient.client_id || "-"}</span>
        <span>Primary Reference: {primaryReference}</span>
        <span>Coordinate Match: {selectedClient.coordinate_match_level || "-"}</span>
      </div>
    </aside>
  );
}

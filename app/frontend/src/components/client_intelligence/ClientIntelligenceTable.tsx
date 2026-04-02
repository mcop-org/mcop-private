import type { ClientIntelligenceDetailRow } from "../../lib/contracts";
import { formatCount, formatKg, formatMoney, formatPercent } from "../../lib/presentation";

function formatShare(value: number | null, available: boolean) {
  if (!available || value === null) {
    return "Unavailable";
  }
  return formatPercent(value);
}

function formatValue(value: number, available: boolean) {
  return available ? formatMoney(value) : "Unavailable";
}

type ClientIntelligenceTableProps = {
  rows: ClientIntelligenceDetailRow[];
};

export function ClientIntelligenceTable({ rows }: ClientIntelligenceTableProps) {
  return (
    <section className="card">
      <div className="section-head">
        <div>
          <div className="eyebrow">Client Intelligence Table</div>
          <h4>Client Activity Details</h4>
          <p className="meta-note">Default order shows highest recorded reservation value first for the selected date range.</p>
        </div>
      </div>
      {rows.length ? (
        <div className="table-wrap">
          <table className="data-table client-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Client ID</th>
                <th className="num">Reservation Rows</th>
                <th className="num">Reserved Bags Recorded</th>
                <th className="num">Reserved KG Recorded</th>
                <th className="num">Reserved Value Recorded</th>
                <th className="num">Distinct References</th>
                <th>Primary Reference</th>
                <th className="num">Primary Reference Share</th>
                <th>Landing Mix</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.company_name}-${row.client_id}`}>
                  <td>
                    <strong>{row.company_name || "-"}</strong>
                  </td>
                  <td>{row.client_id || "-"}</td>
                  <td className="num">{formatCount(row.reservation_row_count)}</td>
                  <td className="num">{formatCount(row.reserved_bags, 2)}</td>
                  <td className="num">{formatKg(row.reserved_kg)}</td>
                  <td className="num">{formatValue(row.reserved_value_gbp, row.reserved_value_available)}</td>
                  <td className="num">{formatCount(row.distinct_reference_count)}</td>
                  <td>{row.primary_reference || "-"}</td>
                  <td className="num">
                    {formatShare(row.primary_reference_share, row.primary_reference_share_available)}
                  </td>
                  <td>{row.landing_mix || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card-empty">No client rows match the current filters.</div>
      )}
    </section>
  );
}

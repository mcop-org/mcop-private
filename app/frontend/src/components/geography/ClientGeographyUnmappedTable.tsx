import type { ClientGeographyUnmappedClientRow } from "../../lib/contracts";

type ClientGeographyUnmappedTableProps = {
  rows: ClientGeographyUnmappedClientRow[];
};

function formatNumber(value: number, digits = 0) {
  return new Intl.NumberFormat("en-GB", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

function formatMoney(value: number) {
  return `GBP ${formatNumber(value, 0)}`;
}

export function ClientGeographyUnmappedTable({
  rows,
}: ClientGeographyUnmappedTableProps) {
  return (
    <section className="card">
      <div className="section-head reservation-table-head">
        <div>
          <h4>Unmapped Clients</h4>
          <p className="meta-note">
            Clients with reservation activity that could not be safely resolved into delivery geography remain visible here.
          </p>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Client ID</th>
              <th className="num">Reserved Bags</th>
              <th className="num">Reserved KG</th>
              <th className="num">Reserved Value GBP</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={`${row.client_id}-${row.company_name}-${index}`}>
                <td>
                  <strong>{row.company_name || "-"}</strong>
                </td>
                <td>{row.client_id || "-"}</td>
                <td className="num">{formatNumber(Number(row.reserved_bags || 0))}</td>
                <td className="num">{formatNumber(Number(row.reserved_kg || 0))} kg</td>
                <td className="num">
                  {row.reserved_value_available
                    ? formatMoney(Number(row.reserved_value_gbp || 0))
                    : "Unavailable"}
                </td>
                <td>{row.reason || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 ? <p className="meta-note">No unmapped clients in the current snapshot.</p> : null}
    </section>
  );
}

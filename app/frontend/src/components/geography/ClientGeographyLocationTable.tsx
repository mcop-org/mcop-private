import type {
  ClientGeographyLocationRow,
  ClientGeographyMapClientRow,
} from "../../lib/contracts";

type ClientGeographyLocationTableProps = {
  rows: ClientGeographyLocationRow[];
  selectedClient: ClientGeographyMapClientRow | null;
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

function locationKey(row: { country: string; city: string; postcode: string }) {
  return [row.country, row.city, row.postcode].join("||");
}

export function ClientGeographyLocationTable({
  rows,
  selectedClient,
}: ClientGeographyLocationTableProps) {
  const selectedKey = selectedClient
    ? locationKey(selectedClient)
    : "";

  return (
    <section className="card">
      <div className="section-head reservation-table-head">
        <div>
          <h4>Location-Level Geography Table</h4>
          <p className="meta-note">
            Delivery geography only. Default order remains the trusted output order.
          </p>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Country</th>
              <th>City</th>
              <th>Postcode</th>
              <th className="num">Client Count</th>
              <th className="num">Exposed Client Count</th>
              <th className="num">Reserved Bags</th>
              <th className="num">Reserved KG</th>
              <th className="num">Reserved Value GBP</th>
              <th>Top Client</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isActive = selectedKey !== "" && locationKey(row) === selectedKey;
              return (
                <tr key={locationKey(row)} className={isActive ? "table-row-active" : undefined}>
                  <td>
                    <strong>{row.country || "-"}</strong>
                  </td>
                  <td>{row.city || "-"}</td>
                  <td>{row.postcode || "-"}</td>
                  <td className="num">{formatNumber(Number(row.client_count || 0))}</td>
                  <td className="num">{formatNumber(Number(row.exposed_client_count || 0))}</td>
                  <td className="num">{formatNumber(Number(row.reserved_bags || 0))}</td>
                  <td className="num">{formatNumber(Number(row.reserved_kg || 0))} kg</td>
                  <td className="num">
                    {row.reserved_value_available
                      ? formatMoney(Number(row.reserved_value_gbp || 0))
                      : "Unavailable"}
                  </td>
                  <td>{row.top_client_company_name || "-"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {rows.length === 0 ? <p className="meta-note">No mapped client locations match the current filters.</p> : null}
    </section>
  );
}

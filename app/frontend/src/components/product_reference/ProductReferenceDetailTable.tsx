import type { ProductLandingProfileRow } from "../../lib/contracts";
import { formatCount, formatIsoDate } from "../../lib/presentation";

type ProductReferenceDetailTableProps = {
  rows: ProductLandingProfileRow[];
  snapshotDate: string;
  hasSelection: boolean;
};

function dayDiff(fromDate: string, toDate: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(fromDate) || !/^\d{4}-\d{2}-\d{2}$/.test(toDate)) {
    return null;
  }
  const from = new Date(`${fromDate}T00:00:00Z`);
  const to = new Date(`${toDate}T00:00:00Z`);
  const diff = Math.round((to.getTime() - from.getTime()) / 86400000);
  return Number.isFinite(diff) ? diff : null;
}

function renderDaysLabel(row: ProductLandingProfileRow, snapshotDate: string) {
  const landingStatus = String(row.landing_status || "").trim().toLowerCase();
  if (landingStatus === "incoming") {
    return "Not landed";
  }
  if (landingStatus === "landed") {
    const diff = dayDiff(row.landing_date || "", snapshotDate);
    if (diff !== null && diff >= 0) {
      return `${formatCount(diff)} days`;
    }
  }
  return "Date unavailable";
}

function statusTone(value: string) {
  const status = value.trim().toLowerCase();
  if (status === "landed") {
    return "tone-good";
  }
  if (status === "incoming") {
    return "tone-warm";
  }
  return "tone-neutral";
}

export function ProductReferenceDetailTable({
  rows,
  snapshotDate,
  hasSelection,
}: ProductReferenceDetailTableProps) {
  return (
    <section className="card">
      <div className="section-head reservation-table-head">
        <div>
          <h4>Stock Details by Lot / Warehouse</h4>
          <p className="meta-note">
            Default order shows landed available rows first, then other landed rows, then incoming rows.
          </p>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Product ID</th>
              <th>Warehouse</th>
              <th>Landing Status</th>
              <th>Landing Date</th>
              <th>Days Since Landing / Not landed</th>
              <th className="num">Bags</th>
              <th className="num">Bags Available</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.product_reference}-${row.product_id}-${row.warehouse}-${row.landing_date}`}>
                <td><strong>{row.product_id || "-"}</strong></td>
                <td>{row.warehouse || "-"}</td>
                <td>
                  <span className={`status-chip ${statusTone(row.landing_status || "")}`}>
                    {row.landing_status || "-"}
                  </span>
                </td>
                <td>{formatIsoDate(row.landing_date)}</td>
                <td>{renderDaysLabel(row, snapshotDate)}</td>
                <td className="num">{row.bags === null ? "Unavailable" : formatCount(Number(row.bags || 0), 2)}</td>
                <td className="num">{row.bags_available === null ? "Unavailable" : formatCount(Number(row.bags_available || 0), 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 ? (
        <p className="meta-note">
          {hasSelection ? "No product rows match the selected reference." : "Select a product reference to view stock details."}
        </p>
      ) : null}
    </section>
  );
}

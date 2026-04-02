import type { LandedStockDetailRow } from "../../lib/contracts";
import { formatCount, formatIsoDate, formatKg, formatMoney, getStatusChipClass } from "../../lib/presentation";

type LandedStockTableProps = {
  rows: LandedStockDetailRow[];
};

export function LandedStockTable({ rows }: LandedStockTableProps) {
  return (
    <section className="card">
      <div className="section-head reservation-table-head">
        <div>
          <h4>Landed Exposure Details</h4>
          <p>Landed rows with unsold exposure or incomplete availability data. Default order shows oldest landed exposure first.</p>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Product Reference</th>
              <th>Product ID</th>
              <th>Warehouse</th>
              <th>Landing Date</th>
              <th className="num">Days Since Landing</th>
              <th>Aging Bucket</th>
              <th className="num">Landed Bags</th>
              <th className="num">Unsold Bags</th>
              <th className="num">Unsold KG</th>
              <th className="num">Unsold Value</th>
              <th>Data Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.product_reference}-${row.product_id}-${row.landing_date}-${row.warehouse}`}>
                <td>
                  <strong>{row.product_reference || "-"}</strong>
                </td>
                <td>{row.product_id || "-"}</td>
                <td>{row.warehouse || "-"}</td>
                <td>{formatIsoDate(row.landing_date)}</td>
                <td className="num">{formatCount(row.days_since_landing)}</td>
                <td>{row.aging_bucket || "-"}</td>
                <td className="num">{formatCount(row.landed_bags)}</td>
                <td className="num">{formatCount(row.unsold_bags)}</td>
                <td className="num">{typeof row.unsold_kg === "number" ? formatKg(row.unsold_kg) : "-"}</td>
                <td className="num">{formatMoney(row.unsold_value_gbp)}</td>
                <td>
                  <span className={getStatusChipClass(row.data_status || "Unknown")}>{row.data_status || "-"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 ? <p>No landed rows match the current filters.</p> : null}
    </section>
  );
}

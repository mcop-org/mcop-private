import type { ActionQueueDetailRow } from "../../lib/contracts";
import {
  formatCount,
  formatIsoDate,
  formatKg,
  formatMoney,
  formatReservationKey,
  getStatusChipClass,
} from "../../lib/presentation";

type ActionQueueTableProps = {
  rows: ActionQueueDetailRow[];
};

export function ActionQueueTable({ rows }: ActionQueueTableProps) {
  return (
    <section className="card">
      <div className="section-head">
        <div>
          <h4>Action Queue Details</h4>
          <p>Default order shows breached first, then near-expiry, then landed-not-approved, then landed-not-released, then other open exposure.</p>
        </div>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Action Priority</th>
            <th>Action Bucket</th>
            <th className="num">Days to Expiry</th>
            <th>Expiry Date</th>
            <th>Company</th>
            <th>Client ID</th>
            <th>Reservation Key</th>
            <th>Product Reference</th>
            <th>Product ID</th>
            <th>Reservation Status</th>
            <th>Approval Date</th>
            <th className="num">Reservation Days</th>
            <th className="num">Bags Remaining</th>
            <th className="num">Remaining KG</th>
            <th className="num">Remaining Value</th>
            <th>Landing Status</th>
            <th>Landing Date</th>
            <th>Warehouse</th>
            <th>Data Status / Missing Fields</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.reservation_key}-${row.product_reference}-${row.action_priority}`}>
              <td><span className={getStatusChipClass(row.action_priority)}>{row.action_priority}</span></td>
              <td><span className={getStatusChipClass(row.action_bucket)}>{row.action_bucket}</span></td>
              <td className="num">{typeof row.days_to_expiry === "number" ? formatCount(row.days_to_expiry) : "-"}</td>
              <td>{formatIsoDate(row.expiry_date)}</td>
              <td>{row.company_name}</td>
              <td>{row.client_id || "-"}</td>
              <td>{formatReservationKey(row.reservation_key)}</td>
              <td>{row.product_reference}</td>
              <td>{row.product_id || "-"}</td>
              <td><span className={getStatusChipClass(row.request_status)}>{row.request_status}</span></td>
              <td>{formatIsoDate(row.approval_date)}</td>
              <td className="num">
                {typeof row.reservation_days === "number" ? formatCount(row.reservation_days) : "-"}
              </td>
              <td className="num">
                {typeof row.bags_remaining === "number" ? formatCount(row.bags_remaining, 2) : "-"}
              </td>
              <td className="num">{typeof row.remaining_kg === "number" ? formatKg(row.remaining_kg) : "-"}</td>
              <td className="num">{formatMoney(row.remaining_value_gbp)}</td>
              <td><span className={getStatusChipClass(row.landing_status || "Unknown")}>{row.landing_status || "-"}</span></td>
              <td>{formatIsoDate(row.landing_date)}</td>
              <td>{row.warehouse || "-"}</td>
              <td><span className={getStatusChipClass(row.data_status || "Unknown")}>{row.data_status || "-"}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 ? <p>No action rows match the current filters.</p> : null}
    </section>
  );
}

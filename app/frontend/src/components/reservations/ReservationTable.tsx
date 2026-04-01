import type { ReservationDetailRow } from "../../lib/contracts";
import { formatReservationKey, getStatusChipClass } from "../../lib/presentation";

type ReservationTableProps = {
  rows: ReservationDetailRow[];
  sortKey: ReservationSortKey;
  sortDirection: "asc" | "desc";
  onSortChange: (key: ReservationSortKey) => void;
};

export type ReservationSortKey =
  | "company_name"
  | "request_status"
  | "effective_bags"
  | "reserved_kg"
  | "reserved_value_gbp"
  | "landing_status"
  | "landing_date"
  | "warehouse"
  | "reservation_key";

function SortButton({
  label,
  column,
  sortKey,
  sortDirection,
  onSortChange,
}: {
  label: string;
  column: ReservationSortKey;
  sortKey: ReservationSortKey;
  sortDirection: "asc" | "desc";
  onSortChange: (key: ReservationSortKey) => void;
}) {
  const isActive = sortKey === column;
  const suffix = isActive ? (sortDirection === "asc" ? " ↑" : " ↓") : "";

  return (
    <button className={`sort-button${isActive ? " active" : ""}`} type="button" onClick={() => onSortChange(column)}>
      {label}
      {suffix}
    </button>
  );
}

export function ReservationTable({ rows, sortKey, sortDirection, onSortChange }: ReservationTableProps) {
  return (
    <section className="card">
      <div className="section-head reservation-table-head">
        <div>
          <h4>Reservation Details</h4>
        </div>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>
              <SortButton
                label="Company"
                column="company_name"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th>
              <SortButton
                label="Reservation Status"
                column="request_status"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th className="num">
              <SortButton
                label="Reserved Bags"
                column="effective_bags"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th className="num">
              <SortButton
                label="Reserved KG"
                column="reserved_kg"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th className="num">
              <SortButton
                label="Reserved Value"
                column="reserved_value_gbp"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th>
              <SortButton
                label="Landing Status"
                column="landing_status"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th>
              <SortButton
                label="Landing Date"
                column="landing_date"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th>
              <SortButton
                label="Warehouse"
                column="warehouse"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
            <th>
              <SortButton
                label="Reservation Key"
                column="reservation_key"
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.reservation_key}-${row.product_reference}-${row.id_request || ""}`}>
              <td>
                <strong>{row.company_name}</strong>
              </td>
              <td>
                <span className={getStatusChipClass(row.request_status)}>{row.request_status}</span>
              </td>
              <td className="num">{row.effective_bags ?? row.bags ?? row.bags_remaining ?? "-"}</td>
              <td className="num">{row.reserved_kg}</td>
              <td className="num">{row.reserved_value_gbp?.toFixed(2) ?? "-"}</td>
              <td>
                <span className={getStatusChipClass(row.landing_status || "Unknown")}>{row.landing_status || "-"}</span>
              </td>
              <td>{row.landing_date || "-"}</td>
              <td>{row.warehouse || "-"}</td>
              <td>{formatReservationKey(row.reservation_key)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 ? <p>No reservation rows match the current filters.</p> : null}
    </section>
  );
}

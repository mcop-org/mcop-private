import type { ActionQueueChartRow, ActionQueueSummary } from "../../lib/contracts";
import { formatCount, formatMoney, getStatusChipClass } from "../../lib/presentation";

type ActionQueueSummaryCardsProps = {
  summary: ActionQueueSummary;
  actionBucketCounts: ActionQueueChartRow[];
  openBagsByExpiryBucket: ActionQueueChartRow[];
  topLandedReferences: {
    metric?: string;
    metric_label?: string;
    status?: string;
    rows?: ActionQueueChartRow[];
  };
};

function valueOrUnavailable(value: unknown, available: unknown) {
  if (!available) {
    return "Unavailable";
  }
  return typeof value === "number" ? formatMoney(value) : "Unavailable";
}

function renderSimpleChart(
  rows: ActionQueueChartRow[],
  labelKey: string,
  valueKey: string,
  emptyMessage: string,
  formatter: (value: number) => string,
) {
  if (!rows.length) {
    return <div className="chart-empty-inline">{emptyMessage}</div>;
  }

  const maxValue = rows.reduce((current, row) => {
    const next = Number(row[valueKey] || 0);
    return next > current ? next : current;
  }, 0);

  return (
    <div className="chart-list-inline">
      {rows.map((row, index) => {
        const value = Number(row[valueKey] || 0);
        const width = maxValue > 0 ? `${Math.max((value / maxValue) * 100, 8)}%` : "8%";
        return (
          <div className="chart-row-inline" key={`${labelKey}-${index}`}>
            <div className="chart-row-head">
              <span className={labelKey === "action_bucket" ? getStatusChipClass(row[labelKey] || "Unknown") : "chart-inline-label"}>
                {String(row[labelKey] || "-")}
              </span>
              <strong>{formatter(value)}</strong>
            </div>
            <div className="chart-track-inline">
              <div className="chart-fill-inline" style={{ width }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ActionQueueSummaryCards({
  summary,
  actionBucketCounts,
  openBagsByExpiryBucket,
  topLandedReferences,
}: ActionQueueSummaryCardsProps) {
  const topReferenceRows = topLandedReferences.rows || [];
  const topReferenceMetric = topLandedReferences.metric_label || "Landed Not Released Value";
  const topReferenceValueKey = topLandedReferences.metric === "open_bags" ? "open_bags" : "remaining_value_gbp";

  return (
    <>
      <div className="card-grid action-kpi-grid-app">
        <section className="card stat-card-strong">
          <span className="stat-label">Open Reservations</span>
          <strong>{formatCount(Number(summary.open_reservations || 0))}</strong>
        </section>
        <section className="card stat-card-strong">
          <span className="stat-label">Open Reserved Bags</span>
          <strong>{formatCount(Number(summary.open_reserved_bags || 0))}</strong>
          <span className="stat-label">
            {formatCount(Number(summary.open_reserved_bags_landed || 0))} landed
          </span>
          <span className="stat-label">
            {formatCount(Number(summary.open_reserved_bags_incoming || 0))} incoming
          </span>
        </section>
        <section className="card stat-card-strong">
          <span className="stat-label">Near-Expiry Reservations</span>
          <strong>{formatCount(Number(summary.near_expiry_reservations || 0))}</strong>
          <span className="stat-label">
            {formatCount(Number(summary.near_expiry_rows || 0))} rows within{" "}
            {formatCount(Number(summary.near_expiry_threshold_days || 0))} days
          </span>
        </section>
        <section className="card stat-card-strong">
          <span className="stat-label">Breached Reservations</span>
          <strong>{formatCount(Number(summary.breached_reservations || 0))}</strong>
        </section>
        <section className="card stat-card-strong">
          <span className="stat-label">Open Reserved Value</span>
          <strong>
            {valueOrUnavailable(summary.open_reserved_value_gbp, summary.open_reserved_value_available)}
          </strong>
          <span className="stat-label">
            Landed:{" "}
            {valueOrUnavailable(
              summary.open_reserved_value_landed_gbp,
              summary.open_reserved_value_landed_available,
            )}
          </span>
          <span className="stat-label">
            Incoming:{" "}
            {valueOrUnavailable(
              summary.open_reserved_value_incoming_gbp,
              summary.open_reserved_value_incoming_available,
            )}
          </span>
        </section>
        <section className="card stat-card-strong">
          <span className="stat-label">Open Exposure Reservations</span>
          <strong>{formatCount(Number(summary.open_exposure_reservations || 0))}</strong>
        </section>
        <section className="card stat-card-strong">
          <span className="stat-label">Action Now Reservations</span>
          <strong>{formatCount(Number(summary.action_now_reservations || 0))}</strong>
        </section>
      </div>

      <section className="card">
        <div className="section-head">
          <div>
            <h4>Reservation Risk / Action Queue Charts</h4>
          </div>
        </div>
        <div className="card-grid action-chart-grid-app">
          <section className="stat-card">
            <h4>Action Bucket Rows</h4>
            <p>Shows the active reservation queue by follow-up priority bucket.</p>
            {renderSimpleChart(
              actionBucketCounts,
              "action_bucket",
              "row_count",
              "No open reservation exposure in the current view.",
              (value) => formatCount(value),
            )}
          </section>
          <section className="stat-card">
            <h4>Open Bags by Expiry Bucket</h4>
            <p>Shows open bags split between breached, near-expiry, longer-dated, and expiry-unknown reservations.</p>
            {renderSimpleChart(
              openBagsByExpiryBucket,
              "expiry_bucket",
              "open_bags",
              "No open reservation exposure in the current view.",
              (value) => formatCount(value),
            )}
          </section>
          <section className="stat-card">
            <h4>Top References Not Released Yet</h4>
            <p>{topLandedReferences.status || "No landed open reservation references in the current view."}</p>
            {renderSimpleChart(
              topReferenceRows,
              "product_reference",
              topReferenceValueKey,
              "No landed open reservation references in the current view.",
              (value) =>
                topReferenceValueKey === "open_bags"
                  ? formatCount(value)
                  : formatMoney(value),
            )}
            <p className="chart-metric-copy">{topReferenceMetric}</p>
          </section>
        </div>
      </section>
    </>
  );
}

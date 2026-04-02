import type {
  ClientIntelligenceChartRow,
  ClientIntelligenceConcentrationRow,
} from "../../lib/contracts";
import { formatCompactMoney } from "../../lib/presentation";

function barWidth(value: number, maxValue: number) {
  if (!maxValue || maxValue <= 0) {
    return "0%";
  }
  return `${Math.max(8, Math.round((value / maxValue) * 100))}%`;
}

type ClientIntelligenceChartsProps = {
  topExposure: ClientIntelligenceChartRow[];
  concentration: ClientIntelligenceConcentrationRow[];
};

export function ClientIntelligenceCharts({
  topExposure,
  concentration,
}: ClientIntelligenceChartsProps) {
  const maxExposureValue = Math.max(...topExposure.map((row) => Number(row.reserved_value_gbp || 0)), 0);

  const groupedConcentration = topExposure.map((clientRow) => ({
    clientKey: `${clientRow.company_name}__${clientRow.client_id}`,
    company_name: clientRow.company_name,
    client_id: clientRow.client_id,
    total_value_gbp: clientRow.reserved_value_gbp,
    rows: concentration.filter(
      (row) =>
        row.company_name === clientRow.company_name &&
        row.client_id === clientRow.client_id,
    ),
  }));

  return (
    <section className="card-grid two-up client-chart-grid">
      <article className="card">
        <div className="section-head">
          <div>
            <div className="eyebrow">Client Intelligence Chart</div>
            <h4>Top Clients by Recorded Reservation Value</h4>
            <p className="meta-note">Ranks clients by recorded reservation value for the selected request-date range.</p>
          </div>
        </div>
        {topExposure.length ? (
          <div className="client-bar-list">
            {topExposure.map((row) => (
              <div className="client-bar-row" key={`${row.company_name}-${row.client_id}`}>
                <div className="client-bar-copy">
                  <strong>{row.company_name || row.client_id || "-"}</strong>
                  <span className="meta-note">{row.client_id || "No client ID"}</span>
                </div>
                <div className="client-bar-track">
                  <div
                    className="client-bar-fill"
                    style={{ width: barWidth(Number(row.reserved_value_gbp || 0), maxExposureValue) }}
                  />
                </div>
                <div className="client-bar-value">{formatCompactMoney(Number(row.reserved_value_gbp || 0))}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card-empty">No client activity for the selected date range.</div>
        )}
      </article>
      <article className="card">
        <div className="section-head">
          <div>
            <div className="eyebrow">Client Intelligence Chart</div>
            <h4>Recorded Reservation Value by Client and Reference</h4>
            <p className="meta-note">
              Shows how recorded reservation value is distributed across product references for the selected date range.
            </p>
          </div>
        </div>
        {groupedConcentration.some((row) => row.rows.length > 0) ? (
          <div className="client-stack-list">
            {groupedConcentration.map((row) => (
              <div className="client-stack-row" key={row.clientKey}>
                <div className="client-stack-copy">
                  <strong>{row.company_name || row.client_id || "-"}</strong>
                  <span className="meta-note">{formatCompactMoney(Number(row.total_value_gbp || 0))}</span>
                </div>
                <div className="client-stack-track">
                  {row.rows.map((segment) => {
                    const width = row.total_value_gbp > 0
                      ? `${Math.max(6, Math.round((Number(segment.reserved_value_gbp || 0) / row.total_value_gbp) * 100))}%`
                      : "0%";
                    return (
                      <div
                        className="client-stack-segment"
                        key={`${row.clientKey}-${segment.product_reference}`}
                        style={{ width }}
                        title={`${segment.product_reference}: ${formatCompactMoney(Number(segment.reserved_value_gbp || 0))}`}
                      >
                        <span>{segment.product_reference}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card-empty">No client concentration data for the selected date range.</div>
        )}
      </article>
    </section>
  );
}

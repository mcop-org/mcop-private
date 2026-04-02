import { useDeferredValue, useMemo } from "react";
import { LandedStockCharts } from "../components/landed_stock/LandedStockCharts";
import { LandedStockFilters } from "../components/landed_stock/LandedStockFilters";
import { LandedStockSummaryCards } from "../components/landed_stock/LandedStockSummaryCards";
import { LandedStockTable } from "../components/landed_stock/LandedStockTable";
import { getLandedStockIntelligenceReadModel } from "../lib/api";
import { useAsyncData } from "../lib/query";
import { useSessionStorageState } from "../lib/sessionState";

const LANDED_STOCK_PAGE_STATE_KEY = "mcop-advanced-ui:landed-stock";

type LandedStockPageState = {
  search: string;
  warehouse: string;
  agingBucket: string;
  dataStatus: string;
};

const INITIAL_LANDED_STOCK_PAGE_STATE: LandedStockPageState = {
  search: "",
  warehouse: "",
  agingBucket: "",
  dataStatus: "",
};

export function LandedStockIntelligencePage() {
  const { data, error, loading } = useAsyncData(getLandedStockIntelligenceReadModel, []);
  const { state, setState, resetState } = useSessionStorageState<LandedStockPageState>(
    LANDED_STOCK_PAGE_STATE_KEY,
    INITIAL_LANDED_STOCK_PAGE_STATE,
  );
  const { search, warehouse, agingBucket, dataStatus } = state;
  const deferredSearch = useDeferredValue(search);

  const rows = data?.details || [];
  const filteredRows = useMemo(() => {
    const searchValue = deferredSearch.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesSearch =
        !searchValue ||
        [
          row.product_reference,
          row.product_id,
          row.warehouse,
          row.data_status,
          row.aging_bucket,
        ]
          .join(" ")
          .toLowerCase()
          .includes(searchValue);
      const matchesWarehouse = !warehouse || row.warehouse === warehouse;
      const matchesAgingBucket = !agingBucket || row.aging_bucket === agingBucket;
      const matchesDataStatus = !dataStatus || row.data_status === dataStatus;
      return matchesSearch && matchesWarehouse && matchesAgingBucket && matchesDataStatus;
    });
  }, [agingBucket, dataStatus, deferredSearch, rows, warehouse]);

  function handleReset() {
    resetState(INITIAL_LANDED_STOCK_PAGE_STATE);
  }

  return (
    <section className="page">
      <div className="page-header">
        <h3>Landed Stock Intelligence</h3>
        <p>Landed-only operational view of unsold stock, aging exposure, and current warehouse concentration.</p>
      </div>
      {loading ? <div className="card">Loading landed stock read-model...</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      {data ? (
        <>
          <LandedStockSummaryCards summary={data.summary} />
          <LandedStockFilters
            search={search}
            warehouse={warehouse}
            agingBucket={agingBucket}
            dataStatus={dataStatus}
            warehouses={data.filters.warehouses}
            agingBuckets={data.filters.aging_buckets}
            dataStatuses={data.filters.data_statuses}
            onSearchChange={(value) => setState((current) => ({ ...current, search: value }))}
            onWarehouseChange={(value) => setState((current) => ({ ...current, warehouse: value }))}
            onAgingBucketChange={(value) => setState((current) => ({ ...current, agingBucket: value }))}
            onDataStatusChange={(value) => setState((current) => ({ ...current, dataStatus: value }))}
            onReset={handleReset}
          />
          <LandedStockCharts
            aging={data.aging}
            warehouseExposure={data.warehouse_exposure}
            referenceExposure={data.reference_exposure}
          />
          <LandedStockTable rows={filteredRows} />
        </>
      ) : null}
    </section>
  );
}

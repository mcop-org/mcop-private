import { useDeferredValue, useState } from "react";
import { ActionQueueFilters } from "../components/action_queue/ActionQueueFilters";
import { ExpiredDraftReviewSection } from "../components/action_queue/ExpiredDraftReviewSection";
import { ActionQueueSummaryCards } from "../components/action_queue/ActionQueueSummaryCards";
import { ActionQueueTable } from "../components/action_queue/ActionQueueTable";
import type { ActionQueueChartRow, ActionQueueDetailRow } from "../lib/contracts";
import { getActionQueueReadModel } from "../lib/api";
import { useAsyncData } from "../lib/query";

function deriveActionBucketCounts(rows: ActionQueueDetailRow[]): ActionQueueChartRow[] {
  const orderedBuckets = [
    "Breached",
    "Near Expiry",
    "Landed Not Approved",
    "Landed Not Released",
    "Open Exposure",
  ];
  return orderedBuckets.map((bucket) => ({
    action_bucket: bucket,
    row_count: rows.filter((row) => row.action_bucket === bucket).length,
  }));
}

function deriveOpenBagsByExpiryBucket(rows: ActionQueueDetailRow[]): ActionQueueChartRow[] {
  const buckets = new Map<string, number>([
    ["Breached", 0],
    ["0-7 days", 0],
    ["8+ days", 0],
    ["No expiry data", 0],
  ]);

  for (const row of rows) {
    const bags = typeof row.bags_remaining === "number" ? row.bags_remaining : 0;
    if (typeof row.days_to_expiry !== "number") {
      buckets.set("No expiry data", (buckets.get("No expiry data") || 0) + bags);
      continue;
    }
    if (row.days_to_expiry < 0) {
      buckets.set("Breached", (buckets.get("Breached") || 0) + bags);
      continue;
    }
    if (row.days_to_expiry <= 7) {
      buckets.set("0-7 days", (buckets.get("0-7 days") || 0) + bags);
      continue;
    }
    buckets.set("8+ days", (buckets.get("8+ days") || 0) + bags);
  }

  return [...buckets.entries()].map(([expiry_bucket, open_bags]) => ({ expiry_bucket, open_bags }));
}

function deriveDistinctRowValues(
  rows: ActionQueueDetailRow[],
  key: "action_bucket" | "landing_status" | "data_status",
): string[] {
  return [...new Set(
    rows
      .map((row) => String(row[key] || "").trim())
      .filter(Boolean),
  )].sort((left, right) => left.localeCompare(right, "en", { sensitivity: "base" }));
}

export function ActionQueuePage() {
  const { data, error, loading } = useAsyncData(getActionQueueReadModel, []);
  const [search, setSearch] = useState("");
  const [actionBucket, setActionBucket] = useState("");
  const [landingStatus, setLandingStatus] = useState("");
  const [dataStatus, setDataStatus] = useState("");
  const deferredSearch = useDeferredValue(search);

  const details = (data?.details || []).filter((row) => {
    const searchValue = deferredSearch.trim().toLowerCase();
    const matchesSearch =
      !searchValue ||
      [
        row.company_name,
        row.client_id,
        row.product_reference,
        row.reservation_key,
        row.warehouse,
      ]
        .join(" ")
        .toLowerCase()
        .includes(searchValue);
    const matchesBucket = !actionBucket || row.action_bucket === actionBucket;
    const matchesLanding = !landingStatus || row.landing_status === landingStatus;
    const matchesDataStatus = !dataStatus || row.data_status === dataStatus;
    return matchesSearch && matchesBucket && matchesLanding && matchesDataStatus;
  });

  const actionBucketCounts = data?.action_bucket_counts?.length
    ? data.action_bucket_counts
    : deriveActionBucketCounts(details);
  const openBagsByExpiryBucket = data?.open_bags_by_expiry_bucket?.length
    ? data.open_bags_by_expiry_bucket
    : deriveOpenBagsByExpiryBucket(details);
  const actionBucketOptions = deriveDistinctRowValues(data?.details || [], "action_bucket");
  const landingStatusOptions = deriveDistinctRowValues(data?.details || [], "landing_status");
  const dataStatusOptions = deriveDistinctRowValues(data?.details || [], "data_status");

  function handleReset() {
    setSearch("");
    setActionBucket("");
    setLandingStatus("");
    setDataStatus("");
  }

  return (
    <section className="page">
      <div className="page-header">
        <h3>Reservation Risk / Action Queue</h3>
        <p>Operational queue for open reservation exposure, expiry risk, landed-not-released balances, and follow-up priority.</p>
      </div>
      {loading ? <div className="card">Loading action queue read-model...</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      {data ? (
        <>
          <ActionQueueSummaryCards
            summary={data.summary}
            actionBucketCounts={actionBucketCounts}
            openBagsByExpiryBucket={openBagsByExpiryBucket}
            topLandedReferences={data.top_landed_references}
          />
          <ActionQueueFilters
            search={search}
            actionBucket={actionBucket}
            landingStatus={landingStatus}
            dataStatus={dataStatus}
            actionBuckets={actionBucketOptions}
            landingStatuses={landingStatusOptions}
            dataStatuses={dataStatusOptions}
            onSearchChange={setSearch}
            onActionBucketChange={setActionBucket}
            onLandingStatusChange={setLandingStatus}
            onDataStatusChange={setDataStatus}
            onReset={handleReset}
          />
          <ActionQueueTable rows={details} />
          <ExpiredDraftReviewSection workflow={data.expired_draft_workflow} />
        </>
      ) : null}
    </section>
  );
}

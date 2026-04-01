import { useDeferredValue, useEffect, useState } from "react";
import { ReservationFilters } from "../components/reservations/ReservationFilters";
import { ReservationSummaryCards } from "../components/reservations/ReservationSummaryCards";
import {
  ReservationTable,
  type ReservationSortKey,
} from "../components/reservations/ReservationTable";
import { getReservationReadModel } from "../lib/api";
import { useAsyncData } from "../lib/query";

function compareValues(left: unknown, right: unknown) {
  const leftNumber = Number(left);
  const rightNumber = Number(right);
  if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
    return leftNumber - rightNumber;
  }
  return String(left ?? "").localeCompare(String(right ?? ""), "en", { sensitivity: "base" });
}

export function ReservationIntelligencePage() {
  const { data, error, loading } = useAsyncData(getReservationReadModel, []);
  const [selectedReference, setSelectedReference] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<ReservationSortKey>("company_name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    if (!data || selectedReference !== null) {
      return;
    }
    setSelectedReference(data.default_reference || "");
  }, [data, selectedReference]);

  const normalizedSelectedReference = selectedReference ?? "";
  const referenceOptions = data?.reference_options || [];
  const validReferences = new Set(referenceOptions.map((row) => row.product_reference));
  const scopedReference =
    normalizedSelectedReference && validReferences.has(normalizedSelectedReference)
      ? normalizedSelectedReference
      : "";
  const selectedSummary = data?.summary.find((row) => row.product_reference === scopedReference);

  const details = (data?.details || [])
    .filter((row) => row.product_reference === scopedReference)
    .filter((row) => {
      const searchValue = deferredSearch.trim().toLowerCase();
      if (!searchValue) {
        return true;
      }
      const haystack = [
        row.company_name,
        row.request_status,
        row.warehouse,
        row.reservation_key,
        row.client_id,
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(searchValue);
    })
    .sort((left, right) => {
      const direction = sortDirection === "asc" ? 1 : -1;
      const primary = compareValues(left[sortKey], right[sortKey]);
      if (primary !== 0) {
        return primary * direction;
      }
      return compareValues(left.id_request, right.id_request);
    });

  const selectedReferenceStatus =
    referenceOptions.find((row) => row.product_reference === scopedReference)?.landing_status || "Unknown";

  function handleSortChange(nextKey: ReservationSortKey) {
    if (sortKey === nextKey) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(nextKey);
    setSortDirection("asc");
  }

  function handleReset() {
    setSelectedReference("");
    setSearch("");
    setSortKey("company_name");
    setSortDirection("asc");
  }

  return (
    <section className="page">
      <div className="page-header">
        <h3>Reservation Intelligence</h3>
        <p>Trusted reservation view with per-reference scoping preserved in the app layer.</p>
      </div>
      {loading ? <div className="card">Loading reservation read-model...</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      {data ? (
        <>
          <ReservationFilters
            selectedReference={normalizedSelectedReference}
            referenceOptions={referenceOptions}
            search={search}
            selectedReferenceStatus={selectedReferenceStatus}
            onReferenceChange={setSelectedReference}
            onSearchChange={setSearch}
            onReset={handleReset}
          />
          <ReservationSummaryCards
            snapshotDate={data.snapshot_date}
            summary={selectedSummary}
            rows={details}
          />
          <ReservationTable
            rows={details}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSortChange={handleSortChange}
          />
        </>
      ) : null}
    </section>
  );
}

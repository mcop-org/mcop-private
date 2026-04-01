import { useEffect, useMemo, useState } from "react";
import { ProductReferenceDetailTable } from "../components/product_reference/ProductReferenceDetailTable";
import { ProductReferenceSelector } from "../components/product_reference/ProductReferenceSelector";
import { ProductReferenceSummaryCards } from "../components/product_reference/ProductReferenceSummaryCards";
import type { ProductLandingProfileRow } from "../lib/contracts";
import { getProductReferenceIntelligenceReadModel } from "../lib/api";
import { useAsyncData } from "../lib/query";

function detailSort(left: ProductLandingProfileRow, right: ProductLandingProfileRow) {
  const statusRank = (row: ProductLandingProfileRow) => {
    const landingStatus = String(row.landing_status || "").trim().toLowerCase();
    const availableBags = typeof row.bags_available === "number" ? row.bags_available : null;
    if (landingStatus === "landed" && availableBags !== null && availableBags > 0) {
      return 0;
    }
    if (landingStatus === "landed") {
      return 1;
    }
    if (landingStatus === "incoming") {
      return 2;
    }
    return 3;
  };

  const rankDiff = statusRank(left) - statusRank(right);
  if (rankDiff !== 0) {
    return rankDiff;
  }
  const landingDateDiff = String(left.landing_date || "").localeCompare(String(right.landing_date || ""), "en", {
    sensitivity: "base",
  });
  if (landingDateDiff !== 0) {
    return landingDateDiff;
  }
  return String(left.product_id || "").localeCompare(String(right.product_id || ""), "en", {
    sensitivity: "base",
  });
}

export function ProductReferenceIntelligencePage() {
  const { data, error, loading } = useAsyncData(getProductReferenceIntelligenceReadModel, []);
  const [selectedReferenceInput, setSelectedReferenceInput] = useState("");
  const [hasInitializedSelection, setHasInitializedSelection] = useState(false);

  useEffect(() => {
    if (!data) {
      return;
    }
    if (hasInitializedSelection) {
      return;
    }
    setSelectedReferenceInput(data.default_reference || "");
    setHasInitializedSelection(true);
  }, [data, hasInitializedSelection]);

  const validOptions = useMemo(
    () => new Set((data?.reference_options || []).map((row) => row.product_reference)),
    [data],
  );

  const normalizedSelectedReference =
    selectedReferenceInput && validOptions.has(selectedReferenceInput) ? selectedReferenceInput : "";

  const selectedSummary =
    data?.summary.find((row) => row.product_reference === normalizedSelectedReference) || null;

  const detailRows = useMemo(
    () =>
      (data?.landing_profile || [])
        .filter((row) => row.product_reference === normalizedSelectedReference)
        .sort(detailSort),
    [data, normalizedSelectedReference],
  );

  function handleReset() {
    setSelectedReferenceInput("");
  }

  return (
    <section className="page">
      <div className="page-header">
        <h3>Product Reference Intelligence</h3>
        <p>
          Stock-only view of whether the selected reference looks early-stage, balanced, or at risk of landed build-up.
        </p>
      </div>
      {loading ? <div className="card">Loading product reference read-model...</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      {data ? (
        <>
          <ProductReferenceSelector
            inputValue={selectedReferenceInput}
            selectedReference={normalizedSelectedReference}
            referenceOptions={data.reference_options}
            onReferenceChange={setSelectedReferenceInput}
            onReset={handleReset}
          />
          <ProductReferenceSummaryCards summary={selectedSummary} />
          <ProductReferenceDetailTable
            rows={detailRows}
            snapshotDate={data.snapshot_date}
            hasSelection={normalizedSelectedReference !== ""}
          />
        </>
      ) : null}
    </section>
  );
}

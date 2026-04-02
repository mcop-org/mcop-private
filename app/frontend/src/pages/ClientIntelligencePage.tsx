import { useDeferredValue, useMemo } from "react";
import { ClientIntelligenceCharts } from "../components/client_intelligence/ClientIntelligenceCharts";
import { ClientIntelligenceFilters } from "../components/client_intelligence/ClientIntelligenceFilters";
import { ClientIntelligenceSummaryCards } from "../components/client_intelligence/ClientIntelligenceSummaryCards";
import { ClientIntelligenceTable } from "../components/client_intelligence/ClientIntelligenceTable";
import { getClientIntelligenceReadModel } from "../lib/api";
import type {
  ClientIntelligenceActivityRow,
  ClientIntelligenceChartRow,
  ClientIntelligenceConcentrationRow,
  ClientIntelligenceDetailRow,
  ClientIntelligenceSummary,
} from "../lib/contracts";
import { useAsyncData } from "../lib/query";
import { useSessionStorageState } from "../lib/sessionState";

const CLIENT_INTELLIGENCE_PAGE_STATE_KEY = "mcop-advanced-ui:client-intelligence";

type ClientIntelligencePageState = {
  datePreset: string;
  dateFrom: string;
  dateTo: string;
  search: string;
  concentration: string;
};

const INITIAL_CLIENT_INTELLIGENCE_PAGE_STATE: ClientIntelligencePageState = {
  datePreset: "all",
  dateFrom: "",
  dateTo: "",
  search: "",
  concentration: "all",
};

type ClientMetrics = {
  summary: ClientIntelligenceSummary & {
    concentration_top_five_share: number | null;
    concentration_top_ten_share: number | null;
    concentration_rest_share: number | null;
    concentration_share_available: boolean;
  };
  details: ClientIntelligenceDetailRow[];
  topExposure: ClientIntelligenceChartRow[];
  concentration: ClientIntelligenceConcentrationRow[];
};

function normaliseIsoDate(value: string) {
  const text = value.trim();
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : "";
}

function dateFromIso(value: string) {
  const normalized = normaliseIsoDate(value);
  if (!normalized) {
    return null;
  }
  const date = new Date(`${normalized}T00:00:00.000Z`);
  return Number.isNaN(date.valueOf()) ? null : date;
}

function isoFromDate(value: Date) {
  return value.toISOString().slice(0, 10);
}

function addDays(value: string, days: number) {
  const anchor = dateFromIso(value);
  if (!anchor) {
    return "";
  }
  const next = new Date(anchor);
  next.setUTCDate(next.getUTCDate() + days);
  return isoFromDate(next);
}

function financialYearStart(value: string) {
  const anchor = dateFromIso(value);
  if (!anchor) {
    return "";
  }
  const year = anchor.getUTCMonth() >= 7 ? anchor.getUTCFullYear() : anchor.getUTCFullYear() - 1;
  return isoFromDate(new Date(Date.UTC(year, 7, 1)));
}

function monthStart(value: string) {
  const anchor = dateFromIso(value);
  if (!anchor) {
    return "";
  }
  return isoFromDate(new Date(Date.UTC(anchor.getUTCFullYear(), anchor.getUTCMonth(), 1)));
}

function currentClientDateRange(
  snapshotDate: string,
  preset: string,
  dateFrom: string,
  dateTo: string,
) {
  const anchor = normaliseIsoDate(snapshotDate);
  if (preset === "all") {
    return { from: "", to: "", anchored: false };
  }
  if (preset === "custom") {
    const from = normaliseIsoDate(dateFrom);
    const to = normaliseIsoDate(dateTo);
    return {
      from,
      to,
      anchored: Boolean(from || to),
    };
  }
  if (!anchor) {
    return { from: "", to: "", anchored: false };
  }
  if (preset === "last-30") {
    return { from: addDays(anchor, -29), to: anchor, anchored: true };
  }
  if (preset === "last-90") {
    return { from: addDays(anchor, -89), to: anchor, anchored: true };
  }
  if (preset === "month-to-date") {
    return { from: monthStart(anchor), to: anchor, anchored: true };
  }
  if (preset === "financial-year-to-date") {
    return { from: financialYearStart(anchor), to: anchor, anchored: true };
  }
  return { from: "", to: "", anchored: false };
}

function aggregateClientMetrics(rows: ClientIntelligenceActivityRow[]): ClientMetrics {
  if (!rows.length) {
    return {
      summary: {
        clients_with_current_exposure: 0,
        total_current_reserved_value_gbp: 0,
        total_current_reserved_value_available: true,
        largest_client_company_name: "",
        largest_client_id: "",
        largest_client_reserved_value_gbp: 0,
        largest_client_reserved_value_available: true,
        clients_concentrated_in_one_reference: 0,
        concentration_top_five_share: null,
        concentration_top_ten_share: null,
        concentration_rest_share: null,
        concentration_share_available: false,
      },
      details: [],
      topExposure: [],
      concentration: [],
    };
  }

  const clientGroups = new Map<string, ClientIntelligenceActivityRow[]>();
  for (const row of rows) {
    const clientKey = String(row.client_key || row.client_id || row.company_name || "").trim();
    if (!clientKey) {
      continue;
    }
    const group = clientGroups.get(clientKey) || [];
    group.push(row);
    clientGroups.set(clientKey, group);
  }

  const details: ClientIntelligenceDetailRow[] = [];
  const concentration: ClientIntelligenceConcentrationRow[] = [];

  for (const [clientKey, group] of [...clientGroups.entries()].sort((left, right) =>
    left[0].localeCompare(right[0], "en", { sensitivity: "base" }),
  )) {
    const clientId = String(group[0]?.client_id || "").trim();
    const companyCandidates = [...new Set(group.map((row) => String(row.company_name || "").trim()).filter(Boolean))]
      .sort((left, right) => left.localeCompare(right, "en", { sensitivity: "base" }));
    const companyName = companyCandidates[0] || clientId || clientKey;
    const reservationRowCount = group.length;
    const reservedBags = group.reduce((sum, row) => sum + Number(row.effective_bags || 0), 0);
    const reservedKg = group.reduce((sum, row) => sum + Number(row.reserved_kg || 0), 0);
    const reservedValue = group.reduce((sum, row) => sum + Number(row.reserved_value_gbp || 0), 0);
    const valueAvailable = group.every((row) => Boolean(row.reserved_value_available));
    const distinctReferenceCount = new Set(
      group.map((row) => String(row.product_reference || "").trim()).filter(Boolean),
    ).size;
    const landingStatuses = [...new Set(
      group
        .map((row) => String(row.landing_status || "").trim().toLowerCase())
        .filter((value) => value === "incoming" || value === "landed"),
    )].sort();

    let landingMix = "Unknown";
    if (landingStatuses.length === 1) {
      landingMix = landingStatuses[0].charAt(0).toUpperCase() + landingStatuses[0].slice(1);
    } else if (landingStatuses.length > 1) {
      landingMix = "Mixed";
    }

    const referenceMap = new Map<string, { product_reference: string; reserved_value_gbp: number; reserved_kg: number }>();
    for (const row of group) {
      const reference = String(row.product_reference || "").trim();
      if (!reference) {
        continue;
      }
      const entry = referenceMap.get(reference) || {
        product_reference: reference,
        reserved_value_gbp: 0,
        reserved_kg: 0,
      };
      entry.reserved_value_gbp += Number(row.reserved_value_gbp || 0);
      entry.reserved_kg += Number(row.reserved_kg || 0);
      referenceMap.set(reference, entry);
    }

    const referenceGroups = [...referenceMap.values()].sort((left, right) => {
      const valueDiff = right.reserved_value_gbp - left.reserved_value_gbp;
      if (valueDiff !== 0) {
        return valueDiff;
      }
      const kgDiff = right.reserved_kg - left.reserved_kg;
      if (kgDiff !== 0) {
        return kgDiff;
      }
      return left.product_reference.localeCompare(right.product_reference, "en", { sensitivity: "base" });
    });

    let primaryReference = "";
    let primaryReferenceShare: number | null = null;
    let primaryReferenceShareAvailable = false;
    if (referenceGroups.length) {
      const primaryRow = referenceGroups[0];
      primaryReference = primaryRow.product_reference;
      if (valueAvailable && reservedValue > 0) {
        primaryReferenceShare = Number((primaryRow.reserved_value_gbp / reservedValue).toFixed(4));
        primaryReferenceShareAvailable = true;
      } else if (reservedKg > 0) {
        primaryReferenceShare = Number((primaryRow.reserved_kg / reservedKg).toFixed(4));
        primaryReferenceShareAvailable = true;
      }

      for (const referenceRow of referenceGroups) {
        concentration.push({
          company_name: companyName,
          client_id: clientId,
          product_reference: referenceRow.product_reference,
          reserved_value_gbp: Number(referenceRow.reserved_value_gbp.toFixed(2)),
        });
      }
    }

    details.push({
      company_name: companyName,
      client_id: clientId,
      reservation_row_count: reservationRowCount,
      reserved_bags: Number(reservedBags.toFixed(4)),
      reserved_kg: Number(reservedKg.toFixed(4)),
      reserved_value_gbp: Number(reservedValue.toFixed(2)),
      reserved_value_available: valueAvailable,
      distinct_reference_count: distinctReferenceCount,
      primary_reference: primaryReference,
      primary_reference_share: primaryReferenceShare,
      primary_reference_share_available: primaryReferenceShareAvailable,
      landing_mix: landingMix,
    });
  }

  details.sort((left, right) => {
    const valueDiff = right.reserved_value_gbp - left.reserved_value_gbp;
    if (valueDiff !== 0) {
      return valueDiff;
    }
    const kgDiff = right.reserved_kg - left.reserved_kg;
    if (kgDiff !== 0) {
      return kgDiff;
    }
    const companyDiff = left.company_name.localeCompare(right.company_name, "en", { sensitivity: "base" });
    if (companyDiff !== 0) {
      return companyDiff;
    }
    return left.client_id.localeCompare(right.client_id, "en", { sensitivity: "base" });
  });

  const detailValueByClient = new Map(
    details.map((row) => [`${row.company_name}__${row.client_id}`, row.reserved_value_gbp]),
  );
  concentration.sort((left, right) => {
    const leftClientValue = detailValueByClient.get(`${left.company_name}__${left.client_id}`) || 0;
    const rightClientValue = detailValueByClient.get(`${right.company_name}__${right.client_id}`) || 0;
    const clientValueDiff = rightClientValue - leftClientValue;
    if (clientValueDiff !== 0) {
      return clientValueDiff;
    }
    const companyDiff = left.company_name.localeCompare(right.company_name, "en", { sensitivity: "base" });
    if (companyDiff !== 0) {
      return companyDiff;
    }
    const valueDiff = right.reserved_value_gbp - left.reserved_value_gbp;
    if (valueDiff !== 0) {
      return valueDiff;
    }
    return left.product_reference.localeCompare(right.product_reference, "en", { sensitivity: "base" });
  });

  const rankedClientKeys = new Set(
    details
      .filter((row) => Number(row.reserved_bags || 0) > 0)
      .map((row) => row.client_id.trim() || row.company_name.trim()),
  );
  const rankedValues = details
    .map((row) => Number(row.reserved_value_gbp || 0))
    .filter((value) => Number.isFinite(value) && value > 0);
  const totalReservedValue = Number(
    rows.reduce((sum, row) => sum + Number(row.reserved_value_gbp || 0), 0).toFixed(2),
  );
  const totalValueAvailable = rows.every((row) => Boolean(row.reserved_value_available));

  let concentrationTopFiveShare: number | null = null;
  let concentrationTopTenShare: number | null = null;
  let concentrationRestShare: number | null = null;
  let concentrationShareAvailable = false;
  if (totalValueAvailable && totalReservedValue > 0) {
    const topFiveValue = rankedValues.slice(0, 5).reduce((sum, value) => sum + value, 0);
    const topTenValue = rankedValues.slice(0, 10).reduce((sum, value) => sum + value, 0);
    concentrationTopFiveShare = Number((topFiveValue / totalReservedValue).toFixed(4));
    concentrationTopTenShare = Number((topTenValue / totalReservedValue).toFixed(4));
    concentrationRestShare = Number(
      Math.max(0, (totalReservedValue - topTenValue) / totalReservedValue).toFixed(4),
    );
    concentrationShareAvailable = true;
  }

  return {
    summary: {
      clients_with_current_exposure: rankedClientKeys.size,
      total_current_reserved_value_gbp: totalReservedValue,
      total_current_reserved_value_available: totalValueAvailable,
      largest_client_company_name: details[0]?.company_name || "",
      largest_client_id: details[0]?.client_id || "",
      largest_client_reserved_value_gbp: Number((details[0]?.reserved_value_gbp || 0).toFixed(2)),
      largest_client_reserved_value_available: Boolean(details[0]?.reserved_value_available ?? true),
      clients_concentrated_in_one_reference: details.filter(
        (row) =>
          Boolean(row.primary_reference_share_available) &&
          row.primary_reference_share !== null &&
          Number(row.primary_reference_share || 0) >= 0.8,
      ).length,
      concentration_top_five_share: concentrationTopFiveShare,
      concentration_top_ten_share: concentrationTopTenShare,
      concentration_rest_share: concentrationRestShare,
      concentration_share_available: concentrationShareAvailable,
    },
    details,
    topExposure: details.slice(0, 10).map((row) => ({
      company_name: row.company_name,
      client_id: row.client_id,
      reserved_value_gbp: row.reserved_value_gbp,
    })),
    concentration,
  };
}

export function ClientIntelligencePage() {
  const { data, error, loading } = useAsyncData(getClientIntelligenceReadModel, []);
  const { state, setState, resetState } = useSessionStorageState<ClientIntelligencePageState>(
    CLIENT_INTELLIGENCE_PAGE_STATE_KEY,
    INITIAL_CLIENT_INTELLIGENCE_PAGE_STATE,
  );
  const { datePreset, dateFrom, dateTo, search, concentration } = state;
  const deferredSearch = useDeferredValue(search);

  const filteredActivityRows = useMemo(() => {
    const rows = data?.activity_rows || [];
    const range = currentClientDateRange(data?.snapshot_date || "", datePreset, dateFrom, dateTo);
    if (!range.anchored) {
      return rows;
    }
    return rows.filter((row) => {
      const requestDate = normaliseIsoDate(row.request_date || "");
      if (!requestDate) {
        return false;
      }
      if (range.from && requestDate < range.from) {
        return false;
      }
      if (range.to && requestDate > range.to) {
        return false;
      }
      return true;
    });
  }, [data?.activity_rows, data?.snapshot_date, dateFrom, datePreset, dateTo]);

  const clientMetrics = useMemo(
    () => aggregateClientMetrics(filteredActivityRows),
    [filteredActivityRows],
  );

  const tableRows = useMemo(() => {
    const text = deferredSearch.trim().toLowerCase();
    return clientMetrics.details.filter((row) => {
      const share = Number(row.primary_reference_share || 0);
      const shareAvailable = Boolean(row.primary_reference_share_available);
      if (concentration === "concentrated" && (!shareAvailable || share < 0.8)) {
        return false;
      }
      if (concentration === "multi" && shareAvailable && share >= 0.8) {
        return false;
      }
      if (!text) {
        return true;
      }
      const haystack = [row.company_name, row.client_id, row.primary_reference].join(" ").toLowerCase();
      return haystack.includes(text);
    });
  }, [clientMetrics.details, concentration, deferredSearch]);

  function handleReset() {
    resetState(INITIAL_CLIENT_INTELLIGENCE_PAGE_STATE);
  }

  return (
    <section className="page">
      <div className="page-header">
        <h3>Client Intelligence</h3>
        <p>Reservation activity view, excluding rejected reservations.</p>
      </div>
      {loading ? <div className="card">Loading client intelligence read-model...</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      {data ? (
        <>
          <ClientIntelligenceFilters
            datePreset={datePreset}
            dateFrom={dateFrom}
            dateTo={dateTo}
            search={search}
            concentration={concentration}
            onDatePresetChange={(value) =>
              setState((current) => ({
                ...current,
                datePreset: value,
                ...(value === "custom" ? {} : { dateFrom: "", dateTo: "" }),
              }))
            }
            onDateFromChange={(value) => setState((current) => ({ ...current, dateFrom: value }))}
            onDateToChange={(value) => setState((current) => ({ ...current, dateTo: value }))}
            onSearchChange={(value) => setState((current) => ({ ...current, search: value }))}
            onConcentrationChange={(value) => setState((current) => ({ ...current, concentration: value }))}
            onReset={handleReset}
          />
          <ClientIntelligenceSummaryCards summary={clientMetrics.summary} />
          <ClientIntelligenceCharts
            topExposure={clientMetrics.topExposure}
            concentration={clientMetrics.concentration}
          />
          <ClientIntelligenceTable rows={tableRows} />
        </>
      ) : null}
    </section>
  );
}

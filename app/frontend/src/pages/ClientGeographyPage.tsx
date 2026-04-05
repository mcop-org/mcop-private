import { useEffect, useMemo } from "react";
import { ClientGeographyCharts } from "../components/geography/ClientGeographyCharts";
import { ClientGeographyDetailPanel } from "../components/geography/ClientGeographyDetailPanel";
import { ClientGeographyFilters } from "../components/geography/ClientGeographyFilters";
import { ClientGeographyLocationTable } from "../components/geography/ClientGeographyLocationTable";
import { ClientGeographyMap } from "../components/geography/ClientGeographyMap";
import { ClientGeographySummaryCards } from "../components/geography/ClientGeographySummaryCards";
import { ClientGeographyUnmappedTable } from "../components/geography/ClientGeographyUnmappedTable";
import {
  DEFAULT_CLIENT_GEOGRAPHY_BASEMAP_MODE,
  type ClientGeographyBasemapMode,
} from "../components/geography/clientGeographyBasemap";
import type {
  ClientGeographyActivityRow,
  ClientGeographyLocationRow,
  ClientGeographyMapClientRow,
  ClientGeographySummary,
  ClientGeographyUnmappedClientRow,
} from "../lib/contracts";
import { getClientGeographyReadModel } from "../lib/api";
import { useAsyncData } from "../lib/query";
import { useSessionStorageState } from "../lib/sessionState";

const CLIENT_GEOGRAPHY_PAGE_STATE_KEY = "mcop-advanced-ui:client-geography";

type ClientGeographyPageState = {
  basemapMode: ClientGeographyBasemapMode;
  datePreset: string;
  dateFrom: string;
  dateTo: string;
  country: string;
  city: string;
  exposure: string;
  selectedMarkerId: string;
};

const INITIAL_CLIENT_GEOGRAPHY_PAGE_STATE: ClientGeographyPageState = {
  basemapMode: DEFAULT_CLIENT_GEOGRAPHY_BASEMAP_MODE,
  datePreset: "all",
  dateFrom: "",
  dateTo: "",
  country: "",
  city: "",
  exposure: "all",
  selectedMarkerId: "",
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

function currentGeographyDateRange(
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

function locationKey(row: { country: string; city: string; postcode: string }) {
  return [row.country, row.city, row.postcode].join("||");
}

function unmappedKey(row: { company_name: string; client_id: string; reason?: string; unmapped_reason?: string }) {
  return [
    String(row.client_id || "").trim(),
    String(row.company_name || "").trim(),
    String(row.reason || row.unmapped_reason || "").trim(),
  ].join("||");
}

function buildScopedGeographySummary(
  baseSummary: ClientGeographySummary | undefined,
  scopedActivityRows: ClientGeographyActivityRow[],
  scopedMapClients: ClientGeographyMapClientRow[],
  scopedUnmappedClients: ClientGeographyUnmappedClientRow[],
): ClientGeographySummary {
  const mappedClientIds = new Set(
    scopedActivityRows
      .filter((row) => !String(row.unmapped_reason || "").trim() && String(row.client_id || "").trim())
      .map((row) => String(row.client_id || "").trim()),
  );
  const resolvedClientIds = new Set(
    scopedMapClients
      .map((row) => String(row.client_id || "").trim())
      .filter(Boolean),
  );
  const matchedClientRows = scopedActivityRows.filter((row) => {
    const reason = String(row.unmapped_reason || "").trim();
    return !reason || reason === "Missing delivery geography on clients master row";
  }).length;
  const unmatchedClientRows = scopedActivityRows.length - matchedClientRows;
  const unresolvedMapClients = Math.max(mappedClientIds.size - resolvedClientIds.size, 0);
  const resolvedMapClients = resolvedClientIds.size;
  const mapStatus = resolvedMapClients > 0
    ? `Plotting ${resolvedMapClients} deterministically resolved client markers; ${unresolvedMapClients} mapped clients remain unplotted.`
    : "No deterministically resolved client coordinates are available for plotting.";

  return {
    mapped_clients: mappedClientIds.size,
    unmapped_clients: scopedUnmappedClients.length,
    countries_covered: Number(baseSummary?.countries_covered || 0),
    cities_covered: Number(baseSummary?.cities_covered || 0),
    exposed_client_locations: Number(baseSummary?.exposed_client_locations || 0),
    duplicate_client_ids: Number(baseSummary?.duplicate_client_ids || 0),
    duplicate_client_rows: Number(baseSummary?.duplicate_client_rows || 0),
    matched_client_rows: matchedClientRows,
    unmatched_client_rows: unmatchedClientRows,
    resolved_map_clients: resolvedMapClients,
    unresolved_map_clients: unresolvedMapClients,
    coordinate_conflicts: Number(baseSummary?.coordinate_conflicts || 0),
    map_included: Boolean(baseSummary?.map_included ?? true),
    map_status: mapStatus,
  };
}

function matchesFilters<T extends { country: string; city: string }>(
  row: T,
  country: string,
  city: string,
) {
  if (country && row.country !== country) {
    return false;
  }
  if (city && row.city !== city) {
    return false;
  }
  return true;
}

function matchesExposureOnLocation(row: ClientGeographyLocationRow, exposure: string) {
  if (exposure === "exposed") {
    return Number(row.exposed_client_count || 0) > 0;
  }
  if (exposure === "no-exposure") {
    return Number(row.exposed_client_count || 0) <= 0;
  }
  return true;
}

function matchesExposureOnClient(row: ClientGeographyMapClientRow, exposure: string) {
  if (exposure === "exposed") {
    return Boolean(row.has_exposure);
  }
  if (exposure === "no-exposure") {
    return !row.has_exposure;
  }
  return true;
}

export function ClientGeographyPage() {
  const { data, error, loading } = useAsyncData(getClientGeographyReadModel, []);
  const { state, setState, resetState } = useSessionStorageState<ClientGeographyPageState>(
    CLIENT_GEOGRAPHY_PAGE_STATE_KEY,
    INITIAL_CLIENT_GEOGRAPHY_PAGE_STATE,
  );
  const { basemapMode, datePreset, dateFrom, dateTo, country, city, exposure, selectedMarkerId } = state;

  const dateRange = useMemo(
    () => currentGeographyDateRange(data?.snapshot_date || "", datePreset, dateFrom, dateTo),
    [data?.snapshot_date, dateFrom, datePreset, dateTo],
  );
  const scopedData = useMemo(() => {
    const locations = data?.locations || [];
    const mapClients = data?.map_clients || [];
    const unmappedClients = data?.unmapped_clients || [];
    const hasActivityRowsSource = Boolean(data) && Object.prototype.hasOwnProperty.call(data, "activity_rows");
    const activityRows = data?.activity_rows || [];
    if (!dateRange.anchored) {
      return {
        locations,
        mapClients,
        unmappedClients,
        summary: data?.summary || {
          mapped_clients: 0,
          unmapped_clients: 0,
          countries_covered: 0,
          cities_covered: 0,
          exposed_client_locations: 0,
          duplicate_client_ids: 0,
          duplicate_client_rows: 0,
          matched_client_rows: 0,
          unmatched_client_rows: 0,
          resolved_map_clients: 0,
          unresolved_map_clients: 0,
          coordinate_conflicts: 0,
          map_included: true,
          map_status: "No plotted client markers available.",
        },
      };
    }
    if (!hasActivityRowsSource) {
      return {
        locations,
        mapClients,
        unmappedClients,
        summary: data?.summary || {
          mapped_clients: 0,
          unmapped_clients: 0,
          countries_covered: 0,
          cities_covered: 0,
          exposed_client_locations: 0,
          duplicate_client_ids: 0,
          duplicate_client_rows: 0,
          matched_client_rows: 0,
          unmatched_client_rows: 0,
          resolved_map_clients: 0,
          unresolved_map_clients: 0,
          coordinate_conflicts: 0,
          map_included: true,
          map_status: "No plotted client markers available.",
        },
      };
    }

    const scopedActivityRows = activityRows.filter((row) => {
      const requestDate = normaliseIsoDate(row.request_date || "");
      if (!requestDate) {
        return false;
      }
      if (dateRange.from && requestDate < dateRange.from) {
        return false;
      }
      if (dateRange.to && requestDate > dateRange.to) {
        return false;
      }
      return true;
    });
    const markerIdsInScope = new Set(
      scopedActivityRows
        .map((row) => String(row.client_id || "").trim())
        .filter(Boolean),
    );
    const locationKeysInScope = new Set(
      scopedActivityRows
        .filter((row) => !String(row.unmapped_reason || "").trim())
        .map((row) =>
          locationKey({
            country: String(row.country || "").trim(),
            city: String(row.city || "").trim(),
            postcode: String(row.postcode || "").trim(),
          }),
        )
        .filter((value) => value !== "||"),
    );
    const unmappedKeysInScope = new Set(
      scopedActivityRows
        .filter((row) => String(row.unmapped_reason || "").trim())
        .map((row) => unmappedKey(row)),
    );
    const scopedLocations = locations.filter((row) => locationKeysInScope.has(locationKey(row)));
    const scopedMapClients = mapClients.filter((row) => {
      const markerId = String(row.marker_id || "").trim();
      const clientId = String(row.client_id || "").trim();
      return markerIdsInScope.has(markerId) || markerIdsInScope.has(clientId);
    });
    const scopedUnmappedClients = unmappedClients.filter((row) => unmappedKeysInScope.has(unmappedKey(row)));
    return {
      locations: scopedLocations,
      mapClients: scopedMapClients,
      unmappedClients: scopedUnmappedClients,
      summary: buildScopedGeographySummary(data?.summary, scopedActivityRows, scopedMapClients, scopedUnmappedClients),
    };
  }, [data?.activity_rows, data?.locations, data?.map_clients, data?.summary, data?.unmapped_clients, dateRange]);

  const locations = scopedData.locations;
  const mapClients = scopedData.mapClients;
  const unmappedClients = scopedData.unmappedClients;

  const cityOptions = useMemo(() => {
    const sourceRows = country ? locations.filter((row) => row.country === country) : locations;
    return [...new Set(sourceRows.map((row) => row.city).filter(Boolean))].sort((left, right) =>
      left.localeCompare(right, "en", { sensitivity: "base" }),
    );
  }, [country, locations]);

  const filteredLocations = useMemo(
    () =>
      locations.filter(
        (row) =>
          matchesFilters(row, country, city) &&
          matchesExposureOnLocation(row, exposure),
      ),
    [city, country, exposure, locations],
  );

  const filteredMapClients = useMemo(
    () =>
      mapClients.filter(
        (row) =>
          matchesFilters(row, country, city) &&
          matchesExposureOnClient(row, exposure),
      ),
    [city, country, exposure, mapClients],
  );

  useEffect(() => {
    if (!filteredMapClients.length) {
      if (selectedMarkerId !== "") {
        setState((current) => ({ ...current, selectedMarkerId: "" }));
      }
      return;
    }
    if (filteredMapClients.some((row) => row.marker_id === selectedMarkerId)) {
      return;
    }
    if (selectedMarkerId) {
      setState((current) => ({ ...current, selectedMarkerId: "" }));
      return;
    }
    setState((current) => ({ ...current, selectedMarkerId: filteredMapClients[0].marker_id }));
  }, [filteredMapClients, selectedMarkerId, setState]);

  const selectedClient =
    filteredMapClients.find((row) => row.marker_id === selectedMarkerId) || null;

  function handleResetFilters() {
    resetState(INITIAL_CLIENT_GEOGRAPHY_PAGE_STATE);
  }

  return (
    <section className="page">
      <div className="page-header">
        <h3>Client Geography</h3>
        <p>
          Delivery geography view of mapped clients, exposure, and unresolved records.
        </p>
      </div>
      {loading ? <div className="card">Loading client geography view...</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      {data ? (
        <>
          <ClientGeographyFilters
            countries={[...new Set(locations.map((row) => row.country).filter(Boolean))].sort((left, right) =>
              left.localeCompare(right, "en", { sensitivity: "base" }),
            )}
            cities={cityOptions}
            datePreset={datePreset}
            dateFrom={dateFrom}
            dateTo={dateTo}
            country={country}
            city={city}
            exposure={exposure}
            onDatePresetChange={(value) =>
              setState((current) => ({
                ...current,
                datePreset: value,
                ...(value === "custom" ? {} : { dateFrom: "", dateTo: "" }),
                country: "",
                city: "",
                selectedMarkerId: "",
              }))
            }
            onDateFromChange={(value) =>
              setState((current) => ({
                ...current,
                dateFrom: value,
                selectedMarkerId: "",
              }))
            }
            onDateToChange={(value) =>
              setState((current) => ({
                ...current,
                dateTo: value,
                selectedMarkerId: "",
              }))
            }
            onCountryChange={(value) => {
              setState((current) => ({
                ...current,
                country: value,
                city: "",
                selectedMarkerId: "",
              }));
            }}
            onCityChange={(value) =>
              setState((current) => ({
                ...current,
                city: value,
                selectedMarkerId: "",
              }))
            }
            onExposureChange={(value) =>
              setState((current) => ({
                ...current,
                exposure: value,
                selectedMarkerId: "",
              }))
            }
            onReset={handleResetFilters}
          />
          <ClientGeographySummaryCards
            summary={scopedData.summary}
            filteredLocations={filteredLocations}
          />
          <section className="geography-workspace">
            <div className="card-grid geography-map-layout">
              <ClientGeographyMap
                basemapMode={basemapMode}
                onBasemapModeChange={(value) =>
                  setState((current) => ({
                    ...current,
                    basemapMode: value,
                  }))
                }
                rows={filteredMapClients}
                selectedMarkerId={selectedMarkerId}
                onSelectMarker={(markerId) =>
                  setState((current) => ({
                    ...current,
                    selectedMarkerId: markerId,
                  }))
                }
              />
              <ClientGeographyDetailPanel selectedClient={selectedClient} />
            </div>
          </section>
          <ClientGeographyCharts
            filteredLocations={filteredLocations}
            summary={scopedData.summary}
          />
          <ClientGeographyLocationTable
            rows={filteredLocations}
            selectedClient={selectedClient}
          />
          <ClientGeographyUnmappedTable rows={unmappedClients} />
        </>
      ) : null}
    </section>
  );
}

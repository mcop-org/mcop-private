import { useEffect, useMemo } from "react";
import { ClientGeographyCharts } from "../components/geography/ClientGeographyCharts";
import { ClientGeographyDetailPanel } from "../components/geography/ClientGeographyDetailPanel";
import { ClientGeographyFilters } from "../components/geography/ClientGeographyFilters";
import { ClientGeographyLocationTable } from "../components/geography/ClientGeographyLocationTable";
import { ClientGeographyMap } from "../components/geography/ClientGeographyMap";
import { ClientGeographySummaryCards } from "../components/geography/ClientGeographySummaryCards";
import { ClientGeographyUnmappedTable } from "../components/geography/ClientGeographyUnmappedTable";
import type {
  ClientGeographyLocationRow,
  ClientGeographyMapClientRow,
} from "../lib/contracts";
import { getClientGeographyReadModel } from "../lib/api";
import { useAsyncData } from "../lib/query";
import { useSessionStorageState } from "../lib/sessionState";

const CLIENT_GEOGRAPHY_PAGE_STATE_KEY = "mcop-advanced-ui:client-geography";

type ClientGeographyPageState = {
  country: string;
  city: string;
  exposure: string;
  selectedMarkerId: string;
};

const INITIAL_CLIENT_GEOGRAPHY_PAGE_STATE: ClientGeographyPageState = {
  country: "",
  city: "",
  exposure: "all",
  selectedMarkerId: "",
};

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
  const { country, city, exposure, selectedMarkerId } = state;

  const locations = data?.locations || [];
  const mapClients = data?.map_clients || [];
  const unmappedClients = data?.unmapped_clients || [];

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
          Analytical delivery geography view over trusted client mapping outputs, with unresolved clients kept explicit.
        </p>
      </div>
      {loading ? <div className="card">Loading client geography read-model...</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      {data ? (
        <>
          <ClientGeographyFilters
            countries={data.filters.countries}
            cities={cityOptions}
            country={country}
            city={city}
            exposure={exposure}
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
            summary={data.summary}
            filteredLocations={filteredLocations}
          />
          <div className="card-grid geography-map-layout">
            <ClientGeographyMap
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
          <ClientGeographyCharts
            filteredLocations={filteredLocations}
            summary={data.summary}
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

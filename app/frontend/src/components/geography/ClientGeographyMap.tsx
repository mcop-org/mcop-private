import { useEffect, useMemo, useRef } from "react";
import maplibregl, {
  type ExpressionSpecification,
  type GeoJSONSource,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Feature, FeatureCollection, Point } from "geojson";
import type { ClientGeographyMapClientRow } from "../../lib/contracts";
import {
  CLIENT_GEOGRAPHY_BASEMAPS,
  type ClientGeographyBasemapMode,
  getClientGeographyBasemapStyleUrl,
} from "./clientGeographyBasemap";

type ClientGeographyMapProps = {
  basemapMode: ClientGeographyBasemapMode;
  onBasemapModeChange: (mode: ClientGeographyBasemapMode) => void;
  rows: ClientGeographyMapClientRow[];
  selectedMarkerId: string;
  onSelectMarker: (markerId: string) => void;
};

type MapFeatureProperties = {
  marker_id: string;
  company_name: string;
  client_id: string;
  country: string;
  city: string;
  postcode: string;
  location_label: string;
  coordinate_match_level: string;
  reserved_value_available: boolean;
  reserved_value_gbp: number;
  reserved_bags: number;
  reserved_kg: number;
  has_exposure: boolean;
  distinct_reference_count: number;
  primary_reference: string;
  marker_radius: number;
};

const EMPTY_COLLECTION: FeatureCollection<Point, MapFeatureProperties> = {
  type: "FeatureCollection",
  features: [],
};

const DEFAULT_CENTER: [number, number] = [-1.5, 53.2];
const DEFAULT_ZOOM = 4.2;

function fitMapToFeatures(
  map: maplibregl.Map,
  features: FeatureCollection<Point, MapFeatureProperties>,
  duration: number,
) {
  if (!features.features.length) {
    map.easeTo({ center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM, duration });
    return;
  }

  if (features.features.length === 1) {
    map.easeTo({
      center: features.features[0].geometry.coordinates as [number, number],
      zoom: 8,
      duration,
    });
    return;
  }

  const bounds = new maplibregl.LngLatBounds();
  for (const feature of features.features) {
    bounds.extend(feature.geometry.coordinates as [number, number]);
  }
  map.fitBounds(bounds, { padding: 48, duration, maxZoom: 8.5 });
}

function setClientSourceData(
  map: maplibregl.Map,
  features: FeatureCollection<Point, MapFeatureProperties>,
) {
  const source = map.getSource("clients") as GeoJSONSource | undefined;
  if (!source) {
    return;
  }
  source.setData(features);
}

function setSelectedMarker(map: maplibregl.Map, selectedMarkerId: string) {
  if (!map.getLayer("client-points-selected")) {
    return;
  }
  map.setFilter("client-points-selected", [
    "all",
    ["!", ["has", "point_count"]],
    ["==", ["get", "marker_id"], selectedMarkerId || ""],
  ]);
}

function installClientLayers(
  map: maplibregl.Map,
  onSelectMarker: (markerId: string) => void,
) {
  if (!map.getSource("clients")) {
    map.addSource("clients", {
      type: "geojson",
      data: EMPTY_COLLECTION,
      cluster: true,
      clusterMaxZoom: 8,
      clusterRadius: 42,
    });
  }

  map.addLayer({
    id: "client-clusters",
    type: "circle",
    source: "clients",
    filter: ["has", "point_count"],
    paint: {
      "circle-color": "#5e8793",
      "circle-opacity": 0.88,
      "circle-stroke-color": "#f5f1e8",
      "circle-stroke-width": 2,
      "circle-radius": [
        "step",
        ["get", "point_count"],
        18,
        10,
        22,
        25,
        28,
        50,
        34,
      ],
    },
  });

  map.addLayer({
    id: "client-cluster-count",
    type: "symbol",
    source: "clients",
    filter: ["has", "point_count"],
    layout: {
      "text-field": ["get", "point_count_abbreviated"],
      "text-size": 12,
    },
    paint: {
      "text-color": "#f8fafc",
    },
  });

  map.addLayer({
    id: "client-points",
    type: "circle",
    source: "clients",
    filter: ["all", ["!", ["has", "point_count"]], ["!=", ["get", "marker_id"], ""]],
    paint: {
      "circle-color": [
        "case",
        ["boolean", ["get", "has_exposure"], false],
        "#3c8d9c",
        "#d08a52",
      ],
      "circle-opacity": 0.94,
      "circle-radius": ["get", "marker_radius"] as ExpressionSpecification,
      "circle-stroke-color": "#f7f3ea",
      "circle-stroke-width": 2.4,
    },
  });

  map.addLayer({
    id: "client-points-selected",
    type: "circle",
    source: "clients",
    filter: ["all", ["!", ["has", "point_count"]], ["==", ["get", "marker_id"], ""]],
    paint: {
      "circle-color": [
        "case",
        ["boolean", ["get", "has_exposure"], false],
        "#2d6572",
        "#b56d35",
      ],
      "circle-opacity": 1,
      "circle-radius": ["+", ["get", "marker_radius"], 4] as ExpressionSpecification,
      "circle-stroke-color": "#fffdf8",
      "circle-stroke-width": 3.4,
    },
  });

  map.on("click", "client-clusters", (event) => {
    const feature = event.features?.[0];
    const clusterId = feature?.properties?.cluster_id;
    if (clusterId === undefined || feature?.geometry.type !== "Point") {
      return;
    }
    const source = map.getSource("clients") as GeoJSONSource;
    source.getClusterExpansionZoom(Number(clusterId)).then((zoom) => {
      map.easeTo({
        center: (feature.geometry as Point).coordinates as [number, number],
        zoom,
        duration: 500,
      });
    });
  });

  const selectMarker = (event: maplibregl.MapLayerMouseEvent) => {
    const feature = event.features?.[0];
    const markerId = String(feature?.properties?.marker_id || "");
    if (markerId) {
      onSelectMarker(markerId);
    }
  };

  map.on("click", "client-points", selectMarker);
  map.on("click", "client-points-selected", selectMarker);

  for (const layerId of ["client-clusters", "client-points", "client-points-selected"]) {
    map.on("mouseenter", layerId, () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", layerId, () => {
      map.getCanvas().style.cursor = "";
    });
  }
}

function markerRadius(row: ClientGeographyMapClientRow) {
  if (row.reserved_value_available) {
    const value = Number(row.reserved_value_gbp || 0);
    if (value >= 100_000) {
      return 18;
    }
    if (value >= 50_000) {
      return 16;
    }
    if (value >= 10_000) {
      return 14;
    }
    if (value > 0) {
      return 12;
    }
  }
  const bags = Number(row.reserved_bags || 0);
  if (bags >= 100) {
    return 15;
  }
  if (bags >= 50) {
    return 13;
  }
  if (bags > 0) {
    return 11;
  }
  return 10;
}

function toFeature(row: ClientGeographyMapClientRow): Feature<Point, MapFeatureProperties> {
  return {
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [Number(row.longitude || 0), Number(row.latitude || 0)],
    },
    properties: {
      marker_id: row.marker_id,
      company_name: row.company_name,
      client_id: row.client_id,
      country: row.country,
      city: row.city,
      postcode: row.postcode,
      location_label: row.location_label,
      coordinate_match_level: row.coordinate_match_level,
      reserved_value_available: row.reserved_value_available,
      reserved_value_gbp: Number(row.reserved_value_gbp || 0),
      reserved_bags: Number(row.reserved_bags || 0),
      reserved_kg: Number(row.reserved_kg || 0),
      has_exposure: Boolean(row.has_exposure),
      distinct_reference_count: Number(row.distinct_reference_count || 0),
      primary_reference: row.primary_reference,
      marker_radius: markerRadius(row),
    },
  };
}

function buildFeatureCollection(rows: ClientGeographyMapClientRow[]): FeatureCollection<Point, MapFeatureProperties> {
  return {
    type: "FeatureCollection",
    features: rows.map(toFeature),
  };
}

export function ClientGeographyMap({
  basemapMode,
  onBasemapModeChange,
  rows,
  selectedMarkerId,
  onSelectMarker,
}: ClientGeographyMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const features = useMemo(() => buildFeatureCollection(rows), [rows]);
  const featuresRef = useRef(features);
  const selectedMarkerRef = useRef(selectedMarkerId);

  useEffect(() => {
    featuresRef.current = features;
  }, [features]);

  useEffect(() => {
    selectedMarkerRef.current = selectedMarkerId;
  }, [selectedMarkerId]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: getClientGeographyBasemapStyleUrl(basemapMode),
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      attributionControl: {
        compact: true,
      },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      installClientLayers(map, onSelectMarker);
      setClientSourceData(map, featuresRef.current);
      setSelectedMarker(map, selectedMarkerRef.current);
      fitMapToFeatures(map, featuresRef.current, 0);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [basemapMode, onSelectMarker]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) {
      return;
    }
    if (!map.getSource("clients")) {
      return;
    }
    setClientSourceData(map, features);
    fitMapToFeatures(map, features, 500);
  }, [features]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) {
      return;
    }
    setSelectedMarker(map, selectedMarkerId);
  }, [selectedMarkerId]);

  function handleResetView() {
    const map = mapRef.current;
    if (!map) {
      return;
    }
    fitMapToFeatures(map, features, 400);
  }

  return (
    <section className="card geography-map-card">
      <div className="section-head">
        <div>
          <div className="eyebrow">Map Workspace</div>
          <h4>Resolved Client Map</h4>
          <p className="meta-note">
            Local-only client overlays on top of an OpenFreeMap cartography foundation rendered with MapLibre.
          </p>
        </div>
        <div className="geography-map-toolbar">
          <div className="geography-basemap-toggle" aria-label="Basemap mode">
            {(
              Object.entries(CLIENT_GEOGRAPHY_BASEMAPS) as Array<
                [ClientGeographyBasemapMode, (typeof CLIENT_GEOGRAPHY_BASEMAPS)[ClientGeographyBasemapMode]]
              >
            ).map(([mode, definition]) => (
              <button
                key={mode}
                className={`secondary-button geography-basemap-button${basemapMode === mode ? " active" : ""}`}
                type="button"
                aria-pressed={basemapMode === mode}
                onClick={() => onBasemapModeChange(mode)}
              >
                {definition.label}
              </button>
            ))}
          </div>
          <button className="secondary-button" type="button" onClick={handleResetView}>
            Reset View
          </button>
        </div>
      </div>
      <div className="geography-map-legend">
        <span className="geography-legend-item">
          <span className="geography-legend-swatch exposure" />
          With current exposure
        </span>
        <span className="geography-legend-item">
          <span className="geography-legend-swatch no-exposure" />
          Zero exposure
        </span>
        <span className="geography-legend-item">
          <span className="geography-legend-swatch cluster" />
          Clustered clients
        </span>
      </div>
      <div className="geography-map-frame">
        <div className="geography-map-canvas" ref={containerRef} />
        {!rows.length ? (
          <div className="geography-map-empty">
            No resolved client markers match the current geography filters.
          </div>
        ) : null}
      </div>
    </section>
  );
}

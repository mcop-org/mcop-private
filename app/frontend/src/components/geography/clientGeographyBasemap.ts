export type ClientGeographyBasemapMode = "light" | "dark";

type ClientGeographyBasemapDefinition = {
  label: string;
  styleUrl: string;
};

export const CLIENT_GEOGRAPHY_BASEMAPS: Record<
  ClientGeographyBasemapMode,
  ClientGeographyBasemapDefinition
> = {
  light: {
    label: "Light",
    styleUrl: "https://tiles.openfreemap.org/styles/positron",
  },
  dark: {
    label: "Dark",
    styleUrl: "https://tiles.openfreemap.org/styles/dark",
  },
};

export const DEFAULT_CLIENT_GEOGRAPHY_BASEMAP_MODE: ClientGeographyBasemapMode = "light";

export function getClientGeographyBasemapStyleUrl(mode: ClientGeographyBasemapMode) {
  return CLIENT_GEOGRAPHY_BASEMAPS[mode].styleUrl;
}

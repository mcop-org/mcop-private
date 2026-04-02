from __future__ import annotations

from pathlib import Path


def test_client_geography_map_uses_openfreemap_basemap_variants_only_for_cartography() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    basemap_config_file = repo_root / "app/frontend/src/components/geography/clientGeographyBasemap.ts"
    map_file = repo_root / "app/frontend/src/components/geography/ClientGeographyMap.tsx"

    basemap_config_source = basemap_config_file.read_text(encoding="utf-8")
    map_source = map_file.read_text(encoding="utf-8")

    assert "https://tiles.openfreemap.org/styles/positron" in basemap_config_source
    assert "https://tiles.openfreemap.org/styles/dark" in basemap_config_source
    assert "maplibre-gl" in map_source
    assert "provider SDK" not in map_source
    assert "client-geography-basemap.svg" not in map_source
    assert '"clients"' in map_source
    assert '"client-clusters"' in map_source
    assert '"client-points"' in map_source
    assert '"client-points-selected"' in map_source
    assert "geocode" not in basemap_config_source.lower()
    assert "geocode" not in map_source.lower()
    assert "routing" not in basemap_config_source.lower()
    assert "routing" not in map_source.lower()

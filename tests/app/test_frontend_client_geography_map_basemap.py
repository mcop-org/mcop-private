from __future__ import annotations

from pathlib import Path


def test_client_geography_map_bundles_local_basemap_layers() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    basemap_file = repo_root / "app/frontend/src/components/geography/client-geography-basemap.svg"
    map_file = repo_root / "app/frontend/src/components/geography/ClientGeographyMap.tsx"

    basemap_source = basemap_file.read_text(encoding="utf-8")
    map_source = map_file.read_text(encoding="utf-8")

    assert "<svg" in basemap_source
    assert "United Kingdom" in basemap_source
    assert '"basemap-image"' in map_source
    assert '"basemap-image-layer"' in map_source
    assert '"basemap-grid"' in map_source
    assert '"basemap-grid-lines"' in map_source

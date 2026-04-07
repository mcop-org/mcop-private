from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "uk_postcodes_primary_raw.csv"
OUTPUT_PATH = ROOT / "uk_postcodes_primary.json"
DATASET_VERSION = "2026-04-07-uk-primary-1"


def main() -> None:
    rows: list[dict[str, object]] = []
    with RAW_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            postcode = str(row.get("postcode") or "").strip()
            city = str(row.get("city") or "").strip()
            latitude = round(float(row["latitude"]), 6)
            longitude = round(float(row["longitude"]), 6)
            if not postcode:
                continue
            rows.append(
                {
                    "postcode": postcode,
                    "city": city,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

    rows = sorted(rows, key=lambda row: (str(row["postcode"]), str(row["city"])))
    payload = {
        "dataset_version": DATASET_VERSION,
        "source": "Local UK postcode dataset generated from canonical raw CSV",
        "country_source": "GB",
        "coverage_note": (
            "Generated local UK postcode dataset in resolver-owned format; trusted overrides remain "
            "authoritative and outward fallback remains secondary."
        ),
        "rows": rows,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

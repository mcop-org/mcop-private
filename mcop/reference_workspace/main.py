from __future__ import annotations

import argparse
from pathlib import Path

from mcop.config import get_paths
from mcop.ingest.loaders import load_inputs
from mcop.reference_workspace.builder import build_reference_workspace_dataset
from mcop.reference_workspace.dashboard import write_reference_workspace_html
from mcop.reference_workspace.uk_postcode_service import UKPostcodeServiceConfig


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m mcop.reference_workspace.main")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output HTML path. Defaults to out/ReferenceWorkspace_<snapshot>.html",
    )
    parser.add_argument(
        "--enable-uk-postcode-service",
        action="store_true",
        help="Enable the internal UK postcode service path for UK geography resolution.",
    )
    parser.add_argument(
        "--uk-postcode-service-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Internal UK postcode service base URL.",
    )
    parser.add_argument(
        "--uk-postcode-service-timeout-seconds",
        type=float,
        default=2.0,
        help="Internal UK postcode service timeout in seconds.",
    )
    args = parser.parse_args()

    paths = get_paths()
    inputs = load_inputs(paths.data_dir)
    dataset = build_reference_workspace_dataset(
        inputs.activity,
        inputs.products,
        inputs.clients,
        enable_uk_postcode_service=args.enable_uk_postcode_service,
        uk_postcode_service_config=UKPostcodeServiceConfig(
            enabled=args.enable_uk_postcode_service,
            base_url=args.uk_postcode_service_url,
            timeout_seconds=args.uk_postcode_service_timeout_seconds,
        ),
    )
    snapshot_date = str(dataset.get("snapshot_date") or "unknown")
    output_path = Path(args.out) if args.out else paths.out_dir / f"ReferenceWorkspace_{snapshot_date}.html"
    write_reference_workspace_html(output_path, dataset)
    print(output_path)


if __name__ == "__main__":
    main()

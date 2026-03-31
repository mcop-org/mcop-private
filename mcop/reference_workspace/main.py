from __future__ import annotations

import argparse
from pathlib import Path

from mcop.config import get_paths
from mcop.ingest.loaders import load_inputs
from mcop.reference_workspace.builder import build_reference_workspace_dataset
from mcop.reference_workspace.dashboard import write_reference_workspace_html


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m mcop.reference_workspace.main")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output HTML path. Defaults to out/ReferenceWorkspace_<snapshot>.html",
    )
    args = parser.parse_args()

    paths = get_paths()
    inputs = load_inputs(paths.data_dir)
    dataset = build_reference_workspace_dataset(inputs.activity, inputs.products, inputs.clients)
    snapshot_date = str(dataset.get("snapshot_date") or "unknown")
    output_path = Path(args.out) if args.out else paths.out_dir / f"ReferenceWorkspace_{snapshot_date}.html"
    write_reference_workspace_html(output_path, dataset)
    print(output_path)


if __name__ == "__main__":
    main()

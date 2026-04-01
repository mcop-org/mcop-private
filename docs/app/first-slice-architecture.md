# First Slice Architecture

The first advanced-UI slice is isolated to `app/`, `tests/app/`, and `docs/app/`.

Service flow:

1. Upload datasets by named contract type into `app/workspace/uploads/`.
2. Validate required columns and build readiness into `app/workspace/validation/`.
3. Stage canonical filenames into `app/workspace/builds/current/data/`.
4. Call `mcop.ingest.loaders.load_inputs(...)` as a read-only integration point.
5. Call `mcop.reference_workspace.builder.build_reference_workspace_dataset(...)` as a read-only integration point.
6. Adapt builder outputs into UI-facing read-models in `app/workspace/readmodels/`.

Protected standalone dashboard and reference workspace renderer code remain untouched.

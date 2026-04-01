# Read-Model Contracts

First-slice read-models:

- `reservation_intelligence.json`
  - snapshot date
  - notes
  - reservation summary rows
  - reservation details rows
  - frontend filter values

- `action_queue.json`
  - summary KPIs
  - action queue detail rows
  - top landed reference summary
  - expired draft workflow passthrough
  - frontend filter values

These contracts are derived from the trusted reference workspace dataset and must not introduce new business decision logic.

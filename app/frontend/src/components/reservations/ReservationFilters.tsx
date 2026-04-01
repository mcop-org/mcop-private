import { getStatusChipClass } from "../../lib/presentation";

type ReservationFiltersProps = {
  selectedReference: string;
  referenceOptions: Array<{
    product_reference: string;
    has_reservations: boolean;
    landing_status: string;
  }>;
  search: string;
  selectedReferenceStatus: string;
  onReferenceChange: (value: string) => void;
  onSearchChange: (value: string) => void;
  onReset: () => void;
};

export function ReservationFilters({
  selectedReference,
  referenceOptions,
  search,
  selectedReferenceStatus,
  onReferenceChange,
  onSearchChange,
  onReset,
}: ReservationFiltersProps) {
  return (
    <>
      <section className="card reservation-selector-card">
        <div className="section-head">
          <div>
            <div className="eyebrow">Reference Selector</div>
            <h4>Choose Product Reference</h4>
          </div>
          <span className="topbar-chip">
            Reference: <strong>{selectedReference || "Not selected"}</strong>
          </span>
        </div>
        <div className="filters">
          <input
            className="text-input"
            list="reservation-reference-options"
            placeholder="Search or select a product reference"
            value={selectedReference}
            onChange={(event) => onReferenceChange(event.target.value)}
          />
          <datalist id="reservation-reference-options">
            {referenceOptions.map((item) => {
              const reservationState = item.has_reservations ? "Reservations live" : "No reservations";
              const label = `${item.product_reference} | ${item.landing_status || "Unknown"} | ${reservationState}`;
              return <option key={item.product_reference} value={item.product_reference} label={label} />;
            })}
          </datalist>
        </div>
        <div className="reservation-selector-footer">
          <div>
            <span className="stat-label">Selected Reference</span>
            <strong>{selectedReference || "Select product"}</strong>
            <div className="reservation-selector-copy">
              {selectedReference ? (
                <span className={getStatusChipClass(selectedReferenceStatus)}>{selectedReferenceStatus || "Unknown"}</span>
              ) : (
                "No reference selected."
              )}
            </div>
          </div>
          <button className="secondary-button" type="button" onClick={onReset}>
            Reset
          </button>
        </div>
      </section>
      <section className="card filters">
        <input
          className="text-input"
          type="search"
          placeholder="Filter by company, status, warehouse, or reservation key"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </section>
    </>
  );
}

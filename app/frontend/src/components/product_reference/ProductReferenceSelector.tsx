import type { ProductReferenceOption } from "../../lib/contracts";

type ProductReferenceSelectorProps = {
  inputValue: string;
  selectedReference: string;
  referenceOptions: ProductReferenceOption[];
  onReferenceChange: (value: string) => void;
  onReset: () => void;
};

export function ProductReferenceSelector({
  inputValue,
  selectedReference,
  referenceOptions,
  onReferenceChange,
  onReset,
}: ProductReferenceSelectorProps) {
  return (
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
          list="product-reference-options"
          placeholder="Search or select a product reference"
          value={inputValue}
          onChange={(event) => onReferenceChange(event.target.value)}
        />
        <datalist id="product-reference-options">
          {referenceOptions.map((row) => {
            const reservationState = row.has_reservations ? "Reservations live" : "No reservations";
            const label = `${row.product_reference} | ${row.landing_status || "Unknown"} | ${reservationState}`;
            return <option key={row.product_reference} value={row.product_reference} label={label} />;
          })}
        </datalist>
      </div>
      <div className="reservation-selector-footer">
        <div>
          <span className="stat-label">Selected Reference</span>
          <strong>{selectedReference || "Select product"}</strong>
        </div>
        <button className="secondary-button" type="button" onClick={onReset}>
          Reset
        </button>
      </div>
    </section>
  );
}

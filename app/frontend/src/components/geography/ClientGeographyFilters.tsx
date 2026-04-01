type ClientGeographyFiltersProps = {
  countries: string[];
  cities: string[];
  country: string;
  city: string;
  exposure: string;
  onCountryChange: (value: string) => void;
  onCityChange: (value: string) => void;
  onExposureChange: (value: string) => void;
  onReset: () => void;
};

export function ClientGeographyFilters({
  countries,
  cities,
  country,
  city,
  exposure,
  onCountryChange,
  onCityChange,
  onExposureChange,
  onReset,
}: ClientGeographyFiltersProps) {
  return (
    <section className="card geography-filter-card">
      <div className="section-head">
        <div>
          <h4>Delivery Geography Filters</h4>
          <p className="meta-note">
            Delivery `country`, `city`, and `postcode` only. Billing `po_*` fields remain excluded.
          </p>
        </div>
        <button className="secondary-button" type="button" onClick={onReset}>
          Reset Filters
        </button>
      </div>
      <div className="filters">
        <select className="select-input" value={country} onChange={(event) => onCountryChange(event.target.value)}>
          <option value="">All Countries</option>
          {countries.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <select className="select-input" value={city} onChange={(event) => onCityChange(event.target.value)}>
          <option value="">All Cities</option>
          {cities.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <select
          className="select-input"
          value={exposure}
          onChange={(event) => onExposureChange(event.target.value)}
        >
          <option value="all">All Locations</option>
          <option value="exposed">Exposed Only</option>
          <option value="no-exposure">No Exposure Only</option>
        </select>
      </div>
    </section>
  );
}

type ClientGeographyFiltersProps = {
  countries: string[];
  cities: string[];
  datePreset: string;
  dateFrom: string;
  dateTo: string;
  country: string;
  city: string;
  exposure: string;
  onDatePresetChange: (value: string) => void;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onCountryChange: (value: string) => void;
  onCityChange: (value: string) => void;
  onExposureChange: (value: string) => void;
  onReset: () => void;
};

export function ClientGeographyFilters({
  countries,
  cities,
  datePreset,
  dateFrom,
  dateTo,
  country,
  city,
  exposure,
  onDatePresetChange,
  onDateFromChange,
  onDateToChange,
  onCountryChange,
  onCityChange,
  onExposureChange,
  onReset,
}: ClientGeographyFiltersProps) {
  const showCustomRange = datePreset === "custom";

  return (
    <section className="card geography-filter-card filter-card-consistent">
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
      <div className="filters filters-consistent">
        <select className="select-input" value={datePreset} onChange={(event) => onDatePresetChange(event.target.value)}>
          <option value="all">All request dates</option>
          <option value="last-30">Last 30 days</option>
          <option value="last-90">Last 90 days</option>
          <option value="month-to-date">Month to date</option>
          <option value="financial-year-to-date">Financial year to date</option>
          <option value="custom">Custom range</option>
        </select>
        {showCustomRange ? (
          <input
            className="text-input"
            type="date"
            value={dateFrom}
            onChange={(event) => onDateFromChange(event.target.value)}
          />
        ) : null}
        {showCustomRange ? (
          <input
            className="text-input"
            type="date"
            value={dateTo}
            onChange={(event) => onDateToChange(event.target.value)}
          />
        ) : null}
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

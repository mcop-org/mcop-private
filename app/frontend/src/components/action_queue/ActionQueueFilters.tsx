type ActionQueueFiltersProps = {
  search: string;
  actionBucket: string;
  landingStatus: string;
  dataStatus: string;
  actionBuckets: string[];
  landingStatuses: string[];
  dataStatuses: string[];
  onSearchChange: (value: string) => void;
  onActionBucketChange: (value: string) => void;
  onLandingStatusChange: (value: string) => void;
  onDataStatusChange: (value: string) => void;
};

export function ActionQueueFilters({
  search,
  actionBucket,
  landingStatus,
  dataStatus,
  actionBuckets,
  landingStatuses,
  dataStatuses,
  onSearchChange,
  onActionBucketChange,
  onLandingStatusChange,
  onDataStatusChange,
}: ActionQueueFiltersProps) {
  return (
    <section className="card filters">
      <input
        className="text-input"
        type="search"
        placeholder="Filter by company, client ID, reference, reservation key, or warehouse"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
      />
      <select className="select-input" value={actionBucket} onChange={(event) => onActionBucketChange(event.target.value)}>
        <option value="">All action buckets</option>
        {actionBuckets.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <select className="select-input" value={landingStatus} onChange={(event) => onLandingStatusChange(event.target.value)}>
        <option value="">All landing statuses</option>
        {landingStatuses.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <select className="select-input" value={dataStatus} onChange={(event) => onDataStatusChange(event.target.value)}>
        <option value="">All data statuses</option>
        {dataStatuses.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </section>
  );
}

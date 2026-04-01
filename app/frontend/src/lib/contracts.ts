export type DatasetContract = {
  dataset_type: string;
  label: string;
  description: string;
  required: boolean;
  blocking_for_build: boolean;
  accepted_extensions: string[];
  required_columns: string[];
};

export type DatasetContractsResponse = {
  datasets: DatasetContract[];
};

export type DatasetStatus = {
  dataset_type: string;
  label: string;
  required: boolean;
  blocking_for_build: boolean;
  blocks_build: boolean;
  uploaded: boolean;
  is_valid: boolean;
  filename: string;
  row_count: number;
  column_count: number;
  raw_columns: string[];
  recognized_columns: string[];
  missing_columns: string[];
  errors: string[];
  build_blocking_reason: string;
};

export type DatasetStatusResponse = {
  build_ready: boolean;
  datasets: DatasetStatus[];
};

export type BuildStatusResponse = {
  state: string;
  message: string;
  snapshot_date: string;
  artifacts: Record<string, string>;
};

export type ProductReferenceOption = {
  product_reference: string;
  has_reservations: boolean;
  landing_status: string;
};

export type ProductReferenceSummaryRow = {
  product_reference: string;
  incoming_bags: number;
  incoming_bags_available: boolean;
  incoming_kg: number;
  incoming_kg_available: boolean;
  landed_bags: number;
  landed_bags_available: boolean;
  landed_kg: number;
  landed_kg_available: boolean;
  landed_available_bags: number;
  landed_available_bags_available: boolean;
  landed_available_kg: number;
  landed_available_kg_available: boolean;
  stock_health: string;
};

export type ProductLandingProfileRow = {
  product_reference: string;
  product_id: string;
  landing_status: string;
  landing_date: string;
  warehouse: string;
  bags: number | null;
  bag_size_kg: number | null;
  total_kg: number | null;
  bags_available: number | null;
  available_kg: number | null;
};

export type ProductReferenceIntelligenceReadModel = {
  snapshot_date: string;
  default_reference: string;
  reference_options: ProductReferenceOption[];
  summary: ProductReferenceSummaryRow[];
  landing_profile: ProductLandingProfileRow[];
  filters: {
    product_references: string[];
  };
};

export type ReservationSummaryRow = {
  product_reference: string;
  landing_status: string;
  is_landed?: boolean;
  reservation_row_count: number;
  client_count: number;
  reserved_bags: number;
  bags_available: number;
  reserved_pct: number;
  reserved_kg: number;
  reserved_value_gbp: number;
};

export type ReservationDetailRow = {
  id_request?: string;
  product_reference: string;
  reservation_key: string;
  client_id: string;
  company_name: string;
  request_status: string;
  request_date: string;
  approval_date: string;
  amendment_date?: string;
  landing_status: string;
  landing_date?: string;
  warehouse: string;
  bags?: number;
  bags_remaining: number;
  effective_bags?: number;
  bag_size_kg?: number;
  reserved_kg: number;
  reserved_value_gbp: number;
};

export type ReservationReadModel = {
  snapshot_date: string;
  notes: string[];
  default_reference: string;
  reference_options: Array<{ product_reference: string; has_reservations: boolean; landing_status: string }>;
  summary: ReservationSummaryRow[];
  details: ReservationDetailRow[];
  filters: {
    product_references: string[];
    statuses: string[];
  };
};

export type ActionQueueSummary = Record<string, number | string>;

export type ActionQueueChartRow = Record<string, string | number | null>;

export type ActionQueueDetailRow = {
  reservation_key: string;
  company_name: string;
  client_id?: string;
  product_reference: string;
  product_id?: string;
  request_status: string;
  action_bucket: string;
  action_priority: string;
  action_priority_rank?: number;
  days_to_expiry: number | null;
  expiry_date?: string;
  approval_date?: string;
  reservation_days?: number | null;
  bags_remaining?: number | null;
  landing_status?: string;
  landing_date?: string;
  warehouse?: string;
  remaining_kg: number | null;
  remaining_value_gbp: number | null;
  data_status: string;
};

export type ActionQueueReadModel = {
  snapshot_date: string;
  summary: ActionQueueSummary;
  top_landed_references: {
    metric?: string;
    metric_label?: string;
    value_available?: boolean;
    status?: string;
    rows?: ActionQueueChartRow[];
  };
  action_bucket_counts?: ActionQueueChartRow[];
  open_bags_by_expiry_bucket?: ActionQueueChartRow[];
  details: ActionQueueDetailRow[];
  expired_draft_workflow: {
    summary?: Record<string, string | number>;
    drafts?: Array<Record<string, unknown>>;
  };
  filters: {
    action_buckets: string[];
    landing_statuses?: string[];
    data_statuses?: string[];
  };
};

export type ClientGeographySummary = {
  mapped_clients: number;
  unmapped_clients: number;
  countries_covered: number;
  cities_covered: number;
  exposed_client_locations: number;
  duplicate_client_ids: number;
  duplicate_client_rows: number;
  matched_client_rows: number;
  unmatched_client_rows: number;
  resolved_map_clients: number;
  unresolved_map_clients: number;
  coordinate_conflicts: number;
  map_included: boolean;
  map_status: string;
};

export type ClientGeographyLocationRow = {
  country: string;
  city: string;
  postcode: string;
  location_label: string;
  client_count: number;
  exposed_client_count: number;
  reserved_bags: number;
  reserved_kg: number;
  reserved_value_gbp: number;
  reserved_value_available: boolean;
  top_client_company_name: string;
  top_client_id: string;
};

export type ClientGeographyMapClientRow = {
  marker_id: string;
  company_name: string;
  client_id: string;
  country: string;
  city: string;
  postcode: string;
  location_label: string;
  latitude: number;
  longitude: number;
  coordinate_match_level: string;
  reserved_value_gbp: number;
  reserved_value_available: boolean;
  reserved_bags: number;
  reserved_kg: number;
  has_exposure: boolean;
  distinct_reference_count: number;
  primary_reference: string;
};

export type ClientGeographyUnmappedClientRow = {
  company_name: string;
  client_id: string;
  reserved_value_gbp: number;
  reserved_value_available: boolean;
  reserved_bags: number;
  reserved_kg: number;
  reason: string;
};

export type ClientGeographyReadModel = {
  snapshot_date: string;
  summary: ClientGeographySummary;
  locations: ClientGeographyLocationRow[];
  map_clients: ClientGeographyMapClientRow[];
  unmapped_clients: ClientGeographyUnmappedClientRow[];
  top_countries: Array<Record<string, string | number | boolean>>;
  top_cities: Array<Record<string, string | number | boolean>>;
  filters: {
    countries: string[];
    cities: string[];
    exposure_states: string[];
  };
};

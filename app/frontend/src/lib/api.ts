import type {
  ActionQueueReadModel,
  BuildStatusResponse,
  ClientGeographyReadModel,
  DatasetContractsResponse,
  DatasetStatusResponse,
  ProductReferenceIntelligenceReadModel,
  ReservationReadModel,
} from "./contracts";

const serviceBaseUrl =
  (
    import.meta.env.VITE_SERVICE_BASE_URL?.toString() || "http://127.0.0.1:8765"
  ).replace(/\/+$/, "");

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${serviceBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed for ${path}`);
  }
  return payload as T;
}

export function getDatasetContracts() {
  return requestJson<DatasetContractsResponse>("/datasets/contracts");
}

export function getDatasetStatus() {
  return requestJson<DatasetStatusResponse>("/datasets/status");
}

export function uploadDataset(datasetType: string, filename: string, contentBase64: string) {
  return requestJson<{ status: DatasetStatusResponse }>("/datasets/load", {
    method: "POST",
    body: JSON.stringify({
      dataset_type: datasetType,
      filename,
      content_base64: contentBase64,
    }),
  });
}

export function runBuild() {
  return requestJson<BuildStatusResponse>("/build/run", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getBuildStatus() {
  return requestJson<BuildStatusResponse>("/build/status");
}

export function getReservationReadModel() {
  return requestJson<ReservationReadModel>("/modules/reservations");
}

export function getProductReferenceIntelligenceReadModel() {
  return requestJson<ProductReferenceIntelligenceReadModel>("/modules/product-reference-intelligence");
}

export function getActionQueueReadModel() {
  return requestJson<ActionQueueReadModel>("/modules/action-queue");
}

export function getClientGeographyReadModel() {
  return requestJson<ClientGeographyReadModel>("/modules/client-geography");
}

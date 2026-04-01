import { useEffect, useState } from "react";
import { BuildRunPanel } from "../components/build/BuildRunPanel";
import { DatasetStatusCard } from "../components/data/DatasetStatusCard";
import { DatasetUploadPanel } from "../components/data/DatasetUploadPanel";
import { ValidationResultsTable } from "../components/data/ValidationResultsTable";
import { getBuildStatus, getDatasetContracts, getDatasetStatus, runBuild, uploadDataset } from "../lib/api";
import type { BuildStatusResponse, DatasetContractsResponse, DatasetStatusResponse } from "../lib/contracts";
import { useAsyncData } from "../lib/query";

export function DataContractsPage() {
  const contractsState = useAsyncData<DatasetContractsResponse>(getDatasetContracts, []);
  const statusState = useAsyncData<DatasetStatusResponse>(getDatasetStatus, []);
  const buildState = useAsyncData<BuildStatusResponse>(getBuildStatus, []);
  const [uploadingType, setUploadingType] = useState<string>("");
  const [actionError, setActionError] = useState<string>("");

  useEffect(() => {
    if (statusState.error) {
      setActionError(statusState.error);
    }
  }, [statusState.error]);

  async function handleUpload(datasetType: string, file: File) {
    setUploadingType(datasetType);
    setActionError("");
    try {
      const contentBase64 = await fileToBase64(file);
      const response = await uploadDataset(datasetType, file.name, contentBase64);
      statusState.setData(response.status);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setUploadingType("");
    }
  }

  async function handleBuild() {
    setActionError("");
    try {
      const response = await runBuild();
      buildState.setData(response);
      const latestStatus = await getDatasetStatus();
      statusState.setData(latestStatus);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Build failed");
    }
  }

  const contracts = contractsState.data?.datasets || [];
  const statuses = statusState.data?.datasets || [];

  return (
    <section className="page">
      <div className="page-header">
        <h3>Named Dataset Contracts</h3>
        <p>Replace or update datasets by contract type, validate them locally, then run a deterministic build.</p>
      </div>
      {actionError ? <div className="banner error">{actionError}</div> : null}
      <div className="card-grid two-up">
        {contracts.map((contract) => {
          const status = statuses.find((item) => item.dataset_type === contract.dataset_type);
          return (
            <DatasetUploadPanel
              key={contract.dataset_type}
              contract={contract}
              status={status}
              isUploading={uploadingType === contract.dataset_type}
              onUpload={handleUpload}
            />
          );
        })}
      </div>
      <div className="card-grid two-up">
        <DatasetStatusCard
          buildReady={Boolean(statusState.data?.build_ready)}
          datasets={statuses}
          loading={statusState.loading}
        />
        <BuildRunPanel buildStatus={buildState.data} onRunBuild={handleBuild} />
      </div>
      <ValidationResultsTable datasets={statuses} />
    </section>
  );
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result || "");
      const base64 = value.includes(",") ? value.split(",")[1] : value;
      resolve(base64);
    };
    reader.onerror = () => reject(new Error("Could not read file"));
    reader.readAsDataURL(file);
  });
}

import type { BuildStatusResponse } from "../../lib/contracts";
import { getStatusChipClass } from "../../lib/presentation";

type BuildRunPanelProps = {
  buildStatus: BuildStatusResponse | null;
  onRunBuild: () => Promise<void>;
};

export function BuildRunPanel({ buildStatus, onRunBuild }: BuildRunPanelProps) {
  return (
    <section className="card">
      <div className="section-head">
        <div>
          <div className="eyebrow">Build orchestration</div>
          <h4>Run Local Build</h4>
        </div>
        <span className={getStatusChipClass(buildStatus?.state === "ready" ? "Build Ready" : buildStatus?.state || "Unknown")}>
          {buildStatus?.state || "idle"}
        </span>
      </div>
      <p>The service validates uploaded contract types, stages files into `app/workspace/`, then calls the trusted loader and reference builder.</p>
      <button className="primary-button" onClick={() => void onRunBuild()} type="button">
        Run build
      </button>
      <div className="build-status">
        <div>State: {buildStatus?.state || "idle"}</div>
        <div>Message: {buildStatus?.message || "No build has been run yet."}</div>
        <div>Snapshot date: {buildStatus?.snapshot_date || "-"}</div>
      </div>
    </section>
  );
}

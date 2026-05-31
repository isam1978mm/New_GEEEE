import React from "react";
import { createRoot } from "react-dom/client";
import { Activity, Archive, CheckCircle2, Download, Search, ShieldCheck } from "lucide-react";
import "./styles.css";

const mockRuns = [
  {
    id: "mock-run-001",
    name: "Mock operator validation run",
    state: "done",
    detail: "Mock Data only. Real API integration starts in Phase 9E-B.",
    currentStage: "Complete",
    updated: "2026-05-31 18:40",
    stages: ["Grid", "DEM", "SAR", "S2", "Stacks", "Objects", "QA"],
    history: ["Queued mock run", "Rendered mock lifecycle", "Validated mock export browser"],
  },
  {
    id: "mock-run-002",
    name: "Mock historical run",
    state: "done",
    detail: "Static sample for side-by-side migration review.",
    currentStage: "Complete",
    updated: "2026-05-31 17:05",
    stages: ["Grid", "DEM", "SAR", "S2", "Stacks"],
    history: ["Loaded fixture", "Rendered summary", "Closed fixture"],
  },
];

const keyDownloads = [
  "QA/RUN_MANIFEST.json",
  "DEM_GEO8_TIFS/DEM_640.tif",
  "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
  "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
  "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
];

const exportGroups = {
  DEM_GEO8_TIFS: ["DEM_640.tif", "slope_deg_640.tif", "hillshade_0to1_640.tif"],
  NPY_STACKS: ["FINAL_TESLA_V7_2_HYPERCUBE.tif", "FINAL_TESLA_V7_2_HYPERCUBE.npy"],
  QA: ["RUN_MANIFEST.json", "QA_GRID_validmask_640.tif", "sar/intermediates/sar_intermediate_manifest.json"],
};

function App() {
  const activeRun = mockRuns[0];
  return (
    <main className="shell">
      <section className="masthead">
        <div>
          <p className="eyebrow">React frontend-v2</p>
          <h1>GEE Screening Operator Mock V2</h1>
          <p className="summary">
            Side-by-side mock dashboard for Phase 9E-A. The legacy UI remains at the root route while this shell is reviewed at /v2.
          </p>
        </div>
        <div className="mock-badge">
          <ShieldCheck size={18} aria-hidden="true" />
          <span>Mock Data</span>
        </div>
      </section>

      <section className="dashboard-grid" aria-label="Mock operator dashboard">
        <article className="panel run-panel">
          <div className="panel-title">
            <Activity size={18} aria-hidden="true" />
            <h2>Overview</h2>
          </div>
          <dl className="run-facts">
            <div>
              <dt>Run</dt>
              <dd>{activeRun.name}</dd>
            </div>
            <div>
              <dt>State</dt>
              <dd>{activeRun.state}</dd>
            </div>
            <div>
              <dt>Current stage</dt>
              <dd>{activeRun.currentStage}</dd>
            </div>
            <div>
              <dt>Updated</dt>
              <dd>{activeRun.updated}</dd>
            </div>
          </dl>
          <p className="detail">{activeRun.detail}</p>
          <div className="stage-row" aria-label="Mock stage progress">
            {activeRun.stages.map((stage) => (
              <span className="stage-pill" key={stage} title={`${stage}: done`}>
                <CheckCircle2 size={14} aria-hidden="true" />
                {stage}
              </span>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-title">
            <Archive size={18} aria-hidden="true" />
            <h2>Recent Runs</h2>
          </div>
          <div className="run-list">
            {mockRuns.map((run) => (
              <button className="run-row" type="button" key={run.id}>
                <span>{run.name}</span>
                <small>{run.state} - {run.updated}</small>
              </button>
            ))}
          </div>
        </article>

        <article className="panel wide">
          <div className="panel-title">
            <Download size={18} aria-hidden="true" />
            <h2>Key Downloads</h2>
          </div>
          <div className="download-grid">
            {keyDownloads.map((path) => (
              <span className="download-token" key={path}>{path}</span>
            ))}
          </div>
        </article>

        <article className="panel wide">
          <div className="panel-title">
            <Search size={18} aria-hidden="true" />
            <h2>Exports</h2>
          </div>
          <label className="search-label">
            Search exports
            <input type="search" placeholder="Filter mock export paths" />
          </label>
          <div className="export-groups">
            {Object.entries(exportGroups).map(([group, files]) => (
              <details key={group}>
                <summary>{group} ({files.length})</summary>
                <ul>
                  {files.map((file) => (
                    <li key={file}>{file}</li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Status History</h2>
          <ol className="history-list">
            {activeRun.history.map((event) => (
              <li key={event}>{event}</li>
            ))}
          </ol>
        </article>

        <article className="panel">
          <h2>Diagnostics</h2>
          <p className="detail">
            No real run data, artifact APIs, guarded downloads, or backend calls are wired in this phase.
          </p>
          <details>
            <summary>Advanced / unavailable outputs</summary>
            <p>Unavailable items are static placeholders in the mock shell.</p>
          </details>
        </article>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);

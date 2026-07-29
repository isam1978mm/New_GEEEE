import { useState, type ChangeEvent } from "react";
import {
  runOperatorLocalDepth,
  type OperatorLocalDepthEstimate,
  type OperatorLocalDepthResult,
} from "../api/operatorLocalDepth";
import {
  buildOperatorLocalDepthTemplate,
  inspectOperatorLocalDepthGeojson,
  type ReviewedFileSummary,
} from "../localDepthPreflight";

interface OperatorLocalDepthPanelProps {
  runId: string;
  operatorAccessToken?: string | null;
}

export function OperatorLocalDepthPanel({ runId, operatorAccessToken }: OperatorLocalDepthPanelProps) {
  const [siteId, setSiteId] = useState("");
  const [datasetVersion, setDatasetVersion] = useState("");
  const [inputCrs, setInputCrs] = useState("EPSG:4326");
  const [erosionPixels, setErosionPixels] = useState(2);
  const [minimumValidPixels, setMinimumValidPixels] = useState(20);
  const [allowWarning, setAllowWarning] = useState(false);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [geojson, setGeojson] = useState<Record<string, unknown> | null>(null);
  const [fileSummary, setFileSummary] = useState<ReviewedFileSummary | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<OperatorLocalDepthResult | null>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setGeojson(null);
    setFileSummary(null);
    setFileError(null);
    setResult(null);
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      const parsed = JSON.parse(await file.text()) as unknown;
      const summary = inspectOperatorLocalDepthGeojson(parsed, file.name);
      setGeojson(parsed as Record<string, unknown>);
      setFileSummary(summary);
    } catch (error) {
      setFileError(error instanceof Error ? error.message : "The selected GeoJSON file is not valid.");
    }
  }

  function handleDownloadTemplate() {
    const template = buildOperatorLocalDepthTemplate();
    const blob = new Blob([`${JSON.stringify(template, null, 2)}\n`], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "operator-local-depth-first-aoi-template.geojson";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function handleRun() {
    if (!geojson || !confirmed || !siteId.trim() || !datasetVersion.trim()) {
      return;
    }
    setProcessing(true);
    setResult(null);
    const nextResult = await runOperatorLocalDepth(
      runId,
      {
        geojson,
        siteId: siteId.trim(),
        calibrationDatasetVersion: datasetVersion.trim(),
        inputCrs: inputCrs.trim() || "EPSG:4326",
        erosionPixels,
        minimumValidPixels,
        allowRunQualityWarning: allowWarning,
        force: replaceExisting,
        operatorConfirmedReview: confirmed,
      },
      { accessToken: operatorAccessToken },
    );
    setResult(nextResult);
    setProcessing(false);
  }

  const ready = Boolean(
    geojson &&
      confirmed &&
      siteId.trim() &&
      datasetVersion.trim() &&
      !processing,
  );

  return (
    <section
      className="rounded-lg bg-card overflow-hidden mt-4"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <details>
        <summary
          className="px-4 py-2"
          style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)", cursor: "pointer" }}
        >
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            Local depth calibration — operator only
          </span>
        </summary>

        <div className="px-4 py-3 flex flex-col gap-3">
          <BoundaryNotice />

          <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(210px,1fr))" }}>
            <Field label="Site ID">
              <input value={siteId} onChange={(event) => setSiteId(event.target.value)} placeholder="example-site" style={inputStyle} />
            </Field>
            <Field label="Calibration dataset version">
              <input value={datasetVersion} onChange={(event) => setDatasetVersion(event.target.value)} placeholder="survey-2026-v1" style={inputStyle} />
            </Field>
            <Field label="GeoJSON coordinate system">
              <input value={inputCrs} onChange={(event) => setInputCrs(event.target.value)} style={inputStyle} />
            </Field>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <Field label="Reviewed anchor and candidate polygons">
              <input
                type="file"
                accept=".geojson,.json,application/geo+json,application/json"
                onChange={(event) => { void handleFileChange(event); }}
                style={{ fontSize: "11px", color: "var(--gs-slate)" }}
              />
            </Field>
            <button type="button" onClick={handleDownloadTemplate} className="rounded px-3 py-2" style={secondaryButtonStyle}>
              Download blank GeoJSON template
            </button>
          </div>

          {fileError && <StatusBox tone="error" message={`Preflight failed: ${fileError}`} />}
          {fileSummary && (
            <StatusBox
              tone="success"
              message={`Preflight passed — ${fileSummary.fileName}: ${fileSummary.featureCount} features, ${fileSummary.anchorCount} measured anchors, ${fileSummary.candidateCount} candidates, anchor support ${formatMetres(fileSummary.minimumAnchorDepthM)}–${formatMetres(fileSummary.maximumAnchorDepthM)} m.`}
            />
          )}
          {fileSummary && (
            <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
              <div><strong style={{ color: "var(--gs-navy)" }}>Anchors:</strong> {summariseIds(fileSummary.anchorIds)}</div>
              <div><strong style={{ color: "var(--gs-navy)" }}>Candidates:</strong> {summariseIds(fileSummary.candidateIds)}</div>
              <div style={{ marginTop: "4px" }}>This structural preflight does not replace the backend raster-intersection, pixel-count, overlap, run-quality, or no-extrapolation checks.</div>
            </div>
          )}

          <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
            <Field label="Boundary erosion (pixels)">
              <input
                type="number"
                min={0}
                max={10}
                value={erosionPixels}
                onChange={(event) => setErosionPixels(clampInteger(event.target.value, 0, 10, 2))}
                style={inputStyle}
              />
            </Field>
            <Field label="Minimum valid pixels">
              <input
                type="number"
                min={1}
                max={100000}
                value={minimumValidPixels}
                onChange={(event) => setMinimumValidPixels(clampInteger(event.target.value, 1, 100000, 20))}
                style={inputStyle}
              />
            </Field>
          </div>

          <label style={checkboxStyle}>
            <input type="checkbox" checked={allowWarning} onChange={(event) => setAllowWarning(event.target.checked)} />
            Permit an otherwise usable run-quality WARNING. PASS remains preferred.
          </label>
          <label style={checkboxStyle}>
            <input type="checkbox" checked={replaceExisting} onChange={(event) => setReplaceExisting(event.target.checked)} />
            Replace this run's previous private local-depth inputs and results.
          </label>
          <label style={checkboxStyle}>
            <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
            I reviewed these polygons and the measured anchor depth ranges.
          </label>

          <button
            type="button"
            disabled={!ready}
            onClick={() => { void handleRun(); }}
            className="rounded px-3 py-2"
            style={{
              alignSelf: "flex-start",
              fontSize: "11px",
              fontWeight: 700,
              color: ready ? "white" : "var(--gs-slate)",
              backgroundColor: ready ? "var(--gs-navy)" : "var(--accent)",
              border: "1px solid rgba(28,43,94,0.18)",
              cursor: ready ? "pointer" : "not-allowed",
            }}
          >
            {processing ? "Processing local calibration..." : "Run local depth calibration"}
          </button>

          {result && <ResultBody result={result} />}
        </div>
      </details>
    </section>
  );
}

function BoundaryNotice() {
  return (
    <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--gs-amber-bg)", border: "1px solid var(--gs-amber-border)", fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.55" }}>
      <strong style={{ color: "var(--gs-navy)" }}>What this does:</strong> uses your measured local anchor polygons to estimate candidates inside the same signal range. It does not discover depth without measured anchors, never extrapolates, and is not transferable to another site.
    </div>
  );
}

function ResultBody({ result }: { result: OperatorLocalDepthResult }) {
  if (result.outcome === "denied") {
    return <StatusBox tone="warning" message={result.message || "Operator local depth access is not available."} />;
  }
  if (result.outcome === "error") {
    return <StatusBox tone="error" message={result.message || "The local depth request could not be processed."} />;
  }

  return (
    <div className="flex flex-col gap-3">
      <StatusBox
        tone={result.estimatedCount > 0 ? "success" : "warning"}
        message={`${result.estimatedCount} of ${result.candidateCount} candidates received a local calibrated metre range. ${result.insufficientDataCount + result.notAvailableCount} abstained.`}
      />
      <div className="rounded overflow-x-auto" style={{ border: "1px solid var(--border)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
          <thead style={{ backgroundColor: "var(--accent)", color: "var(--gs-navy)" }}>
            <tr>
              <Header>Candidate</Header>
              <Header>Status</Header>
              <Header>Local depth range</Header>
              <Header>Best</Header>
            </tr>
          </thead>
          <tbody>
            {result.estimates.map((estimate) => <EstimateRow key={estimate.candidateId} estimate={estimate} />)}
          </tbody>
        </table>
      </div>
      <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
        Private filesystem-only output. Geometry returned: {result.geometryReturned ? "yes" : "no"}. Transferable: {result.transferable ? "yes" : "no"}. Enabled by default: {result.appDepthEnabledByDefault ? "yes" : "no"}.
      </div>
    </div>
  );
}

function EstimateRow({ estimate }: { estimate: OperatorLocalDepthEstimate }) {
  const ranged = estimate.estimatedDepthMinM !== null && estimate.estimatedDepthMaxM !== null;
  return (
    <tr style={{ borderTop: "1px solid var(--border)", color: "var(--gs-slate)" }}>
      <Cell mono>{estimate.candidateId}</Cell>
      <Cell>{estimate.depthStatus}</Cell>
      <Cell>{ranged ? `${formatMetres(estimate.estimatedDepthMinM)}–${formatMetres(estimate.estimatedDepthMaxM)} m` : "No metre range"}</Cell>
      <Cell>{estimate.estimatedDepthBestM === null ? "—" : `${formatMetres(estimate.estimatedDepthBestM)} m`}</Cell>
    </tr>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1" style={{ fontSize: "10.5px", fontWeight: 600, color: "var(--gs-navy)" }}>
      {label}
      {children}
    </label>
  );
}

function Header({ children }: { children: React.ReactNode }) {
  return <th style={{ padding: "7px 9px", textAlign: "left", fontWeight: 700 }}>{children}</th>;
}

function Cell({ children, mono = false }: { children: React.ReactNode; mono?: boolean }) {
  return <td className={mono ? "font-mono" : undefined} style={{ padding: "7px 9px", verticalAlign: "top" }}>{children}</td>;
}

function StatusBox({ tone, message }: { tone: "neutral" | "warning" | "error" | "success"; message: string }) {
  const styles = {
    neutral: { backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" },
    warning: { backgroundColor: "var(--gs-amber-bg)", border: "1px solid var(--gs-amber-border)", color: "var(--gs-slate)" },
    error: { backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)", color: "var(--gs-red)" },
    success: { backgroundColor: "rgba(23,135,84,0.08)", border: "1px solid rgba(23,135,84,0.25)", color: "var(--gs-navy)" },
  }[tone];
  return <div className="rounded px-3 py-2" style={{ ...styles, fontSize: "11px", lineHeight: "1.5" }}>{message}</div>;
}

function summariseIds(values: string[]): string {
  if (values.length <= 5) {
    return values.join(", ");
  }
  return `${values.slice(0, 5).join(", ")} and ${values.length - 5} more`;
}

function clampInteger(value: string, minimum: number, maximum: number, fallback: number): number {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? Math.min(maximum, Math.max(minimum, parsed)) : fallback;
}

function formatMetres(value: number): string {
  return value.toFixed(3);
}

const inputStyle = {
  width: "100%",
  padding: "7px 8px",
  borderRadius: "5px",
  border: "1px solid rgba(28,43,94,0.18)",
  backgroundColor: "white",
  color: "var(--gs-navy)",
  fontSize: "11px",
} as const;

const secondaryButtonStyle = {
  alignSelf: "flex-start",
  fontSize: "11px",
  fontWeight: 700,
  color: "var(--gs-navy)",
  backgroundColor: "var(--accent)",
  border: "1px solid rgba(28,43,94,0.18)",
  cursor: "pointer",
} as const;

const checkboxStyle = {
  display: "flex",
  alignItems: "flex-start",
  gap: "7px",
  fontSize: "10.5px",
  color: "var(--gs-slate)",
  lineHeight: "1.45",
} as const;

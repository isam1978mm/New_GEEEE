import { useEffect, useState, type ChangeEvent } from "react";
import {
  fetchOperatorLocalDepthResult,
  runOperatorLocalDepth,
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
  const [savedResult, setSavedResult] = useState<OperatorLocalDepthResult | null>(null);
  const [requestResult, setRequestResult] = useState<OperatorLocalDepthResult | null>(null);
  const [loadingSaved, setLoadingSaved] = useState(true);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadSavedCalibration() {
      setLoadingSaved(true);
      const nextResult = await fetchOperatorLocalDepthResult(runId, {
        accessToken: operatorAccessToken,
      });
      if (!cancelled) {
        setSavedResult(nextResult);
        setSiteId(nextResult.siteId || "");
        setDatasetVersion(nextResult.calibrationDatasetVersion || "");
        setEditing(nextResult.outcome !== "completed");
        setLoadingSaved(false);
      }
    }

    void loadSavedCalibration();
    return () => {
      cancelled = true;
    };
  }, [runId, operatorAccessToken]);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setGeojson(null);
    setFileSummary(null);
    setFileError(null);
    setRequestResult(null);
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
    link.download = "site-depth-known-reference-zones-template.geojson";
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
    setRequestResult(null);
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
    setRequestResult(nextResult);
    setProcessing(false);
    if (nextResult.outcome === "completed") {
      setSavedResult(nextResult);
      setEditing(false);
      setReplaceExisting(false);
      window.dispatchEvent(
        new CustomEvent("operator-local-depth-updated", { detail: { runId } }),
      );
    }
  }

  function beginReplacement() {
    setEditing(true);
    setReplaceExisting(true);
    setConfirmed(false);
    setGeojson(null);
    setFileSummary(null);
    setFileError(null);
    setRequestResult(null);
  }

  const ready = Boolean(
    geojson &&
      confirmed &&
      siteId.trim() &&
      datasetVersion.trim() &&
      !processing,
  );
  const hasCompletedCalibration = savedResult?.outcome === "completed";

  return (
    <section
      className="rounded-lg bg-card overflow-hidden"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <div
        className="px-4 py-2"
        style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <span
          className="font-mono"
          style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
        >
          Site depth calibration — one-time setup
        </span>
      </div>

      <div className="px-4 py-3 flex flex-col gap-3">
        <BoundaryNotice />

        {loadingSaved && <StatusBox tone="neutral" message="Checking this run's saved site calibration..." />}

        {!loadingSaved && hasCompletedCalibration && !editing && savedResult && (
          <SavedCalibrationSummary result={savedResult} onReplace={beginReplacement} />
        )}

        {!loadingSaved && (!hasCompletedCalibration || editing) && (
          <>
            {savedResult?.outcome === "denied" && (
              <StatusBox tone="warning" message={savedResult.message || "Site depth calibration access is not available."} />
            )}
            {savedResult?.outcome === "error" && (
              <StatusBox tone="error" message={savedResult.message || "Saved calibration status could not be loaded."} />
            )}

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
              <Field label="Known-depth reference zones (surveyed)">
                <input
                  type="file"
                  accept=".geojson,.json,application/geo+json,application/json"
                  onChange={(event) => { void handleFileChange(event); }}
                  style={{ fontSize: "11px", color: "var(--gs-slate)" }}
                />
              </Field>
              <button type="button" onClick={handleDownloadTemplate} className="rounded px-3 py-2" style={secondaryButtonStyle}>
                Download known-depth reference template
              </button>
            </div>

            {fileError && <StatusBox tone="error" message={`Preflight failed: ${fileError}`} />}
            {fileSummary && (
              <StatusBox
                tone="success"
                message={`Preflight passed — ${fileSummary.fileName}: ${fileSummary.anchorCount} known-depth references, support ${formatMetres(fileSummary.minimumAnchorDepthM)}–${formatMetres(fileSummary.maximumAnchorDepthM)} m.`}
              />
            )}
            {fileSummary && (
              <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
                <div><strong style={{ color: "var(--gs-navy)" }}>Known-depth references:</strong> {summariseIds(fileSummary.anchorIds)}</div>
                <div style={{ marginTop: "4px" }}>
                  No finding or candidate AOI is uploaded. The app automatically applies this calibration to every classifier finding in the selected run.
                </div>
                <div style={{ marginTop: "4px" }}>
                  Numerical results appear only in Dashboard → Classifier Results, beside each classifier object.
                </div>
              </div>
            )}

            <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
              <Field label="Reference boundary erosion (pixels)">
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={erosionPixels}
                  onChange={(event) => setErosionPixels(clampInteger(event.target.value, 0, 10, 2))}
                  style={inputStyle}
                />
              </Field>
              <Field label="Minimum valid reference pixels">
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
            {hasCompletedCalibration && (
              <label style={checkboxStyle}>
                <input type="checkbox" checked={replaceExisting} onChange={(event) => setReplaceExisting(event.target.checked)} />
                Replace this run's saved calibration and finding-depth results.
              </label>
            )}
            <label style={checkboxStyle}>
              <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
              I verified these are surveyed same-site zones with known depth ranges.
            </label>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={!ready}
                onClick={() => { void handleRun(); }}
                className="rounded px-3 py-2"
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: ready ? "white" : "var(--gs-slate)",
                  backgroundColor: ready ? "var(--gs-navy)" : "var(--accent)",
                  border: "1px solid rgba(28,43,94,0.18)",
                  cursor: ready ? "pointer" : "not-allowed",
                }}
              >
                {processing ? "Applying calibration to all findings..." : "Save calibration and estimate every finding"}
              </button>
              {hasCompletedCalibration && editing && (
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="rounded px-3 py-2"
                  style={secondaryButtonStyle}
                >
                  Cancel replacement
                </button>
              )}
            </div>

            {requestResult && requestResult.outcome !== "completed" && <RequestStatus result={requestResult} />}
          </>
        )}
      </div>
    </section>
  );
}

function BoundaryNotice() {
  return (
    <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--gs-amber-bg)", border: "1px solid var(--gs-amber-border)", fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.55" }}>
      <strong style={{ color: "var(--gs-navy)" }}>Calibration only — not a new AOI analysis:</strong> upload surveyed same-site reference zones whose depths are already known. The app uses every existing classifier finding automatically. Depth results are shown only in the classifier table.
    </div>
  );
}

function SavedCalibrationSummary({ result, onReplace }: { result: OperatorLocalDepthResult; onReplace: () => void }) {
  return (
    <div className="flex flex-col gap-3">
      <StatusBox
        tone="success"
        message={`Calibration saved for ${result.siteId || "this site"}. ${result.estimatedCount} of ${result.candidateCount} classifier findings received a metre range; ${result.insufficientDataCount + result.notAvailableCount} received no estimate.`}
      />
      <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))" }}>
        <Metric label="Dataset" value={result.calibrationDatasetVersion || "not reported"} />
        <Metric label="Known-depth references" value={String(result.anchorCount)} />
        <Metric label="Classifier findings" value={String(result.candidateCount)} />
        <Metric label="Estimated findings" value={String(result.estimatedCount)} />
      </dl>
      <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
        View the numerical depth range, best depth, and depth status in Dashboard → Classifier Results. The setup form is hidden because this run is already calibrated.
      </div>
      <button type="button" onClick={onReplace} className="rounded px-3 py-2" style={secondaryButtonStyle}>
        Replace saved calibration
      </button>
    </div>
  );
}

function RequestStatus({ result }: { result: OperatorLocalDepthResult }) {
  if (result.outcome === "denied") {
    return <StatusBox tone="warning" message={result.message || "Site depth calibration access is not available."} />;
  }
  return <StatusBox tone="error" message={result.message || "The site depth calibration could not be processed."} />;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.1)" }}>
      <div className="font-mono" style={{ fontSize: "9.5px", color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
      <div className="font-mono" style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-navy)", marginTop: "2px" }}>{value}</div>
    </div>
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

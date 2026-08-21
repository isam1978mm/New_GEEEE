import { Info, Loader2 } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import {
  runOperatorReviewedZoneDepth,
  type OperatorReviewedZoneDepthResult,
} from "../api/operatorReviewedZoneDepth";

interface OperatorLocalDepthPanelProps {
  runId: string;
  operatorAccessToken?: string | null;
}

export function OperatorLocalDepthPanel({ runId, operatorAccessToken }: OperatorLocalDepthPanelProps) {
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OperatorReviewedZoneDepthResult | null>(null);
  const calibrated = useMemo(
    () => result?.estimates.filter((estimate) => estimate.depthStatus === "calibrated_range") ?? [],
    [result],
  );

  async function runRouteA() {
    if (!confirmed || loading) return;
    setLoading(true);
    try {
      const next = await runOperatorReviewedZoneDepth(
        runId,
        { operatorConfirmedReview: confirmed },
        { accessToken: operatorAccessToken },
      );
      setResult(next);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section
      className="mt-3 rounded-lg bg-card overflow-hidden"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <div
        className="flex items-center justify-between px-4 py-2"
        style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <div className="flex items-center gap-2">
          <span className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
            Local depth — Route A
          </span>
          <span className="font-mono" style={{ fontSize: "9px", fontWeight: 700, color: "var(--gs-blue)", backgroundColor: "var(--gs-blue-bg)", border: "1px solid var(--gs-blue-border)", padding: "1px 5px", borderRadius: "3px" }}>
            PROVISIONAL LOCAL
          </span>
        </div>
        {loading && (
          <span className="flex items-center gap-1" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            <Loader2 size={11} className="animate-spin" /> Processing
          </span>
        )}
      </div>

      <div className="px-4 py-3 flex flex-col gap-3">
        <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
          The six reviewed Tyrone plots TP1/TP2/TP3/TP5/TP6/TP7 are checked against this run footprint. Each reviewed plot fully contained by the run becomes a Route A candidate and receives its provisional local metre range. The classifier is not used for this lookup.
        </div>

        <div className="flex flex-wrap gap-1.5">
          {[
            "LOCAL ONLY",
            "PROVISIONAL CALIBRATION",
            "DERIVED GEOMETRY",
            "NOT TRANSFERABLE",
            "NOT PHYSICAL CONFIRMATION",
          ].map((label) => (
            <span key={label} className="font-mono" style={{ fontSize: "8.5px", padding: "2px 5px", borderRadius: "3px", border: "1px solid rgba(28,43,94,0.14)", color: "var(--gs-slate)", backgroundColor: "var(--accent)" }}>
              {label}
            </span>
          ))}
        </div>

        <label className="flex items-start gap-2" style={{ fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.45" }}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(event) => {
              setConfirmed(event.target.checked);
              setResult(null);
            }}
            style={{ marginTop: "2px" }}
          />
          <span>I understand these metre ranges apply only to the six reviewed Tyrone zones contained by this run footprint and are not transferable to unknown ground.</span>
        </label>

        <div>
          <button
            type="button"
            onClick={() => void runRouteA()}
            disabled={!confirmed || loading}
            className="rounded px-3 py-2"
            style={{
              fontSize: "11px",
              fontWeight: 700,
              border: "1px solid var(--gs-blue-border)",
              color: confirmed ? "var(--gs-blue)" : "var(--gs-slate)",
              backgroundColor: "var(--gs-blue-bg)",
              opacity: !confirmed || loading ? 0.55 : 1,
            }}
          >
            Run reviewed-zone depth
          </button>
        </div>

        {result?.outcome === "denied" && <Message>Operator access is not available for this run.</Message>}
        {result?.outcome === "error" && <Message>{result.message ?? "Reviewed-zone depth processing could not be completed."}</Message>}

        {result?.outcome === "completed" && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              <Stat label="Reviewed candidates" value={String(result.candidateCount)} />
              <Stat label="Inside run footprint" value={String(result.spatialMatchCount)} />
              <Stat label="Calibrated ranges" value={String(result.estimatedCount)} />
              <Stat label="Not available" value={String(result.notAvailableCount)} />
              <Stat label="Run quality" value={result.runQualityStatus} />
            </div>

            {calibrated.length === 0 ? (
              <Message>No reviewed Tyrone zone is fully inside this run footprint, or run quality does not support Route A. No metre estimate is returned.</Message>
            ) : (
              <div className="overflow-auto" style={{ border: "1px solid rgba(28,43,94,0.12)", borderRadius: "4px", maxHeight: "360px" }}>
                <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "760px" }}>
                  <thead>
                    <tr style={{ backgroundColor: "var(--accent)" }}>
                      {["Candidate", "Reviewed zone", "Status", "Min", "Best", "Max", "Quality"].map((header) => (
                        <th key={header} className="font-mono" style={headerStyle}>{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {calibrated.map((estimate) => (
                      <tr key={estimate.candidateId}>
                        <td style={cellStyle}>{estimate.candidateId}</td>
                        <td style={cellStyle}>{displayZone(estimate.zoneId)}</td>
                        <td style={cellStyle}>{estimate.depthStatus}</td>
                        <td style={cellStyle}>{formatM(estimate.estimatedDepthMinM)}</td>
                        <td style={depthCellStyle}>{formatM(estimate.estimatedDepthBestM)}</td>
                        <td style={cellStyle}>{formatM(estimate.estimatedDepthMaxM)}</td>
                        <td style={cellStyle}>{estimate.depthQuality}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
              Method: {result.methodKind || "operator_zone_lookup_v1"}. Validation status: {result.validationStatus}. Classifier used = no. These are known-zone provisional ranges; this does not validate numerical depth for new unknown locations.
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function Message({ children }: { children: ReactNode }) {
  return (
    <div className="rounded px-3 py-2 flex items-start gap-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" }}>
      <Info size={13} className="shrink-0" style={{ marginTop: "2px" }} />
      <span style={{ fontSize: "11.5px", lineHeight: "1.5" }}>{children}</span>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded px-2 py-2" style={{ border: "1px solid rgba(28,43,94,0.12)", backgroundColor: "var(--accent)" }}>
      <div className="font-mono" style={{ fontSize: "8.5px", color: "var(--gs-slate)", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--gs-navy)", marginTop: "2px" }}>{value}</div>
    </div>
  );
}

const headerStyle = {
  padding: "7px 8px",
  textAlign: "left" as const,
  fontSize: "9.5px",
  fontWeight: 700,
  color: "var(--gs-navy)",
  whiteSpace: "nowrap" as const,
  borderBottom: "1px solid rgba(28,43,94,0.12)",
};
const cellStyle = {
  padding: "7px 8px",
  fontSize: "10.5px",
  color: "var(--gs-slate)",
  whiteSpace: "nowrap" as const,
  borderBottom: "1px solid rgba(28,43,94,0.08)",
};
const depthCellStyle = { ...cellStyle, fontWeight: 700, color: "var(--gs-navy)" };

function formatM(value: number | null): string {
  return value === null ? "NOT AVAILABLE" : `${value.toFixed(3)} m`;
}
function displayZone(zoneId: string): string {
  return zoneId.startsWith("tyrone_") ? zoneId.replace("tyrone_", "").toUpperCase() : zoneId || "—";
}

import { Info, Loader2 } from "lucide-react";
import { useState } from "react";

import {
  runOperatorRecordedDepth,
  type OperatorRecordedDepthResult,
} from "../api/operatorRecordedDepth";

interface OperatorLocalDepthPanelProps {
  runId: string;
  operatorAccessToken?: string | null;
}

export function OperatorLocalDepthPanel({ runId, operatorAccessToken }: OperatorLocalDepthPanelProps) {
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OperatorRecordedDepthResult | null>(null);

  async function loadRecordedDepth() {
    if (!confirmed || loading) return;
    setLoading(true);
    try {
      const next = await runOperatorRecordedDepth(
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
            Recorded measured depth
          </span>
          <span className="font-mono" style={{ fontSize: "9px", fontWeight: 700, color: "var(--gs-blue)", backgroundColor: "var(--gs-blue-bg)", border: "1px solid var(--gs-blue-border)", padding: "1px 5px", borderRadius: "3px" }}>
            REVIEWED ZONES ONLY
          </span>
        </div>
        {loading && (
          <span className="flex items-center gap-1" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            <Loader2 size={11} className="animate-spin" /> Loading
          </span>
        )}
      </div>

      <div className="px-4 py-3 flex flex-col gap-3">
        <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
          Official recorded measurements for reviewed Tyrone plots that fall inside this run footprint. These metres are not predicted from this run, are not interpolated, and are never transferred to unknown zones.
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
          <span>I understand this is a lookup of reviewed official measurements, not a depth estimate for classifier objects or unknown areas.</span>
        </label>

        <div>
          <button
            type="button"
            onClick={() => void loadRecordedDepth()}
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
            Load reviewed recorded measurements
          </button>
        </div>

        {result?.outcome === "denied" && (
          <Message>Operator access is not available for this run.</Message>
        )}
        {result?.outcome === "error" && (
          <Message>{result.message ?? "Recorded measurement lookup could not be completed."}</Message>
        )}
        {result?.outcome === "completed" && result.status === "not_available" && (
          <Message>No reviewed Tyrone TP5/TP6 recorded-measurement zone is contained in this run footprint. No metre value is returned.</Message>
        )}

        {result?.outcome === "completed" && result.records.length > 0 && (
          <>
            <div className="overflow-auto" style={{ border: "1px solid rgba(28,43,94,0.12)", borderRadius: "4px" }}>
              <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "920px" }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--accent)" }}>
                    {["Reviewed plot", "Recorded mean", "95% CI", "Sample range", "n", "Design depth", "Measurement method", "Timing"].map((header) => (
                      <th key={header} className="font-mono" style={headerStyle}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.records.map((record) => (
                    <tr key={record.zoneId}>
                      <td style={cellStyle}>{record.plotId}</td>
                      <td style={depthCellStyle}>{formatM(record.recordedDepthMeanM)}</td>
                      <td style={cellStyle}>{formatRange(record.recordedDepthCi95LowM, record.recordedDepthCi95HighM)}</td>
                      <td style={cellStyle}>{formatRange(record.recordedSampleMinM, record.recordedSampleMaxM)}</td>
                      <td style={cellStyle}>{record.recordedSampleCount || "—"}</td>
                      <td style={cellStyle}>{formatM(record.reportedDesignDepthM)}</td>
                      <td style={cellStyle}>{record.measurementMethod || "—"}</td>
                      <td style={cellStyle}>{record.measurementTiming || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
              Source: official 2006 3X as-built report. Method: {result.methodKind}. Prediction = no · interpolation = no · extrapolation = no.
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function Message({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded px-3 py-2 flex items-start gap-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" }}>
      <Info size={13} className="shrink-0" style={{ marginTop: "2px" }} />
      <span style={{ fontSize: "11.5px", lineHeight: "1.5" }}>{children}</span>
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

const depthCellStyle = {
  ...cellStyle,
  fontWeight: 700,
  color: "var(--gs-navy)",
};

function formatM(value: number | null): string {
  return value === null ? "NOT AVAILABLE" : `${value.toFixed(3)} m`;
}

function formatRange(low: number | null, high: number | null): string {
  return low === null || high === null ? "NOT AVAILABLE" : `${low.toFixed(3)}–${high.toFixed(3)} m`;
}

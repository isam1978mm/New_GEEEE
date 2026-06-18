import { useEffect, useState } from "react";

import {
  getH5OperatorAggregateSummary,
  type H5OperatorAggregateSummary,
  type H5OperatorSummaryResponse,
} from "../api/h5OperatorSummary";
import { useOperatorAccessToken } from "./OperatorSessionContext";

interface H5OperatorAggregateSummaryPanelProps {
  operatorAccessToken?: string | null;
}

export function H5OperatorAggregateSummaryPanel({ operatorAccessToken }: H5OperatorAggregateSummaryPanelProps) {
  const contextOperatorAccessToken = useOperatorAccessToken();
  const resolvedOperatorAccessToken = operatorAccessToken ?? contextOperatorAccessToken;
  const [result, setResult] = useState<H5OperatorSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadSummary() {
      setLoading(true);
      const nextResult = await getH5OperatorAggregateSummary({ accessToken: resolvedOperatorAccessToken });
      if (!cancelled) {
        setResult(nextResult);
        setLoading(false);
      }
    }
    void loadSummary();
    return () => {
      cancelled = true;
    };
  }, [resolvedOperatorAccessToken]);

  return (
    <section
      className="rounded-lg bg-card overflow-hidden mt-4"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <details open>
        <summary
          className="px-4 py-2"
          style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)", cursor: "pointer" }}
        >
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            H5 operator aggregate summary
          </span>
        </summary>

        <div className="px-4 py-3 flex flex-col gap-3">
          <div style={{ fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
            Operator-only aggregate view. It shows summary counts, score ranges, and score bands only. No row-level output, private paths, raw files, or overlays are exposed.
          </div>

          {loading && <StatusBox tone="neutral" message="Loading aggregate summary..." />}
          {!loading && result && <SummaryBody result={result} />}
        </div>
      </details>
    </section>
  );
}

function SummaryBody({ result }: { result: H5OperatorSummaryResponse }) {
  if (result.outcome === "denied") {
    return <StatusBox tone="warning" message={result.message || "Operator aggregate summary is not available."} />;
  }
  if (result.outcome === "error") {
    return <StatusBox tone="error" message={result.message || "Operator aggregate summary is temporarily unavailable."} />;
  }
  if (!result.summary) {
    return <StatusBox tone="neutral" message="No aggregate summary is available yet." />;
  }
  return <AggregateSummary summary={result.summary} />;
}

function AggregateSummary({ summary }: { summary: H5OperatorAggregateSummary }) {
  return (
    <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)", marginBottom: "6px" }}>
        Aggregate prediction summary
      </div>
      <dl className="grid gap-2" style={{ gridTemplateColumns: "max-content 1fr", fontSize: "11px", color: "var(--gs-slate)" }}>
        <dt style={labelStyle}>Rows</dt>
        <dd>{summary.totalRowCount}</dd>
        <dt style={labelStyle}>Feature columns</dt>
        <dd>{summary.featureColumnCount}</dd>
        <dt style={labelStyle}>Score range</dt>
        <dd>{formatScore(summary.scoreMin)} to {formatScore(summary.scoreMax)}</dd>
        <dt style={labelStyle}>Score mean</dt>
        <dd>{formatScore(summary.scoreMean)}</dd>
        <dt style={labelStyle}>Score bands</dt>
        <dd>{formatCounts(summary.scoreBandCounts)}</dd>
        <dt style={labelStyle}>Score band status</dt>
        <dd>{summary.scoreBandCountsStatus}</dd>
        <dt style={labelStyle}>Sources</dt>
        <dd>{formatCounts(summary.rowsBySource)}</dd>
        <dt style={labelStyle}>Splits</dt>
        <dd>{formatCounts(summary.rowsBySplit)}</dd>
        <dt style={labelStyle}>Output boundary</dt>
        <dd>
          row-level included: {summary.rowLevelOutputIncluded ? "yes" : "no"}; private paths included: {summary.privatePathsIncluded ? "yes" : "no"}; overlays: {summary.overlaysCreated ? "yes" : "no"}
        </dd>
      </dl>
      <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "8px" }}>
        HTTP servable files are not exposed from this panel. Raw outputs remain private outside Git.
      </div>
    </div>
  );
}

const labelStyle = { fontWeight: 600, color: "var(--gs-navy)" };

function formatScore(value: number | null): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(6) : "not reported";
}

function formatCounts(value: Record<string, number>): string {
  const entries = Object.entries(value);
  if (entries.length === 0) {
    return "not reported";
  }
  return entries.map(([key, count]) => `${key}: ${count}`).join(" · ");
}

function StatusBox({ tone, message }: { tone: "neutral" | "warning" | "error"; message: string }) {
  const styles = {
    neutral: { backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" },
    warning: { backgroundColor: "var(--gs-amber-bg)", border: "1px solid var(--gs-amber-border)", color: "var(--gs-slate)" },
    error: { backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)", color: "var(--gs-red)" },
  }[tone];

  return (
    <div className="rounded px-3 py-2" style={{ ...styles, fontSize: "11px", lineHeight: "1.5" }}>
      {message}
    </div>
  );
}

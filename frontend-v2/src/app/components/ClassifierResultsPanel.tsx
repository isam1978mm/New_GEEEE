import { Download, Info, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  classifierDownloadLinks,
  fetchClassifierObjects,
  fetchClassifierSummary,
  type ClassifierObjectRow,
  type ClassifierSummary,
} from "../api/classifierResults";

interface ClassifierResultsPanelProps {
  runId: string;
}

const NOTEBOOK_TERMINOLOGY = "ENTRANCE_SHAFT_TRACE, COMPACT_CHAMBER_POINT, CHAMBER_VOID_AREA, RING_CONTEXT_AREA, WEAK_CONTEXT_AREA, and BACKGROUND_AREA";

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  const [summary, setSummary] = useState<ClassifierSummary | null>(null);
  const [objects, setObjects] = useState<ClassifierObjectRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const downloadLinks = useMemo(() => classifierDownloadLinks(runId), [runId]);

  useEffect(() => {
    let cancelled = false;

    async function loadClassifierResults() {
      setLoading(true);
      setUnavailable(false);
      setSummary(null);
      setObjects([]);
      try {
        const [nextSummary, nextObjects] = await Promise.all([
          fetchClassifierSummary(runId),
          fetchClassifierObjects(runId).catch(() => []),
        ]);
        if (!cancelled) {
          setSummary(nextSummary);
          setObjects(nextObjects);
        }
      } catch (_error) {
        if (!cancelled) {
          setUnavailable(true);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadClassifierResults();
    return () => {
      cancelled = true;
    };
  }, [runId]);

  const scoreLevelEntries = Object.entries(summary?.classCounts ?? {})
    .filter(([, count]) => count > 0)
    .sort(([left], [right]) => left.localeCompare(right));

  return (
    <section
      className="rounded-lg bg-card overflow-hidden"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <div
        className="flex items-center justify-between px-4 py-2"
        style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <div className="flex items-center gap-2">
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            Classifier Results
          </span>
          <span
            className="font-mono"
            style={{
              fontSize: "9px",
              fontWeight: 700,
              color: "var(--gs-blue)",
              backgroundColor: "var(--gs-blue-bg)",
              border: "1px solid var(--gs-blue-border)",
              padding: "1px 5px",
              borderRadius: "3px",
              letterSpacing: "0.03em",
            }}
          >
            REDACTED_PUBLIC
          </span>
        </div>
        {loading && (
          <span className="flex items-center gap-1" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            <Loader2 size={11} className="animate-spin" />
            Loading
          </span>
        )}
      </div>

      <div className="px-4 py-3 flex flex-col gap-3">
        {unavailable && (
          <div
            className="rounded px-3 py-2 flex items-start gap-2"
            style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" }}
          >
            <Info size={13} className="shrink-0" style={{ marginTop: "2px" }} />
            <span style={{ fontSize: "11.5px", lineHeight: "1.5" }}>
              No classifier result is available for this run yet.
            </span>
          </div>
        )}

        {summary && (
          <>
            <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
              Screening-confidence view: rows use notebook terminology from score plus simple row/column shape. Treat this as an early review aid, about a 30% signal.
            </div>

            <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
              <Metric label="objects_found" value={String(summary.objectCount)} />
              <Metric label="clusters_found" value={String(summary.clusterCount)} />
              <Metric label="classifier_version" value={summary.classifierVersion} />
            </dl>

            <div>
              <SectionLabel>score levels</SectionLabel>
              <div className="grid gap-1.5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))" }}>
                {scoreLevelEntries.map(([classId]) => (
                  <div key={classId} className="font-mono" style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)" }}>
                    {scoreLevelLabel(classId)}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.1)" }}>
              <SectionLabel>notebook terminology labels</SectionLabel>
              <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
                Labels use the notebook structural language: {NOTEBOOK_TERMINOLOGY}.
              </div>
            </div>

            <div>
              <SectionLabel>score level counts</SectionLabel>
              {scoreLevelEntries.length === 0 ? (
                <div style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
                  No score-level entries reported.
                </div>
              ) : (
                <div className="grid gap-1.5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
                  {scoreLevelEntries.map(([classId, count]) => (
                    <div
                      key={classId}
                      className="rounded px-2 py-1.5 flex items-center justify-between"
                      style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.1)" }}
                    >
                      <span className="font-mono" style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)" }}>
                        {scoreLevelLabel(classId)}
                      </span>
                      <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-slate)" }}>
                        {count}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <details open>
              <summary className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em", cursor: "pointer" }}>
                All objects, sorted by score ({objects.length})
              </summary>
              <div className="mt-2 overflow-auto" style={{ maxHeight: "460px", border: "1px solid rgba(28,43,94,0.12)", borderRadius: "4px" }}>
                <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "1080px" }}>
                  <thead>
                    <tr style={{ backgroundColor: "var(--accent)" }}>
                      {[
                        "Object #",
                        "Cluster #",
                        "Score",
                        "Score level",
                        "Notebook label",
                        "Rule reason",
                        "Review order",
                        "Row start",
                        "Row end",
                        "Column start",
                        "Column end",
                      ].map((header) => (
                        <th key={header} className="font-mono" style={tableHeaderStyle}>{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {objects.map((row) => (
                      <tr key={`${row.objectId}-${row.clusterId}`}>
                        <td style={tableCellStyle}>{row.objectId}</td>
                        <td style={tableCellStyle}>{row.clusterId}</td>
                        <td style={tableCellStyle}>{row.score.toFixed(3)}</td>
                        <td style={tableCellStyle}>{row.scoreLevel}</td>
                        <td style={tableCellStyle}>{row.notebookLabel}</td>
                        <td style={tableCellStyle}>{row.ruleReason}</td>
                        <td style={tableCellStyle}>{row.reviewOrder}</td>
                        <td style={tableCellStyle}>{row.rowStart}</td>
                        <td style={tableCellStyle}>{row.rowEnd}</td>
                        <td style={tableCellStyle}>{row.columnStart}</td>
                        <td style={tableCellStyle}>{row.columnEnd}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </>
        )}

        <div className="flex flex-wrap gap-2">
          {downloadLinks.map((link) => (
            <a
              key={link.artifactName}
              href={link.downloadUrl}
              download={link.filename}
              className="flex items-center gap-1 px-2.5 py-1 rounded"
              style={{
                fontSize: "11px",
                fontWeight: 600,
                color: "var(--gs-navy)",
                backgroundColor: "var(--accent)",
                border: "1px solid rgba(28,43,94,0.15)",
                textDecoration: "none",
              }}
            >
              <Download size={10} />
              {link.label}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="rounded px-3 py-2"
      style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.1)" }}
    >
      <dt className="font-mono" style={{ fontSize: "9.5px", color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
        {label}
      </dt>
      <dd className="font-mono truncate" style={{ fontSize: "13px", fontWeight: 700, color: "var(--gs-navy)", marginTop: "2px" }}>
        {value}
      </dd>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-mono mb-1.5" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
      {children}
    </div>
  );
}

function scoreLevelLabel(classId: string): string {
  const labels: Record<string, string> = {
    Class_A: "Very high (Class_A)",
    Class_B: "High (Class_B)",
    Class_C: "Strong (Class_C)",
    Class_D: "Medium-high (Class_D)",
    Class_E: "Medium (Class_E)",
    Class_F: "Lower-medium (Class_F)",
    Class_G: "Background (Class_G)",
  };
  return labels[classId] || classId;
}

const tableHeaderStyle = {
  padding: "7px 8px",
  borderBottom: "1px solid rgba(28,43,94,0.14)",
  textAlign: "left",
  fontSize: "10px",
  color: "var(--gs-navy)",
  whiteSpace: "nowrap",
} as const;

const tableCellStyle = {
  padding: "6px 8px",
  borderBottom: "1px solid rgba(28,43,94,0.08)",
  fontSize: "11px",
  color: "var(--gs-slate)",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  whiteSpace: "nowrap",
} as const;

import { Download, Info, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  buildLegacyFinalAreaFindings,
  classifierDownloadLinks,
  easyFindingName,
  fetchClassifierObjects,
  fetchClassifierSummary,
  type ClassifierObjectRow,
  type ClassifierSummary,
} from "../api/classifierResults";
import {
  fetchOperatorLocalDepthResult,
  type OperatorLocalDepthEstimate,
  type OperatorLocalDepthResult,
} from "../api/operatorLocalDepth";
import { useOperatorAccessToken } from "./OperatorSessionContext";

interface ClassifierResultsPanelProps {
  runId: string;
}

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  const operatorAccessToken = useOperatorAccessToken();
  const [summary, setSummary] = useState<ClassifierSummary | null>(null);
  const [objects, setObjects] = useState<ClassifierObjectRow[]>([]);
  const [depthResult, setDepthResult] = useState<OperatorLocalDepthResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const downloadLinks = useMemo(() => classifierDownloadLinks(runId), [runId]);
  const finalAreaFindings = useMemo(
    () => summary?.finalAreaFindings ?? buildLegacyFinalAreaFindings(objects, runId),
    [objects, runId, summary],
  );
  const depthByCandidateId = useMemo(
    () => new Map((depthResult?.estimates ?? []).map((estimate) => [estimate.candidateId, estimate])),
    [depthResult],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadClassifierResults() {
      setLoading(true);
      setUnavailable(false);
      setSummary(null);
      setObjects([]);
      setDepthResult(null);
      try {
        const [nextSummary, nextObjects, nextDepth] = await Promise.all([
          fetchClassifierSummary(runId),
          fetchClassifierObjects(runId).catch(() => []),
          fetchOperatorLocalDepthResult(runId, { accessToken: operatorAccessToken }).catch(() => null),
        ]);
        if (!cancelled) {
          setSummary(nextSummary);
          setObjects(nextObjects);
          setDepthResult(nextDepth);
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
  }, [runId, operatorAccessToken]);

  useEffect(() => {
    let cancelled = false;

    async function refreshDepthResult() {
      const nextDepth = await fetchOperatorLocalDepthResult(runId, {
        accessToken: operatorAccessToken,
      }).catch(() => null);
      if (!cancelled) {
        setDepthResult(nextDepth);
      }
    }

    function handleDepthUpdated(event: Event) {
      const detail = (event as CustomEvent<{ runId?: string }>).detail;
      if (!detail?.runId || detail.runId === runId) {
        void refreshDepthResult();
      }
    }

    window.addEventListener("operator-local-depth-updated", handleDepthUpdated);
    return () => {
      cancelled = true;
      window.removeEventListener("operator-local-depth-updated", handleDepthUpdated);
    };
  }, [runId, operatorAccessToken]);

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
              App screening scores rank objects for review. They are not measured probabilities or physical confirmation.
            </div>

            <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
              <Metric label="objects_found" value={String(summary.objectCount)} />
              <Metric label="clusters_found" value={String(summary.clusterCount)} />
              <Metric label="classifier_version" value={summary.classifierVersion} />
            </dl>

            {finalAreaFindings && (
              <div
                className="rounded px-3 py-3"
                style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.14)" }}
              >
                <SectionLabel>Final area findings summary</SectionLabel>
                <div style={{ fontSize: "12px", color: "var(--gs-navy)", lineHeight: "1.6", fontWeight: 600 }}>
                  {finalAreaFindings.summaryTextEasyEnglish}
                </div>
                {finalAreaFindings.rankedFindings.length > 0 && (
                  <div className="mt-2 grid gap-1.5">
                    {finalAreaFindings.rankedFindings.slice(0, 5).map((finding, index) => (
                      <div
                        key={finding.findingLabel}
                        className="flex items-center justify-between gap-3 rounded px-2 py-1.5"
                        style={{ backgroundColor: "var(--card)", border: "1px solid rgba(28,43,94,0.1)" }}
                      >
                        <span style={{ fontSize: "11px", color: "var(--gs-navy)" }}>
                          {index + 1}. {easyFindingName(finding.findingLabel)}
                        </span>
                        <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-slate)", whiteSpace: "nowrap" }}>
                          App score {Math.round(finding.findingScore * 100)}% · {finding.supportingCandidateCount} candidate{finding.supportingCandidateCount === 1 ? "" : "s"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-2" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                  {depthSummaryText(depthResult)}
                </div>
              </div>
            )}

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
                <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "1380px" }}>
                  <thead>
                    <tr style={{ backgroundColor: "var(--accent)" }}>
                      {[
                        "Object #",
                        "Cluster #",
                        "Score",
                        "Score level",
                        "Finding label",
                        "Depth range",
                        "Best depth",
                        "Depth status",
                        "Finding reason",
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
                    {objects.map((row) => {
                      const estimate = depthByCandidateId.get(candidateIdForObject(row.objectId));
                      return (
                        <tr key={`${row.objectId}-${row.clusterId}`}>
                          <td style={tableCellStyle}>{row.objectId}</td>
                          <td style={tableCellStyle}>{row.clusterId}</td>
                          <td style={tableCellStyle}>{row.score.toFixed(3)}</td>
                          <td style={tableCellStyle}>{row.scoreLevel}</td>
                          <td style={tableCellStyle}>{row.findingLabel}</td>
                          <td style={tableCellStyle}>{depthRangeText(estimate)}</td>
                          <td style={tableCellStyle}>{bestDepthText(estimate)}</td>
                          <td style={tableCellStyle}>{depthStatusText(estimate, depthResult)}</td>
                          <td style={tableCellStyle}>{row.findingReason}</td>
                          <td style={tableCellStyle}>{row.reviewOrder}</td>
                          <td style={tableCellStyle}>{row.rowStart}</td>
                          <td style={tableCellStyle}>{row.rowEnd}</td>
                          <td style={tableCellStyle}>{row.columnStart}</td>
                          <td style={tableCellStyle}>{row.columnEnd}</td>
                        </tr>
                      );
                    })}
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

function candidateIdForObject(objectId: string): string {
  return `finding-object-${objectId}`;
}

function depthSummaryText(result: OperatorLocalDepthResult | null): string {
  if (result?.outcome === "completed") {
    return `Depth estimates: ${result.estimatedCount} of ${result.candidateCount} findings received a local metre range; ${result.insufficientDataCount + result.notAvailableCount} received no estimate.`;
  }
  return "Depth estimates: measured-anchor calibration has not been completed for this run.";
}

function depthRangeText(estimate: OperatorLocalDepthEstimate | undefined): string {
  if (!estimate || estimate.estimatedDepthMinM === null || estimate.estimatedDepthMaxM === null) {
    return "—";
  }
  return `${estimate.estimatedDepthMinM.toFixed(3)}–${estimate.estimatedDepthMaxM.toFixed(3)} m`;
}

function bestDepthText(estimate: OperatorLocalDepthEstimate | undefined): string {
  return !estimate || estimate.estimatedDepthBestM === null
    ? "—"
    : `${estimate.estimatedDepthBestM.toFixed(3)} m`;
}

function depthStatusText(
  estimate: OperatorLocalDepthEstimate | undefined,
  result: OperatorLocalDepthResult | null,
): string {
  if (estimate) {
    return estimate.depthStatus;
  }
  return result?.outcome === "completed" ? "not_available" : "not_calibrated";
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

function SectionLabel({ children }: { children: ReactNode }) {
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

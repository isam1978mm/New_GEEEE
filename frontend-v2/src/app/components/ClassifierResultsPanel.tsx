import { Download, Info, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  anomalyDownloadUrl,
  fetchAnomalyObjects,
  summarizeAnomalyObjects,
  summarizeAnomalyZones,
  type AnomalyObjectRow,
} from "../api/anomalyResults";
import {
  buildLegacyFinalAreaFindings,
  classifierDownloadLinks,
  easyFindingName,
  fetchClassifierObjects,
  fetchClassifierSummary,
  type ClassifierObjectRow,
  type ClassifierSummary,
} from "../api/classifierResults";

interface ClassifierResultsPanelProps {
  runId: string;
}

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  const [summary, setSummary] = useState<ClassifierSummary | null>(null);
  const [objects, setObjects] = useState<ClassifierObjectRow[]>([]);
  const [anomalyObjects, setAnomalyObjects] = useState<AnomalyObjectRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [classifierUnavailable, setClassifierUnavailable] = useState(false);
  const [anomalyUnavailable, setAnomalyUnavailable] = useState(false);

  const downloadLinks = useMemo(() => classifierDownloadLinks(runId), [runId]);
  const finalAreaFindings = useMemo(
    () => summary?.finalAreaFindings ?? buildLegacyFinalAreaFindings(objects, runId),
    [objects, runId, summary],
  );
  const anomalySummary = useMemo(() => summarizeAnomalyObjects(anomalyObjects), [anomalyObjects]);
  const anomalyZones = useMemo(() => summarizeAnomalyZones(anomalyObjects), [anomalyObjects]);

  useEffect(() => {
    let cancelled = false;

    async function loadResults() {
      setLoading(true);
      setSummary(null);
      setObjects([]);
      setAnomalyObjects([]);
      setClassifierUnavailable(false);
      setAnomalyUnavailable(false);

      const [classifierResult, anomalyResult] = await Promise.allSettled([
        Promise.all([
          fetchClassifierSummary(runId),
          fetchClassifierObjects(runId).catch(() => []),
        ]),
        fetchAnomalyObjects(runId),
      ]);

      if (cancelled) {
        return;
      }

      if (classifierResult.status === "fulfilled") {
        setSummary(classifierResult.value[0]);
        setObjects(classifierResult.value[1]);
      } else {
        setClassifierUnavailable(true);
      }

      if (anomalyResult.status === "fulfilled") {
        setAnomalyObjects(anomalyResult.value);
      } else {
        setAnomalyUnavailable(true);
      }

      setLoading(false);
    }

    void loadResults();
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
          <span className="font-mono" style={sectionTitleStyle}>Classifier Results</span>
          <Badge text="REDACTED_PUBLIC" />
        </div>
        {loading && (
          <span className="flex items-center gap-1" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            <Loader2 size={11} className="animate-spin" />
            Loading
          </span>
        )}
      </div>

      <div className="px-4 py-3 flex flex-col gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <SectionLabel>Radar anomaly review</SectionLabel>
            <Badge text="NOT DEPTH" warning />
          </div>

          <div
            className="rounded px-3 py-2 flex items-start gap-2 mb-3"
            style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" }}
          >
            <Info size={13} className="shrink-0" style={{ marginTop: "2px" }} />
            <span style={{ fontSize: "11.5px", lineHeight: "1.5" }}>
              These are unitless, within-run PCA anomaly scores. A higher score means an object was more unusual than other valid pixels in this run. It is not a probability, not physical confirmation, not a measured change, and not a depth estimate.
            </span>
          </div>

          {anomalyUnavailable ? (
            <UnavailableNotice text="No radar anomaly result is available for this run yet." />
          ) : (
            <>
              <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
                <Metric label="objects_found" value={String(anomalySummary.objectCount)} />
                <Metric label="total_object_area_px" value={String(anomalySummary.totalAreaPixels)} />
                <Metric label="median_mean_anomaly" value={formatScore(anomalySummary.medianObjectMean)} />
                <Metric label="strongest_peak_anomaly" value={formatScore(anomalySummary.strongestPeak)} />
              </dl>

              {anomalyZones.length > 0 && (
                <div className="rounded px-3 py-3 mt-3" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.14)" }}>
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <SectionLabel>Cluster-zone comparison and disturbance review</SectionLabel>
                    <Badge text="WITHIN RUN" />
                    <Badge text="NOT MEASURED CHANGE" warning />
                  </div>
                  <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5", marginBottom: "10px" }}>
                    Existing anomaly objects are grouped by cluster ID and ranked only against other clusters in this run. The relative disturbance-review tier is a review priority, not measured displacement, settlement, temporal surface change, physical confirmation, or depth.
                  </p>

                  <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
                    <Metric label="cluster_zones" value={String(anomalyZones.length)} />
                    <Metric label="highest_review_zone" value={anomalyZones[0]?.zoneId ?? "Not available"} />
                    <Metric label="leading_area_share" value={formatPercent(anomalyZones[0]?.areaShare ?? null)} />
                    <Metric label="surface_change_status" value="Not available" />
                  </dl>

                  <div className="rounded px-3 py-2 flex items-start gap-2 mt-3" style={{ backgroundColor: "var(--card)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" }}>
                    <Info size={13} className="shrink-0" style={{ marginTop: "2px" }} />
                    <span style={{ fontSize: "11.5px", lineHeight: "1.5" }}>
                      A validated before/after radar pair is required for a measured surface-change result. This single-run object artifact cannot provide one.
                    </span>
                  </div>

                  <div className="mt-3 overflow-auto" style={tableContainerStyle}>
                    <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "820px" }}>
                      <thead>
                        <tr style={{ backgroundColor: "var(--card)" }}>
                          {["Cluster zone", "Objects", "Area px", "Area share", "Weighted mean anomaly", "Peak anomaly", "Relative disturbance review"].map((header) => (
                            <th key={header} className="font-mono" style={tableHeaderStyle}>{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {anomalyZones.map((zone) => (
                          <tr key={zone.zoneId}>
                            <td style={tableCellStyle}>{zone.zoneId}</td>
                            <td style={tableCellStyle}>{zone.objectCount}</td>
                            <td style={tableCellStyle}>{zone.totalAreaPixels}</td>
                            <td style={tableCellStyle}>{formatPercent(zone.areaShare)}</td>
                            <td style={tableCellStyle}>{zone.areaWeightedMeanAnomaly.toFixed(3)}</td>
                            <td style={tableCellStyle}>{zone.strongestPeak.toFixed(3)}</td>
                            <td style={tableCellStyle}>{zone.relativeDisturbanceReview}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {anomalyObjects.length > 0 && (
                <details className="mt-3" open>
                  <summary className="font-mono" style={detailsSummaryStyle}>
                    Objects ranked by peak anomaly ({anomalyObjects.length})
                  </summary>
                  <div className="mt-2 overflow-auto" style={tableContainerStyle}>
                    <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "620px" }}>
                      <thead>
                        <tr style={{ backgroundColor: "var(--accent)" }}>
                          {["Object #", "Cluster #", "Area px", "Mean anomaly", "Peak anomaly"].map((header) => (
                            <th key={header} className="font-mono" style={tableHeaderStyle}>{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {anomalyObjects.slice(0, 50).map((row) => (
                          <tr key={`${row.objectId}-${row.clusterId}`}>
                            <td style={tableCellStyle}>{row.objectId}</td>
                            <td style={tableCellStyle}>{row.clusterId}</td>
                            <td style={tableCellStyle}>{row.areaPixels}</td>
                            <td style={tableCellStyle}>{row.meanAnomaly.toFixed(3)}</td>
                            <td style={tableCellStyle}>{row.peakAnomaly.toFixed(3)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              )}

              <div className="mt-2 flex items-center justify-between gap-3 flex-wrap">
                <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                  Depth estimate: not available. Global and local numerical calibration remain disabled.
                </span>
                <DownloadLink href={anomalyDownloadUrl(runId)} label="Download anomaly object CSV" />
              </div>
            </>
          )}
        </div>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "14px" }}>
          <SectionLabel>Classifier results</SectionLabel>
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5", marginBottom: "10px" }}>
            App screening scores rank objects for review. They are not measured probabilities or physical confirmation.
          </p>

          {classifierUnavailable && <UnavailableNotice text="No classifier result is available for this run yet." />}

          {summary && (
            <>
              <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
                <Metric label="objects_found" value={String(summary.objectCount)} />
                <Metric label="clusters_found" value={String(summary.clusterCount)} />
                <Metric label="classifier_version" value={summary.classifierVersion} />
              </dl>

              {finalAreaFindings && (
                <div className="rounded px-3 py-3 mt-3" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.14)" }}>
                  <SectionLabel>Final area findings summary</SectionLabel>
                  <div style={{ fontSize: "12px", color: "var(--gs-navy)", lineHeight: "1.6", fontWeight: 600 }}>
                    {finalAreaFindings.summaryTextEasyEnglish}
                  </div>
                  {finalAreaFindings.rankedFindings.length > 0 && (
                    <div className="mt-2 grid gap-1.5">
                      {finalAreaFindings.rankedFindings.slice(0, 5).map((finding, index) => (
                        <div key={finding.findingLabel} className="flex items-center justify-between gap-3 rounded px-2 py-1.5" style={{ backgroundColor: "var(--card)", border: "1px solid rgba(28,43,94,0.1)" }}>
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
                    Depth estimate: not available.
                  </div>
                </div>
              )}

              <div className="mt-3">
                <SectionLabel>Score level counts</SectionLabel>
                {scoreLevelEntries.length === 0 ? (
                  <div style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>No score-level entries reported.</div>
                ) : (
                  <div className="grid gap-1.5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
                    {scoreLevelEntries.map(([classId, count]) => (
                      <div key={classId} className="rounded px-2 py-1.5 flex items-center justify-between" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.1)" }}>
                        <span className="font-mono" style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)" }}>{scoreLevelLabel(classId)}</span>
                        <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-slate)" }}>{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <details className="mt-3">
                <summary className="font-mono" style={detailsSummaryStyle}>Classifier objects ({objects.length})</summary>
                <div className="mt-2 overflow-auto" style={tableContainerStyle}>
                  <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "820px" }}>
                    <thead>
                      <tr style={{ backgroundColor: "var(--accent)" }}>
                        {["Object #", "Cluster #", "Score", "Score level", "Finding", "Review order"].map((header) => (
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
                          <td style={tableCellStyle}>{row.findingLabel}</td>
                          <td style={tableCellStyle}>{row.reviewOrder}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </>
          )}

          <div className="flex flex-wrap gap-2 mt-3">
            {downloadLinks.map((link) => (
              <DownloadLink key={link.artifactName} href={link.downloadUrl} label={link.label} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Badge({ text, warning = false }: { text: string; warning?: boolean }) {
  return (
    <span className="font-mono" style={{
      fontSize: "9px",
      fontWeight: 700,
      color: warning ? "var(--gs-amber)" : "var(--gs-blue)",
      backgroundColor: warning ? "rgba(217,119,6,0.08)" : "var(--gs-blue-bg)",
      border: `1px solid ${warning ? "rgba(217,119,6,0.25)" : "var(--gs-blue-border)"}`,
      padding: "1px 5px",
      borderRadius: "3px",
      letterSpacing: "0.03em",
    }}>{text}</span>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.1)" }}>
      <dt className="font-mono" style={{ fontSize: "9.5px", color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</dt>
      <dd className="font-mono truncate" style={{ fontSize: "13px", fontWeight: 700, color: "var(--gs-navy)", marginTop: "2px" }}>{value}</dd>
    </div>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return <div className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em" }}>{children}</div>;
}

function UnavailableNotice({ text }: { text: string }) {
  return (
    <div className="rounded px-3 py-2 flex items-start gap-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" }}>
      <Info size={13} className="shrink-0" style={{ marginTop: "2px" }} />
      <span style={{ fontSize: "11.5px", lineHeight: "1.5" }}>{text}</span>
    </div>
  );
}

function DownloadLink({ href, label }: { href: string; label: string }) {
  return (
    <a href={href} download className="flex items-center gap-1 px-2.5 py-1 rounded" style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)", backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.15)", textDecoration: "none" }}>
      <Download size={10} />
      {label}
    </a>
  );
}

function formatScore(value: number | null): string {
  return value === null ? "Not available" : value.toFixed(3);
}

function formatPercent(value: number | null): string {
  return value === null ? "Not available" : `${(value * 100).toFixed(1)}%`;
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

const sectionTitleStyle = {
  fontSize: "10px",
  fontWeight: 700,
  color: "var(--gs-navy)",
  textTransform: "uppercase",
  letterSpacing: "0.07em",
} as const;

const detailsSummaryStyle = {
  fontSize: "10px",
  fontWeight: 700,
  color: "var(--gs-navy)",
  textTransform: "uppercase",
  letterSpacing: "0.07em",
  cursor: "pointer",
} as const;

const tableContainerStyle = {
  maxHeight: "420px",
  border: "1px solid rgba(28,43,94,0.12)",
  borderRadius: "4px",
} as const;

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

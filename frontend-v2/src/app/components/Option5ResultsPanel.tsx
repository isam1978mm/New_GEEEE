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
  fetchSurfaceChangeSummary,
  type SurfaceChangeSummary,
} from "../api/surfaceChangeResults";

interface Option5ResultsPanelProps {
  runId: string;
}

export function Option5ResultsPanel({ runId }: Option5ResultsPanelProps) {
  const [anomalyObjects, setAnomalyObjects] = useState<AnomalyObjectRow[]>([]);
  const [surfaceChange, setSurfaceChange] = useState<SurfaceChangeSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [anomalyUnavailable, setAnomalyUnavailable] = useState(false);
  const [surfaceChangeUnavailable, setSurfaceChangeUnavailable] = useState(false);

  const anomalySummary = useMemo(
    () => summarizeAnomalyObjects(anomalyObjects),
    [anomalyObjects],
  );
  const anomalyZones = useMemo(
    () => summarizeAnomalyZones(anomalyObjects),
    [anomalyObjects],
  );
  const firstReviewZone = anomalyZones[0] ?? null;

  useEffect(() => {
    let cancelled = false;

    async function loadOption5Results() {
      setLoading(true);
      setAnomalyObjects([]);
      setSurfaceChange(null);
      setAnomalyUnavailable(false);
      setSurfaceChangeUnavailable(false);

      const [anomalyResult, surfaceChangeResult] = await Promise.allSettled([
        fetchAnomalyObjects(runId),
        fetchSurfaceChangeSummary(runId),
      ]);

      if (cancelled) {
        return;
      }

      if (anomalyResult.status === "fulfilled") {
        setAnomalyObjects(anomalyResult.value);
      } else {
        setAnomalyUnavailable(true);
      }

      if (surfaceChangeResult.status === "fulfilled") {
        setSurfaceChange(surfaceChangeResult.value);
      } else {
        setSurfaceChangeUnavailable(true);
      }

      setLoading(false);
    }

    void loadOption5Results();
    return () => {
      cancelled = true;
    };
  }, [runId]);

  return (
    <section
      className="rounded-lg bg-card overflow-hidden"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <div
        className="flex items-center justify-between px-4 py-2"
        style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono" style={sectionTitleStyle}>Option 5 Results</span>
          <Badge text="REVIEW PRIORITY" />
          <Badge text="NOT DEPTH" warning />
        </div>
        {loading && (
          <span className="flex items-center gap-1" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            <Loader2 size={11} className="animate-spin" />
            Loading
          </span>
        )}
      </div>

      <div className="px-4 py-3 flex flex-col gap-4">
        <div
          className="rounded px-3 py-3"
          style={{ backgroundColor: "var(--gs-blue-bg)", border: "1px solid var(--gs-blue-border)" }}
        >
          <SectionLabel>Decision you can take</SectionLabel>
          <div style={{ fontSize: "12px", color: "var(--gs-navy)", lineHeight: "1.6", fontWeight: 600 }}>
            {decisionText({
              anomalyUnavailable,
              firstReviewZoneId: firstReviewZone?.zoneId ?? null,
              surfaceChange,
              surfaceChangeUnavailable,
            })}
          </div>
          <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5", marginTop: "6px" }}>
            Option 5 only helps choose what area to review first. It does not identify what is underground and it does not provide excavation depth.
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <SectionLabel>Radar anomaly review</SectionLabel>
            <Badge text="WITHIN THIS RUN" />
          </div>

          {anomalyUnavailable ? (
            <UnavailableNotice text="No Option 5 anomaly result is available for this run." />
          ) : (
            <>
              <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
                <Metric label="areas to review" value={String(anomalySummary.objectCount)} />
                <Metric label="zone groups" value={String(anomalyZones.length)} />
                <Metric label="review first" value={firstReviewZone?.zoneId ?? "None"} />
                <Metric label="surface comparison" value={surfaceChangeStatus(surfaceChange, surfaceChangeUnavailable)} />
              </dl>

              {anomalyZones.length > 0 ? (
                <div className="mt-3 overflow-auto" style={tableContainerStyle}>
                  <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "680px" }}>
                    <thead>
                      <tr style={{ backgroundColor: "var(--accent)" }}>
                        {["Review order", "Zone", "Priority", "Unusual areas", "Share of anomaly area"].map((header) => (
                          <th key={header} className="font-mono" style={tableHeaderStyle}>{header}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {anomalyZones.map((zone, index) => (
                        <tr key={zone.zoneId}>
                          <td style={tableCellStyle}>{index + 1}</td>
                          <td style={tableCellStyle}>{zone.zoneId}</td>
                          <td style={tableCellStyle}>{plainPriority(zone.relativeDisturbanceReview)}</td>
                          <td style={tableCellStyle}>{zone.objectCount}</td>
                          <td style={tableCellStyle}>{formatPercent(zone.areaShare)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <UnavailableNotice text="No anomaly zones were produced for this run." />
              )}

              <details className="mt-3">
                <summary className="font-mono" style={detailsSummaryStyle}>
                  Technical Option 5 numbers
                </summary>
                <div className="rounded px-3 py-2 mt-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}>
                  <p style={{ fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.5", marginBottom: "8px" }}>
                    These unitless numbers explain the ranking only. They are not probabilities, measurements, settlement, physical confirmation, or depth.
                  </p>
                  <div className="overflow-auto" style={tableContainerStyle}>
                    <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "760px" }}>
                      <thead>
                        <tr style={{ backgroundColor: "var(--card)" }}>
                          {["Zone", "Area pixels", "Area-weighted anomaly", "Peak anomaly", "Relative review tier"].map((header) => (
                            <th key={header} className="font-mono" style={tableHeaderStyle}>{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {anomalyZones.map((zone) => (
                          <tr key={zone.zoneId}>
                            <td style={tableCellStyle}>{zone.zoneId}</td>
                            <td style={tableCellStyle}>{zone.totalAreaPixels}</td>
                            <td style={tableCellStyle}>{zone.areaWeightedMeanAnomaly.toFixed(3)}</td>
                            <td style={tableCellStyle}>{zone.strongestPeak.toFixed(3)}</td>
                            <td style={tableCellStyle}>{zone.relativeDisturbanceReview}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </details>

              <div className="mt-3 flex items-center justify-between gap-3 flex-wrap">
                <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                  Depth estimate: not available from Option 5.
                </span>
                <DownloadLink href={anomalyDownloadUrl(runId)} label="Download Option 5 anomaly CSV" />
              </div>
            </>
          )}
        </div>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "14px" }}>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <SectionLabel>Dual-window radar surface-change review</SectionLabel>
            <Badge text="RADAR BACKSCATTER ONLY" />
            <Badge text="NOT DEPTH OR SETTLEMENT" warning />
          </div>
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5", marginBottom: "10px" }}>
            This compares compatible before and after Sentinel-1 radar returns. Moisture, vegetation and surface roughness may contribute. It is not measured displacement, settlement, physical confirmation, or depth.
          </p>

          {surfaceChangeUnavailable || surfaceChange === null ? (
            <UnavailableNotice text="No dual-window radar surface-change summary exists for this run. Older runs must be rerun after this stage is enabled. A validated before/after radar pair is required. This single-run object artifact cannot provide one." />
          ) : surfaceChange.status === "not_available" ? (
            <UnavailableNotice text={`Surface-change review abstained: ${surfaceChangeReason(surfaceChange.reason)}.`} />
          ) : (
            <>
              <div
                className="rounded px-3 py-3"
                style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.14)" }}
              >
                <SectionLabel>What this means</SectionLabel>
                <div style={{ fontSize: "12px", color: "var(--gs-navy)", lineHeight: "1.6", fontWeight: 600 }}>
                  Radar returns changed enough for {formatPercent(surfaceChange.change_review_pixel_fraction ?? null)} of compatible pixels to meet this run's review threshold. Check those changes against maps, weather, vegetation, construction records, or field observations before acting.
                </div>
              </div>
              <details className="mt-3">
                <summary className="font-mono" style={detailsSummaryStyle}>Technical surface-change numbers</summary>
                <dl className="grid gap-2 mt-2" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
                  <Metric label="review_pixel_fraction" value={formatPercent(surfaceChange.change_review_pixel_fraction ?? null)} />
                  <Metric label="review_threshold_db" value={formatDb(surfaceChange.review_threshold_db)} />
                  <Metric label="valid_pixel_fraction" value={formatPercent(surfaceChange.valid_pixel_fraction ?? null)} />
                  <Metric label="p95_abs_delta_db" value={formatDb(surfaceChange.p95_absolute_centered_delta_db)} />
                </dl>
                <dl className="grid gap-2 mt-2" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
                  <Metric label="before window" value={formatWindow(surfaceChange.before_window)} />
                  <Metric label="after window" value={formatWindow(surfaceChange.after_window)} />
                  <Metric label="pair support" value={`${surfaceChange.before_pair_count ?? "?"} before / ${surfaceChange.after_pair_count ?? "?"} after`} />
                </dl>
              </details>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

function decisionText({
  anomalyUnavailable,
  firstReviewZoneId,
  surfaceChange,
  surfaceChangeUnavailable,
}: {
  anomalyUnavailable: boolean;
  firstReviewZoneId: string | null;
  surfaceChange: SurfaceChangeSummary | null;
  surfaceChangeUnavailable: boolean;
}): string {
  if (anomalyUnavailable || firstReviewZoneId === null) {
    return "Option 5 cannot recommend a first review area for this run.";
  }
  if (!surfaceChangeUnavailable && surfaceChange?.status === "available") {
    return `Review zone ${firstReviewZoneId} first, then compare it with the available before/after radar-change result and independent records.`;
  }
  return `Review zone ${firstReviewZoneId} first. This is only a relative priority inside this run; no temporal radar-change confirmation is available.`;
}

function surfaceChangeStatus(summary: SurfaceChangeSummary | null, unavailable: boolean): string {
  if (unavailable || summary === null) {
    return "Not available";
  }
  return summary.status === "available" ? "Available" : "Abstained";
}

function plainPriority(value: string): string {
  const labels: Record<string, string> = {
    higher: "Review earlier",
    medium: "Review after higher zones",
    lower: "Review later",
    "only zone": "Only zone",
  };
  return labels[value] ?? value;
}

function surfaceChangeReason(reason: string | undefined): string {
  const reasons: Record<string, string> = {
    insufficient_compatible_pixels: "not enough compatible pixels remained after the radar checks",
    insufficient_after_pairs: "the later period did not contain enough ascending and descending radar pairs",
    insufficient_before_pairs: "the earlier period did not contain enough ascending and descending radar pairs",
    orbit_signature_mismatch: "the earlier and later radar orbit coverage did not match",
    configured_after_window_too_short: "the configured later period was too short",
    surface_change_prerequisite_failed: "a required radar input was unavailable",
    surface_change_processing_unavailable: "the radar comparison could not be completed",
  };
  return reasons[reason ?? ""] ?? "the scientific compatibility checks were not satisfied";
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

function formatPercent(value: number | null): string {
  return value === null ? "Not available" : `${(value * 100).toFixed(1)}%`;
}

function formatDb(value: number | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(2)} dB` : "Not available";
}

function formatWindow(window: { start: string; end: string } | undefined): string {
  return window ? `${window.start} to ${window.end}` : "Not available";
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

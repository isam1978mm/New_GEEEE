import { Download, Info, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  classifierDownloadLinks,
  fetchClassifierSummary,
  type ClassifierSummary,
} from "../api/classifierResults";

interface ClassifierResultsPanelProps {
  runId: string;
}

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  const [summary, setSummary] = useState<ClassifierSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const downloadLinks = useMemo(() => classifierDownloadLinks(runId), [runId]);

  useEffect(() => {
    let cancelled = false;

    async function loadSummary() {
      setLoading(true);
      setUnavailable(false);
      setSummary(null);
      try {
        const nextSummary = await fetchClassifierSummary(runId);
        if (!cancelled) {
          setSummary(nextSummary);
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

    void loadSummary();
    return () => {
      cancelled = true;
    };
  }, [runId]);

  const classCountEntries = Object.entries(summary?.classCounts ?? {}).sort(([left], [right]) =>
    left.localeCompare(right),
  );

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
            <dl className="grid gap-2" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
              <Metric label="object_count" value={String(summary.objectCount)} />
              <Metric label="cluster_count" value={String(summary.clusterCount)} />
              <Metric label="classifier_version" value={summary.classifierVersion} />
            </dl>

            <div>
              <div
                className="font-mono mb-1.5"
                style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em" }}
              >
                class_counts
              </div>
              {classCountEntries.length === 0 ? (
                <div style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
                  No class_counts entries reported.
                </div>
              ) : (
                <div className="grid gap-1.5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))" }}>
                  {classCountEntries.map(([classId, count]) => (
                    <div
                      key={classId}
                      className="rounded px-2 py-1.5 flex items-center justify-between"
                      style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.1)" }}
                    >
                      <span className="font-mono" style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)" }}>
                        {classId}
                      </span>
                      <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-slate)" }}>
                        {count}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
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

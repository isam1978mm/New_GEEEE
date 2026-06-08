import { useEffect, useState } from "react";
import {
  getOperatorPrivateOverlayPreview,
  type OperatorPrivateOverlayArtifactFamily,
  type OperatorPrivateOverlayPreview,
} from "../api/operatorOverlays";
import { useOperatorAccessToken } from "./OperatorSessionContext";

interface OperatorPrivateOverlayPanelProps {
  runId: string;
  operatorAccessToken?: string | null;
}

const ARTIFACT_FAMILIES: { key: OperatorPrivateOverlayArtifactFamily; label: string }[] = [
  { key: "phase_d1_private_geojson", label: "D1 GeoJSON" },
  { key: "phase_d2_private_kmz", label: "D2 KMZ" },
  { key: "phase_d3_private_heatmap_json", label: "D3 Heatmap" },
];

export function OperatorPrivateOverlayPanel({ runId, operatorAccessToken }: OperatorPrivateOverlayPanelProps) {
  const contextOperatorAccessToken = useOperatorAccessToken();
  const resolvedOperatorAccessToken = operatorAccessToken ?? contextOperatorAccessToken;
  const [activeFamily, setActiveFamily] = useState<OperatorPrivateOverlayArtifactFamily>("phase_d1_private_geojson");
  const [preview, setPreview] = useState<OperatorPrivateOverlayPreview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadPreview() {
      setLoading(true);
      const nextPreview = await getOperatorPrivateOverlayPreview(runId, activeFamily, { accessToken: resolvedOperatorAccessToken });
      if (!cancelled) {
        setPreview(nextPreview);
        setLoading(false);
      }
    }
    void loadPreview();
    return () => {
      cancelled = true;
    };
  }, [runId, activeFamily, resolvedOperatorAccessToken]);

  return (
    <section
      className="rounded-lg bg-card overflow-hidden mt-4"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <details open>
        <summary
          className="px-4 py-2"
          style={{
            borderBottom: "1px solid var(--border)",
            backgroundColor: "var(--accent)",
            cursor: "pointer",
          }}
        >
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            Operator-only private preview (coordinate-free)
          </span>
        </summary>

        <div className="px-4 py-3 flex flex-col gap-3">
          <div style={{ fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
            Uses the default-off backend gate. May forward a provider-supplied bearer token when one is available. Operator identity is not set directly by this browser.
          </div>

          <div className="flex flex-wrap gap-2">
            {ARTIFACT_FAMILIES.map((family) => (
              <button
                key={family.key}
                onClick={() => setActiveFamily(family.key)}
                className="rounded px-2.5 py-1"
                style={{
                  fontSize: "11px",
                  fontWeight: activeFamily === family.key ? 700 : 500,
                  color: activeFamily === family.key ? "white" : "var(--gs-navy)",
                  backgroundColor: activeFamily === family.key ? "var(--gs-navy)" : "transparent",
                  border: "1px solid rgba(28,43,94,0.18)",
                  cursor: "pointer",
                }}
              >
                {family.label}
              </button>
            ))}
          </div>

          {loading && <StatusBox tone="neutral" message="Loading private preview status..." />}
          {!loading && preview && <PreviewBody preview={preview} />}
        </div>
      </details>
    </section>
  );
}

function PreviewBody({ preview }: { preview: OperatorPrivateOverlayPreview }) {
  if (preview.outcome === "denied") {
    return (
      <StatusBox
        tone="warning"
        message={preview.message || "Operator private overlay preview is not available."}
        detail={preview.supportReference ? `Support reference: ${preview.supportReference}` : undefined}
      />
    );
  }

  if (preview.outcome === "not_available") {
    return <StatusBox tone="neutral" message="No operator private overlay preview is available for this run and family." />;
  }

  if (preview.outcome === "error") {
    return <StatusBox tone="error" message={preview.message || "Operator private overlay preview is temporarily unavailable."} />;
  }

  const payload = preview.previewPayload;
  return (
    <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)", marginBottom: "6px" }}>
        Coordinate-free summary
      </div>
      <dl className="grid gap-2" style={{ gridTemplateColumns: "max-content 1fr", fontSize: "11px", color: "var(--gs-slate)" }}>
        <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Run</dt>
        <dd className="font-mono">{preview.runId}</dd>
        <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Family</dt>
        <dd className="font-mono">{preview.artifactFamily}</dd>
        <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Items</dt>
        <dd>{preview.itemCount ?? "not reported"}</dd>
        {typeof payload?.featureCount === "number" && (
          <>
            <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Features</dt>
            <dd>{payload.featureCount}</dd>
          </>
        )}
        {payload?.featureKinds && payload.featureKinds.length > 0 && (
          <>
            <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Geometry kinds</dt>
            <dd>{payload.featureKinds.join(", ")}</dd>
          </>
        )}
        {typeof payload?.placemarkCount === "number" && (
          <>
            <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Placemarks</dt>
            <dd>{payload.placemarkCount}</dd>
          </>
        )}
        {typeof payload?.pointCount === "number" && (
          <>
            <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Points</dt>
            <dd>{payload.pointCount}</dd>
          </>
        )}
        {payload?.weightSummary && (
          <>
            <dt style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Weight summary</dt>
            <dd>
              min {payload.weightSummary.min.toFixed(4)} · max {payload.weightSummary.max.toFixed(4)} · mean {payload.weightSummary.mean.toFixed(4)}
            </dd>
          </>
        )}
      </dl>
      <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "8px" }}>
        Filesystem-only: {preview.filesystemOnly ? "yes" : "no"}; HTTP servable: {preview.httpServable ? "yes" : "no"}; downloadable via API: {preview.downloadableViaApi ? "yes" : "no"}; visibility: {preview.frontendVisible}.
      </div>
    </div>
  );
}

function StatusBox({ tone, message, detail }: { tone: "neutral" | "warning" | "error"; message: string; detail?: string }) {
  const styles = {
    neutral: { backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" },
    warning: { backgroundColor: "var(--gs-amber-bg)", border: "1px solid var(--gs-amber-border)", color: "var(--gs-slate)" },
    error: { backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)", color: "var(--gs-red)" },
  }[tone];

  return (
    <div className="rounded px-3 py-2" style={{ ...styles, fontSize: "11px", lineHeight: "1.5" }}>
      <div>{message}</div>
      {detail && <div className="font-mono" style={{ marginTop: "4px", fontSize: "10.5px" }}>{detail}</div>}
    </div>
  );
}

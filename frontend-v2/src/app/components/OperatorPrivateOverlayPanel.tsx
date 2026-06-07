import { useEffect, useState } from "react";
import {
  getOperatorPrivateOverlayPreview,
  type OperatorPrivateOverlayArtifactFamily,
  type OperatorPrivateOverlayPreview,
} from "../api/client";

const ARTIFACT_FAMILIES: { key: OperatorPrivateOverlayArtifactFamily; label: string; description: string }[] = [
  {
    key: "phase_d1_private_geojson",
    label: "GeoJSON",
    description: "Feature count and neutral geometry kinds only.",
  },
  {
    key: "phase_d2_private_kmz",
    label: "KMZ",
    description: "Placemark count only.",
  },
  {
    key: "phase_d3_private_heatmap_json",
    label: "Heatmap",
    description: "Point count and scalar weight summary only.",
  },
];

interface OperatorPrivateOverlayPanelProps {
  runId: string;
}

export function OperatorPrivateOverlayPanel({ runId }: OperatorPrivateOverlayPanelProps) {
  const [collapsed, setCollapsed] = useState(true);
  const [artifactFamily, setArtifactFamily] = useState<OperatorPrivateOverlayArtifactFamily>("phase_d1_private_geojson");
  const [preview, setPreview] = useState<OperatorPrivateOverlayPreview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (collapsed) {
      return;
    }
    void loadPreview();
  }, [runId, artifactFamily, collapsed]);

  async function loadPreview() {
    setLoading(true);
    try {
      setPreview(await getOperatorPrivateOverlayPreview(runId, artifactFamily));
    } finally {
      setLoading(false);
    }
  }

  const selectedFamily = ARTIFACT_FAMILIES.find((family) => family.key === artifactFamily) ?? ARTIFACT_FAMILIES[0];

  return (
    <section
      className="rounded-lg bg-card overflow-hidden"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <button
        type="button"
        onClick={() => setCollapsed((value) => !value)}
        className="w-full px-4 py-2 flex items-center justify-between"
        style={{ border: "none", borderBottom: collapsed ? "none" : "1px solid var(--border)", backgroundColor: "var(--accent)", cursor: "pointer" }}
      >
        <div className="flex flex-col items-start">
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            Operator-only private preview
          </span>
          <span style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px" }}>
            Coordinate-free overlay summary. No downloads or public overlay layer.
          </span>
        </div>
        <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)" }}>
          {collapsed ? "Show" : "Hide"}
        </span>
      </button>

      {!collapsed && (
        <div className="px-4 py-3 flex flex-col gap-3">
          <div
            className="rounded px-3 py-2"
            style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}
          >
            <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>Access model</div>
            <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px", lineHeight: "1.5" }}>
              The browser does not set operator identity, role, or authorized-run headers. A trusted upstream context must supply them. If the backend denies access, this panel shows only the generic redacted response.
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {ARTIFACT_FAMILIES.map((family) => (
              <button
                key={family.key}
                type="button"
                onClick={() => setArtifactFamily(family.key)}
                className="rounded px-3 py-1.5"
                style={{
                  border: artifactFamily === family.key ? "1px solid var(--gs-navy)" : "1px solid var(--border)",
                  backgroundColor: artifactFamily === family.key ? "var(--accent)" : "transparent",
                  color: "var(--gs-navy)",
                  cursor: "pointer",
                  fontSize: "11.5px",
                  fontWeight: artifactFamily === family.key ? 700 : 500,
                }}
              >
                {family.label}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-between gap-3">
            <div>
              <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>{selectedFamily.label}</div>
              <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px" }}>{selectedFamily.description}</div>
            </div>
            <button
              type="button"
              onClick={() => { void loadPreview(); }}
              disabled={loading}
              className="rounded px-3 py-1.5"
              style={{
                border: "1px solid var(--border)",
                backgroundColor: loading ? "var(--accent)" : "transparent",
                color: "var(--gs-navy)",
                cursor: loading ? "default" : "pointer",
                fontSize: "11.5px",
              }}
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>

          <PreviewContent preview={preview} loading={loading} />
        </div>
      )}
    </section>
  );
}

function PreviewContent({ preview, loading }: { preview: OperatorPrivateOverlayPreview | null; loading: boolean }) {
  if (loading && !preview) {
    return <StatusBox tone="neutral" title="Loading" detail="Requesting coordinate-free operator preview." />;
  }
  if (!preview) {
    return <StatusBox tone="neutral" title="Not loaded" detail="Open a family tab or refresh to request the preview." />;
  }
  if (preview.outcome === "denied") {
    return (
      <StatusBox
        tone="warning"
        title={preview.status || "Access denied"}
        detail={`${preview.message}${preview.supportReference ? ` Support: ${preview.supportReference}` : ""}`}
      />
    );
  }
  if (preview.outcome === "error") {
    return <StatusBox tone="warning" title="Preview unavailable" detail={preview.message} />;
  }
  if (preview.outcome === "not_available") {
    return <StatusBox tone="neutral" title="Not available" detail="No operator preview is available for this run and artifact family." />;
  }

  return (
    <div className="rounded px-3 py-2" style={{ border: "1px solid var(--border)", backgroundColor: "var(--card)" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)", marginBottom: "6px" }}>Coordinate-free summary</div>
      <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
        <Metric label="Preview type" value={preview.previewType || "summary"} />
        <Metric label="Item count" value={formatNullableNumber(preview.itemCount)} />
        {preview.previewPayload?.featureCount !== undefined && <Metric label="Feature count" value={formatNullableNumber(preview.previewPayload.featureCount)} />}
        {preview.previewPayload?.placemarkCount !== undefined && <Metric label="Placemark count" value={formatNullableNumber(preview.previewPayload.placemarkCount)} />}
        {preview.previewPayload?.pointCount !== undefined && <Metric label="Point count" value={formatNullableNumber(preview.previewPayload.pointCount)} />}
      </div>
      {preview.previewPayload?.featureKinds && preview.previewPayload.featureKinds.length > 0 && (
        <div className="mt-3">
          <div style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Neutral geometry kinds
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {preview.previewPayload.featureKinds.map((kind) => (
              <span key={kind} className="rounded px-2 py-0.5 font-mono" style={{ fontSize: "10.5px", color: "var(--gs-slate)", backgroundColor: "var(--accent)" }}>
                {kind}
              </span>
            ))}
          </div>
        </div>
      )}
      {preview.previewPayload?.weightSummary && (
        <div className="mt-3 grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))" }}>
          <Metric label="Weight min" value={formatNullableNumber(preview.previewPayload.weightSummary.min)} />
          <Metric label="Weight max" value={formatNullableNumber(preview.previewPayload.weightSummary.max)} />
          <Metric label="Weight mean" value={formatNullableNumber(preview.previewPayload.weightSummary.mean)} />
        </div>
      )}
      <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "10px", lineHeight: "1.5" }}>
        Filesystem-only: {preview.filesystemOnly ? "yes" : "no"}. HTTP servable: {preview.httpServable ? "yes" : "no"}. Downloadable via API: {preview.downloadableViaApi ? "yes" : "no"}. Frontend visibility: {preview.frontendVisible || "operator_only"}.
      </div>
    </div>
  );
}

function StatusBox({ tone, title, detail }: { tone: "neutral" | "warning"; title: string; detail: string }) {
  return (
    <div
      className="rounded px-3 py-2"
      style={{
        backgroundColor: tone === "warning" ? "var(--gs-amber-bg)" : "var(--accent)",
        border: tone === "warning" ? "1px solid var(--gs-amber-border)" : "1px solid rgba(28,43,94,0.12)",
      }}
    >
      <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)" }}>{title}</div>
      <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px", lineHeight: "1.5" }}>{detail}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded px-2.5 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.08)" }}>
      <div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>{label}</div>
      <div className="font-mono" style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-navy)", marginTop: "2px" }}>
        {value}
      </div>
    </div>
  );
}

function formatNullableNumber(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? String(value) : "unavailable";
}

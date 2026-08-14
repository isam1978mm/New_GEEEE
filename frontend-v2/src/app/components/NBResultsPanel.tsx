import { Info, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchNBResults, type NBResults } from "../api/nbResults";

interface NBResultsPanelProps {
  runId: string;
}

export function NBResultsPanel({ runId }: NBResultsPanelProps) {
  const [results, setResults] = useState<NBResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setUnavailable(false);
      setResults(null);
      try {
        const next = await fetchNBResults(runId);
        if (!cancelled) setResults(next);
      } catch (_error) {
        if (!cancelled) setUnavailable(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [runId]);

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
            NB Results Add-ons
          </span>
          <span className="font-mono" style={{ fontSize: "9px", fontWeight: 700, color: "var(--gs-blue)", backgroundColor: "var(--gs-blue-bg)", border: "1px solid var(--gs-blue-border)", padding: "1px 5px", borderRadius: "3px" }}>
            NOTEBOOK METHOD
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
          Notebook-derived screening add-ons. They do not change the classifier, confirm a material, or provide calibrated numerical depth.
        </div>

        {(unavailable || results?.status === "not_available") && (
          <div className="rounded px-3 py-2 flex items-start gap-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" }}>
            <Info size={13} className="shrink-0" style={{ marginTop: "2px" }} />
            <span style={{ fontSize: "11.5px", lineHeight: "1.5" }}>NB results are not available for this run.</span>
          </div>
        )}

        {results && results.status !== "not_available" && (
          <>
            {results.unavailableSupport.length > 0 && (
              <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)", fontSize: "10.5px", lineHeight: "1.5" }}>
                Exact notebook support is unavailable for: {results.unavailableSupport.join(", ")}. Affected NB fields are shown as NOT AVAILABLE; no substitute value is used.
              </div>
            )}

            <div className="overflow-auto" style={{ border: "1px solid rgba(28,43,94,0.12)", borderRadius: "4px" }}>
              <table className="w-full" style={{ borderCollapse: "collapse", minWidth: "1180px" }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--accent)" }}>
                    {[
                      "Object #",
                      "NB metal signature",
                      "NB void signature",
                      "NB ceramic signature",
                      "NB mass signature",
                      "NB false-signature score",
                      "NB best object interpretation",
                      "Interpretation score",
                      "NANO penetration proxy",
                      "NB depth",
                    ].map((header) => (
                      <th key={header} className="font-mono" style={headerStyle}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.objects.map((row) => (
                    <tr key={row.objectId}>
                      <td style={cellStyle}>{row.objectId}</td>
                      <td style={cellStyle}>{formatScore(row.nbMetalSignature)}</td>
                      <td style={cellStyle}>{formatScore(row.nbVoidSignature)}</td>
                      <td style={cellStyle}>{formatScore(row.nbCeramicSignature)}</td>
                      <td style={cellStyle}>{formatScore(row.nbMassSignature)}</td>
                      <td style={cellStyle}>{formatScore(row.nbFalseSignatureScore)}</td>
                      <td style={cellStyle}>{row.nbBestObjectInterpretation ?? "NOT AVAILABLE"}</td>
                      <td style={cellStyle}>{formatScore(row.nbBestObjectScore)}</td>
                      <td style={cellStyle}>{row.nanoDepthPenetration === null ? "NOT AVAILABLE" : row.nanoDepthPenetration.toFixed(4)}</td>
                      <td style={cellStyle}>{row.nbDepthAvailable && row.nbDepthM !== null ? `${row.nbDepthM.toFixed(2)} m` : "NOT AVAILABLE"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
              NB metal signature is an indirect notebook proxy, not confirmed metal. NB depth is the notebook indirect depth proxy, not the separate calibrated Numerical Depth Estimate. The notebook's default 3.0 m display fallback is not used.
            </div>
          </>
        )}
      </div>
    </section>
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

function formatScore(value: number | null): string {
  return value === null ? "NOT AVAILABLE" : value.toFixed(4);
}

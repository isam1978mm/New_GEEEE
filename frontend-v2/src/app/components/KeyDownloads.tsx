import { Download, Info } from "lucide-react";
import { useState } from "react";
import type { KeyDownload } from "../api/client";

interface KeyDownloadsProps {
  downloads: KeyDownload[];
  loading?: boolean;
}

export function KeyDownloads({ downloads, loading = false }: KeyDownloadsProps) {
  const [infoOpen, setInfoOpen] = useState<string | null>(null);

  return (
    <div
      className="rounded-lg bg-card overflow-hidden"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2"
        style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <span
          className="font-mono"
          style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
        >
          Key Downloads
        </span>
        <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
          {downloads.length} artifacts
        </span>
      </div>

      {/* Rows */}
      <div className="flex flex-col">
        {loading && (
          <div className="px-3 py-2" style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
            Loading guarded downloads...
          </div>
        )}
        {!loading && downloads.length === 0 && (
          <div className="px-3 py-2" style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
            Key downloads appear here when a completed run exposes them.
          </div>
        )}
        {!loading && downloads.map((dl, i) => (
          <div
            key={dl.path}
            className="relative group"
            style={{ borderBottom: i < downloads.length - 1 ? "1px solid rgba(28,43,94,0.06)" : "none" }}
          >
            <div className="flex items-center gap-2 px-3 py-1.5 hover:bg-accent/30 transition-colors">
              {/* Tag */}
              <span
                className="font-mono shrink-0"
                style={{
                  fontSize: "8.5px",
                  fontWeight: 700,
                  color: "var(--gs-blue)",
                  backgroundColor: "var(--gs-blue-bg)",
                  border: "1px solid var(--gs-blue-border)",
                  padding: "1px 4px",
                  borderRadius: "2px",
                  letterSpacing: "0.03em",
                }}
              >
                PUB
              </span>

              {/* Name + path */}
              <div className="flex-1 min-w-0">
                <span
                  className="font-mono"
                  style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-navy)" }}
                >
                  {dl.label}
                </span>
                <span
                  style={{ fontSize: "10px", color: "var(--gs-slate)", marginLeft: "6px", opacity: 0.6 }}
                >
                  {dl.path}
                </span>
              </div>

              {/* Size */}
              <span
                className="font-mono shrink-0"
                style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginRight: "4px" }}
              >
                {dl.size}
              </span>

              {/* More info */}
              <button
                onClick={() => setInfoOpen(infoOpen === dl.path ? null : dl.path)}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-accent"
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--gs-slate)" }}
                title="More info"
              >
                <Info size={11} />
              </button>

              {/* Download */}
              {dl.downloadUrl && (
                <a
                  href={dl.downloadUrl}
                  download={dl.label}
                  className="flex items-center gap-1 px-2 py-0.5 rounded shrink-0 transition-colors hover:bg-accent"
                  style={{
                    fontSize: "11px",
                    fontWeight: 500,
                    color: "var(--gs-navy)",
                    backgroundColor: "var(--accent)",
                    border: "1px solid rgba(28,43,94,0.15)",
                    cursor: "pointer",
                    textDecoration: "none",
                  }}
                >
                  <Download size={9} />
                  Download
                </a>
              )}
            </div>

            {/* More info panel */}
            {infoOpen === dl.path && (
              <div
                className="px-3 py-2"
                style={{
                  backgroundColor: "var(--gs-blue-bg)",
                  borderTop: "1px solid var(--gs-blue-border)",
                  fontSize: "11px",
                  color: "var(--gs-slate)",
                  lineHeight: "1.5",
                }}
              >
                Safe operator deliverable. Tagged REDACTED_PUBLIC — cleared for download from this session.
                Full export tree available in the <strong>Exports</strong> tab.
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer note */}
      <div
        className="px-3 py-1.5"
        style={{ borderTop: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <p style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
          Safe operator deliverables only. Full exports →{" "}
          <span style={{ fontWeight: 600, color: "var(--gs-navy)" }}>Exports tab</span>.
        </p>
      </div>
    </div>
  );
}

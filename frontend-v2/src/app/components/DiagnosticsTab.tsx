import { CheckCircle2, Info, RefreshCw, AlertTriangle } from "lucide-react";

interface DiagItem {
  id: string;
  type: "ok" | "info" | "warning";
  label: string;
  detail: string;
}

const DIAG_ITEMS: DiagItem[] = [
  {
    id: "radar-stack",
    type: "ok",
    label: "RADAR_STACK xfail accepted",
    detail: "RADAR_STACK has accepted inherited SAR dB residual; stack assembly is correct.",
  },
  {
    id: "sar-rtc",
    type: "ok",
    label: "SAR RTC normalization verified",
    detail: "Backscatter calibration applied. VV/VH ratio within expected range.",
  },
  {
    id: "dem-align",
    type: "ok",
    label: "DEM alignment QA passed",
    detail: "Co-registration error < 0.3 px. No resampling artifacts detected.",
  },
  {
    id: "hypercube-bands",
    type: "ok",
    label: "Hypercube band order verified",
    detail: "9-band FINAL_TESLA_V7_2 matches reference schema v7.2.",
  },
  {
    id: "patched-14b",
    type: "ok",
    label: "PATCHED_14B 13-band integrity OK",
    detail: "All 13 bands present. No null-band injection detected.",
  },
  {
    id: "pca-variance",
    type: "info",
    label: "PCA variance capture: 94.2%",
    detail: "Top 8 components capture 94.2% of spectral variance. Within acceptable bounds.",
  },
  {
    id: "object-cluster",
    type: "ok",
    label: "Object/cluster alignment QA passed",
    detail: "Cluster centroids align within 1.2 px of reference objects.",
  },
  {
    id: "s2-coverage",
    type: "warning",
    label: "S2 cloud coverage: 18%",
    detail: "Affected cells use nearest-clear S2 composite.",
  },
];

const typeCfg = {
  ok: { icon: <CheckCircle2 size={12} />, color: "var(--gs-green)", bg: "var(--gs-green-bg)", border: "var(--gs-green-border)" },
  info: { icon: <Info size={12} />, color: "var(--gs-blue)", bg: "var(--gs-blue-bg)", border: "var(--gs-blue-border)" },
  warning: { icon: <AlertTriangle size={12} />, color: "var(--gs-amber)", bg: "var(--gs-amber-bg)", border: "var(--gs-amber-border)" },
};

export function DiagnosticsTab() {
  const okCount = DIAG_ITEMS.filter((d) => d.type === "ok").length;
  const warnCount = DIAG_ITEMS.filter((d) => d.type === "warning").length;
  const infoCount = DIAG_ITEMS.filter((d) => d.type === "info").length;

  return (
    <div className="flex flex-col gap-3">
      {/* Summary bar */}
      <div
        className="rounded-lg px-4 py-2.5 flex items-center gap-6"
        style={{ backgroundColor: "var(--card)", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div className="flex items-center gap-1.5">
          <CheckCircle2 size={13} style={{ color: "var(--gs-green)" }} />
          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-green)" }}>{okCount} passed</span>
        </div>
        <div className="flex items-center gap-1.5">
          <AlertTriangle size={13} style={{ color: "var(--gs-amber)" }} />
          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-amber)" }}>{warnCount} warning</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Info size={13} style={{ color: "var(--gs-blue)" }} />
          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-blue)" }}>{infoCount} note</span>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <RefreshCw size={10} style={{ color: "var(--gs-slate)", opacity: 0.5 }} />
          <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            Parity notes · run: <span className="font-mono">validation-run</span>
          </span>
        </div>
      </div>

      {/* Diagnostics list */}
      <div
        className="rounded-lg bg-card overflow-hidden"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div
          className="px-4 py-2"
          style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
        >
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            Parity &amp; Stack Diagnostics
          </span>
        </div>

        {DIAG_ITEMS.map((item, i) => {
          const cfg = typeCfg[item.type];
          return (
            <div
              key={item.id}
              className="flex items-start gap-3 px-4 py-2.5"
              style={{ borderBottom: i < DIAG_ITEMS.length - 1 ? "1px solid var(--border)" : "none" }}
            >
              <div
                className="flex items-center justify-center rounded shrink-0"
                style={{
                  width: "22px",
                  height: "22px",
                  backgroundColor: cfg.bg,
                  color: cfg.color,
                  border: `1px solid ${cfg.border}`,
                  marginTop: "1px",
                }}
              >
                {cfg.icon}
              </div>
              <div className="flex-1 min-w-0">
                <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>
                  {item.label}
                </span>
                <span style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginLeft: "8px" }}>
                  {item.detail}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Reference refresh note */}
      <div
        className="rounded-lg px-4 py-3 flex items-start gap-3"
        style={{ backgroundColor: "var(--gs-blue-bg)", border: "1px solid var(--gs-blue-border)" }}
      >
        <RefreshCw size={12} style={{ color: "var(--gs-blue)", marginTop: "2px", flexShrink: 0 }} />
        <div>
          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-blue)" }}>
            Reference refresh policy
          </span>
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px", lineHeight: "1.5" }}>
            External tile sources are disabled. DEM, SAR, and S2 reference layers use local cached data.
            Trigger a new run to refresh. Cached version:{" "}
            <span className="font-mono">2026-05-31</span>.
          </p>
        </div>
      </div>
    </div>
  );
}

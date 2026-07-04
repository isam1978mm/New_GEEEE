import { AlertTriangle, CheckCircle2, Download, FileText, Info, XCircle } from "lucide-react";
import type { OperatorOutputTree, PublicArtifact, UnavailableOutput } from "../api/client";

type DiagnosticStatus = "available" | "warning" | "unavailable" | "accepted";

interface DiagnosticRow {
  id: string;
  label: string;
  status: DiagnosticStatus;
  detail: string;
  source: string;
  downloadUrl?: string;
}

interface DiagnosticSection {
  id: string;
  label: string;
  rows: DiagnosticRow[];
}

interface DiagnosticsTabProps {
  outputTree: OperatorOutputTree;
  artifacts: PublicArtifact[];
}

const statusCfg: Record<DiagnosticStatus, { icon: JSX.Element; color: string; bg: string; border: string; label: string }> = {
  available: {
    icon: <CheckCircle2 size={12} />,
    color: "var(--gs-green)",
    bg: "var(--gs-green-bg)",
    border: "var(--gs-green-border)",
    label: "Available",
  },
  warning: {
    icon: <AlertTriangle size={12} />,
    color: "var(--gs-amber)",
    bg: "var(--gs-amber-bg)",
    border: "var(--gs-amber-border)",
    label: "Warning",
  },
  unavailable: {
    icon: <XCircle size={12} />,
    color: "var(--gs-red)",
    bg: "var(--gs-red-bg)",
    border: "var(--gs-red-border)",
    label: "Unavailable",
  },
  accepted: {
    icon: <Info size={12} />,
    color: "var(--gs-blue)",
    bg: "var(--gs-blue-bg)",
    border: "var(--gs-blue-border)",
    label: "Accepted exception",
  },
};

const SECTION_SPECS: Array<{
  id: string;
  label: string;
  entries: Array<{ path: string; label: string; detail: string }>;
}> = [
  {
    id: "run-qa",
    label: "Run QA summaries",
    entries: [
      {
        path: "QA/RUN_MANIFEST.json",
        label: "Run manifest available",
        detail: "Primary run manifest is available as a guarded QA summary.",
      },
      {
        path: "QA/REPORT_640_manifest.json",
        label: "REPORT_640 manifest available",
        detail: "Report 640 manifest is available for operator review.",
      },
    ],
  },
  {
    id: "dem-grid",
    label: "DEM / Grid QA",
    entries: [
      {
        path: "QA/grid_dem/grid_guard_summary.json",
        label: "Grid guard summary available",
        detail: "Grid lock and alignment guard summary is available for review.",
      },
      {
        path: "QA/grid_dem/dem_audit_summary.json",
        label: "DEM audit summary available",
        detail: "DEM audit summary is available as a guarded QA file.",
      },
      {
        path: "QA/grid_dem/drift_audit.csv",
        label: "Grid drift audit available",
        detail: "Grid drift audit is available for manual inspection.",
      },
    ],
  },
  {
    id: "sar-qa",
    label: "SAR QA",
    entries: [
      {
        path: "QA/sar/sar_pair_diagnostics.json",
        label: "SAR pair diagnostics available",
        detail: "SAR pair diagnostics are available as a guarded QA summary.",
      },
      {
        path: "QA/sar/sar_summary.csv",
        label: "SAR summary available",
        detail: "SAR summary is available for operator review.",
      },
      {
        path: "QA/sar/sar_nodata_audit.csv",
        label: "SAR nodata audit available",
        detail: "SAR nodata audit is available for manual inspection.",
      },
      {
        path: "QA/sar/sar_alignment_summary.json",
        label: "SAR alignment summary available",
        detail: "SAR alignment summary is available as a guarded QA file.",
      },
    ],
  },
  {
    id: "stack-qa",
    label: "Stack / S2 / Thermal QA",
    entries: [
      {
        path: "QA/stacks/s2_indices_summary.json",
        label: "S2 indices summary available",
        detail: "Sentinel-2 index summary is available as a guarded QA file.",
      },
      {
        path: "QA/stacks/thermal_summary.json",
        label: "Thermal summary available",
        detail: "Thermal summary is available for operator review.",
      },
      {
        path: "QA/stacks/secret_layers_manifest.json",
        label: "Secret layers manifest available",
        detail: "Notebook-compatible secret-layer manifest is available as a guarded QA file.",
      },
      {
        path: "pca_eigenvalues.json",
        label: "PCA eigenvalues available",
        detail: "PCA eigenvalues are available as a guarded run output.",
      },
    ],
  },
  {
    id: "alignment-qa",
    label: "Alignment QA",
    entries: [
      {
        path: "alignment_qa.json",
        label: "Alignment QA summary available",
        detail: "Alignment QA summary is available as a public-safe artifact.",
      },
      {
        path: "alignment_audit.csv",
        label: "Alignment audit available",
        detail: "Alignment audit is available as a guarded run output.",
      },
      {
        path: "alignment_mask_selection.json",
        label: "Alignment mask selection available",
        detail: "Alignment mask selection is available for manual review.",
      },
    ],
  },
];

function rowFromOutput(
  outputTree: OperatorOutputTree,
  artifactMap: Map<string, PublicArtifact>,
  path: string,
  label: string,
  detail: string,
): DiagnosticRow | null {
  const output = outputTree.outputs.find((item) => item.path === path);
  if (output) {
    return {
      id: path,
      label,
      status: "available",
      detail,
      source: path,
      downloadUrl: output.downloadUrl,
    };
  }

  const artifact = artifactMap.get(path);
  if (artifact) {
    return {
      id: path,
      label,
      status: "available",
      detail,
      source: path,
      downloadUrl: artifact.downloadUrl,
    };
  }

  return null;
}

function artifactPathMap(artifacts: PublicArtifact[]) {
  const map = new Map<string, PublicArtifact>();
  for (const artifact of artifacts) {
    if (artifact.name === "alignment_qa.json") {
      map.set("alignment_qa.json", artifact);
    }
    if (artifact.name === "alignment_audit.json") {
      map.set("alignment_audit.csv", artifact);
    }
    if (artifact.name === "alignment_mask_selection.json") {
      map.set("alignment_mask_selection.json", artifact);
    }
  }
  return map;
}

function unavailableRows(unavailable: UnavailableOutput[]): DiagnosticRow[] {
  return unavailable
    .filter((item) => item.path.startsWith("QA/") || item.path.includes("manifest") || item.path.includes("PATCHED"))
    .slice(0, 6)
    .map((item) => ({
      id: `unavailable-${item.path}`,
      label: item.filename,
      status: "unavailable",
      detail: "This diagnostic-related output is unavailable in the current app output set for this run.",
      source: item.source,
    }));
}

export function DiagnosticsTab({ outputTree, artifacts }: DiagnosticsTabProps) {
  const artifactMap = artifactPathMap(artifacts);
  const sections: DiagnosticSection[] = SECTION_SPECS.map((section) => ({
    id: section.id,
    label: section.label,
    rows: section.entries
      .map((entry) => rowFromOutput(outputTree, artifactMap, entry.path, entry.label, entry.detail))
      .filter((row): row is DiagnosticRow => row !== null),
  })).filter((section) => section.rows.length > 0);

  const acceptedExceptionRows: DiagnosticRow[] = [
    {
      id: "accepted-radar-stack",
      label: "RADAR_STACK accepted inherited residual",
      status: "accepted",
      detail: "RADAR_STACK_HWC_640_app.npy has accepted inherited SAR dB residual; stack assembly is correct.",
      source: "tests/notebook_parity/test_stack_output_reference_numeric_contract.py",
    },
  ];

  const advancedUnavailableRows = unavailableRows(outputTree.unavailable);
  const sourceBackedCount = sections.reduce((count, section) => count + section.rows.length, 0);

  return (
    <div className="flex flex-col gap-3">
      <div
        className="rounded-lg px-4 py-2.5 flex items-center gap-6"
        style={{ backgroundColor: "var(--card)", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div className="flex items-center gap-1.5">
          <CheckCircle2 size={13} style={{ color: "var(--gs-green)" }} />
          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-green)" }}>{sourceBackedCount} source-backed items</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Info size={13} style={{ color: "var(--gs-blue)" }} />
          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-blue)" }}>{acceptedExceptionRows.length} accepted exception</span>
        </div>
        <div className="flex items-center gap-1.5">
          <AlertTriangle size={13} style={{ color: "var(--gs-amber)" }} />
          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-amber)" }}>{advancedUnavailableRows.length} advanced note</span>
        </div>
      </div>

      {sourceBackedCount === 0 && (
        <div
          className="rounded-lg px-4 py-3"
          style={{ backgroundColor: "var(--card)", border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
        >
          <span style={{ fontSize: "12px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
            No source-backed diagnostics are available yet. Completed runs may expose guarded QA outputs after exports load.
          </span>
        </div>
      )}

      {sections.map((section) => (
        <div
          key={section.id}
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
              {section.label}
            </span>
          </div>
          {section.rows.map((row, index) => {
            const cfg = statusCfg[row.status];
            return (
              <div
                key={row.id}
                className="flex items-start gap-3 px-4 py-2.5"
                style={{ borderBottom: index < section.rows.length - 1 ? "1px solid var(--border)" : "none" }}
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
                  <div className="flex items-center gap-2 flex-wrap">
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>{row.label}</span>
                    <span
                      className="font-mono"
                      style={{
                        fontSize: "9.5px",
                        fontWeight: 700,
                        color: cfg.color,
                        backgroundColor: cfg.bg,
                        border: `1px solid ${cfg.border}`,
                        borderRadius: "3px",
                        padding: "1px 5px",
                        letterSpacing: "0.03em",
                      }}
                    >
                      {cfg.label}
                    </span>
                  </div>
                  <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>{row.detail}</div>
                  <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "4px" }}>
                    Source: <span className="font-mono">{row.source}</span>
                  </div>
                </div>
                {row.downloadUrl && (
                  <a
                    href={row.downloadUrl}
                    download
                    className="flex items-center gap-1 px-2 py-1 rounded shrink-0"
                    style={{
                      fontSize: "11px",
                      fontWeight: 500,
                      color: "var(--gs-navy)",
                      backgroundColor: "var(--accent)",
                      border: "1px solid rgba(28,43,94,0.15)",
                      textDecoration: "none",
                    }}
                  >
                    <Download size={10} />
                    Open
                  </a>
                )}
              </div>
            );
          })}
        </div>
      ))}

      <div
        className="rounded-lg bg-card overflow-hidden"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
          <span className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
            Accepted exceptions
          </span>
        </div>
        {acceptedExceptionRows.map((row) => {
          const cfg = statusCfg[row.status];
          return (
            <div key={row.id} className="flex items-start gap-3 px-4 py-2.5">
              <div
                className="flex items-center justify-center rounded shrink-0"
                style={{ width: "22px", height: "22px", backgroundColor: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`, marginTop: "1px" }}
              >
                {cfg.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>{row.label}</div>
                <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>{row.detail}</div>
                <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "4px" }}>
                  Source: <span className="font-mono">{row.source}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div
        className="rounded-lg bg-card overflow-hidden"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
          <span className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
            Reference refresh policy
          </span>
        </div>
        <div className="flex items-start gap-3 px-4 py-2.5">
          <div
            className="flex items-center justify-center rounded shrink-0"
            style={{ width: "22px", height: "22px", backgroundColor: "var(--gs-blue-bg)", color: "var(--gs-blue)", border: "1px solid var(--gs-blue-border)", marginTop: "1px" }}
          >
            <FileText size={12} />
          </div>
          <div style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
            Reference refreshes are policy-driven and one-file scoped. This tab does not infer refreshed values; it only shows guarded QA outputs and accepted documented exceptions.
          </div>
        </div>
      </div>

      <div
        className="rounded-lg bg-card overflow-hidden"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
          <span className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
            Advanced unavailable notes
          </span>
        </div>
        {advancedUnavailableRows.length === 0 ? (
          <div className="px-4 py-2.5" style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
            No advanced unavailable diagnostic notes are reported for this run. Check Exports if guarded outputs are still loading.
          </div>
        ) : (
          advancedUnavailableRows.map((row, index) => {
            const cfg = statusCfg[row.status];
            return (
              <div
                key={row.id}
                className="flex items-start gap-3 px-4 py-2.5"
                style={{ borderBottom: index < advancedUnavailableRows.length - 1 ? "1px solid var(--border)" : "none" }}
              >
                <div
                  className="flex items-center justify-center rounded shrink-0"
                  style={{ width: "22px", height: "22px", backgroundColor: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`, marginTop: "1px" }}
                >
                  {cfg.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>{row.label}</div>
                  <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>{row.detail}</div>
                  <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "4px" }}>
                    Source: <span className="font-mono">{row.source}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

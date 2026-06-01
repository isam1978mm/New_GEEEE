import { useState } from "react";
import { ChevronDown, ChevronRight, WifiOff, Play, RotateCcw } from "lucide-react";

const steps = [
  { n: 1, label: "Define Target" },
  { n: 2, label: "Execute Run" },
  { n: 3, label: "Review Results" },
];

export function RunWorkflowCard() {
  const [targetLabel, setTargetLabel] = useState("");
  const [runName, setRunName] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [bufferKm, setBufferKm] = useState("2.0");
  const [resolution, setResolution] = useState("640");

  const canQueue = targetLabel.trim().length > 2;
  const hasPreview = targetLabel.trim() || runName;

  function handleReset() {
    setTargetLabel(""); setRunName("");
    setBufferKm("2.0"); setResolution("640");
    setShowAdvanced(false);
  }

  return (
    <div
      className="rounded-lg bg-card flex flex-col"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.06)" }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <div>
          <h3
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", letterSpacing: "0.07em", textTransform: "uppercase" }}
          >
            Run Workflow
          </h3>
        </div>
        <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>Queue a new screening run</span>
      </div>

      <div className="px-4 py-3 flex flex-col gap-3">
        {/* Stepper */}
        <div className="flex items-center gap-1">
          {steps.map((step, i) => {
            const isActive = step.n === 1;
            return (
              <div key={step.n} className="flex items-center gap-1">
                <div
                  className="flex items-center justify-center rounded-full shrink-0"
                  style={{
                    width: "18px",
                    height: "18px",
                    backgroundColor: isActive ? "var(--gs-navy)" : "var(--muted)",
                    color: isActive ? "white" : "var(--gs-slate)",
                    fontSize: "9.5px",
                    fontWeight: 700,
                  }}
                >
                  {step.n}
                </div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? "var(--gs-navy)" : "var(--gs-slate)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {step.label}
                </span>
                {i < steps.length - 1 && (
                  <ChevronRight size={11} style={{ color: "var(--gs-slate)", opacity: 0.35, margin: "0 2px" }} />
                )}
              </div>
            );
          })}
        </div>

        {/* Target reference field */}
        <div className="flex flex-col gap-1">
          <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>
            Target reference
            <span style={{ fontWeight: 400, color: "var(--gs-slate)", marginLeft: "4px" }}>mock only</span>
          </label>
          <input
            type="text"
            value={targetLabel}
            onChange={(e) => setTargetLabel(e.target.value)}
            placeholder="e.g. validation-target"
            className="font-mono rounded outline-none"
            style={{
              fontSize: "12px",
              padding: "6px 10px",
              backgroundColor: "var(--input-background)",
              border: "1px solid var(--border)",
              color: "var(--gs-navy)",
            }}
          />
        </div>

        {/* Run name */}
        <div className="flex flex-col gap-1">
          <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>
            Run name
            <span style={{ fontWeight: 400, color: "var(--gs-slate)", marginLeft: "4px" }}>optional</span>
          </label>
          <input
            type="text"
            value={runName}
            onChange={(e) => setRunName(e.target.value)}
            placeholder="e.g. validation-run-2026"
            className="rounded outline-none"
            style={{
              fontSize: "12px",
              padding: "6px 10px",
              backgroundColor: "var(--input-background)",
              border: "1px solid var(--border)",
              color: "var(--gs-navy)",
            }}
          />
        </div>

        {/* Advanced settings */}
        <div>
          <button
            onClick={() => setShowAdvanced((p) => !p)}
            className="flex items-center gap-1 hover:opacity-75 transition-opacity"
            style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
          >
            {showAdvanced
              ? <ChevronDown size={11} style={{ color: "var(--gs-slate)" }} />
              : <ChevronRight size={11} style={{ color: "var(--gs-slate)" }} />
            }
            <span style={{ fontSize: "11px", color: "var(--gs-slate)", fontWeight: 500 }}>
              Advanced settings
            </span>
          </button>

          {showAdvanced && (
            <div
              className="mt-2 pl-3 flex flex-col gap-2.5"
              style={{ borderLeft: "2px solid var(--border)" }}
            >
              <div className="grid grid-cols-2 gap-2.5">
                <div className="flex flex-col gap-1">
                  <label style={{ fontSize: "10.5px", fontWeight: 600, color: "var(--gs-slate)" }}>
                    Buffer radius (km)
                  </label>
                  <input
                    type="number"
                    value={bufferKm}
                    onChange={(e) => setBufferKm(e.target.value)}
                    className="font-mono rounded outline-none"
                    style={{ fontSize: "11.5px", padding: "5px 8px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label style={{ fontSize: "10.5px", fontWeight: 600, color: "var(--gs-slate)" }}>
                    Grid resolution
                  </label>
                  <select
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    className="font-mono rounded outline-none"
                    style={{ fontSize: "11.5px", padding: "5px 8px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }}
                  >
                    <option value="320">320 m</option>
                    <option value="640">640 m</option>
                    <option value="1280">1280 m</option>
                  </select>
                </div>
              </div>
              <label className="flex items-center gap-2" style={{ cursor: "pointer" }}>
                <input type="checkbox" defaultChecked className="rounded" />
                <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                  Accept SAR residual xfail (RADAR_STACK)
                </span>
              </label>
            </div>
          )}
        </div>

        {/* Target preview */}
        {hasPreview && (
          <div
            className="rounded px-3 py-2 flex flex-col gap-1"
            style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}
          >
            <div
              className="font-mono"
              style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              Target Preview
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5">
              {targetLabel.trim() && (
                <span className="font-mono" style={{ fontSize: "11.5px", color: "var(--gs-navy)" }}>
                  Target: {targetLabel.trim()}
                </span>
              )}
              {runName && (
                <span style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>"{runName}"</span>
              )}
            </div>
            <div className="flex items-center gap-1">
              <WifiOff size={9} style={{ color: "var(--gs-slate)", opacity: 0.5 }} />
              <span style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.55 }}>
                External tiles disabled
              </span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            disabled={!canQueue}
            className="flex items-center justify-center gap-1.5 py-2 rounded flex-1 transition-opacity"
            style={{
              backgroundColor: canQueue ? "var(--gs-navy)" : "var(--muted)",
              color: canQueue ? "white" : "var(--gs-slate)",
              border: "none",
              cursor: canQueue ? "pointer" : "not-allowed",
              fontSize: "12.5px",
              fontWeight: 600,
            }}
          >
            <Play size={11} />
            Queue Run
          </button>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-2 rounded hover:opacity-75 transition-opacity"
            style={{
              backgroundColor: "transparent",
              color: "var(--gs-slate)",
              border: "1px solid var(--border)",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 500,
            }}
          >
            <RotateCcw size={11} />
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}

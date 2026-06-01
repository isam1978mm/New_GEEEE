import { useState } from "react";
import { ChevronDown, ChevronRight, WifiOff, Play, RotateCcw } from "lucide-react";
import type { CreateRunInput } from "../api/client";

const steps = [
  { n: 1, label: "Define Target" },
  { n: 2, label: "Execute Run" },
  { n: 3, label: "Review Results" },
];

interface RunWorkflowCardProps {
  onQueueRun?: (input: CreateRunInput) => Promise<void>;
  isQueueing?: boolean;
  feedback?: string | null;
}

export function RunWorkflowCard({ onQueueRun, isQueueing = false, feedback = null }: RunWorkflowCardProps) {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [runName, setRunName] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [bufferKm, setBufferKm] = useState("2.0");
  const [resolution, setResolution] = useState("640");

  const latitudeValue = Number.parseFloat(latitude);
  const longitudeValue = Number.parseFloat(longitude);
  const hasLatitude = latitude.trim().length > 0;
  const hasLongitude = longitude.trim().length > 0;
  const latitudeValid = Number.isFinite(latitudeValue) && latitudeValue >= -90 && latitudeValue <= 90;
  const longitudeValid = Number.isFinite(longitudeValue) && longitudeValue >= -180 && longitudeValue <= 180;
  const canQueue = latitudeValid && longitudeValid;
  const hasPreview = hasLatitude || hasLongitude || runName.trim().length > 0;

  function handleReset() {
    setLatitude(""); setLongitude(""); setRunName("");
    setBufferKm("2.0"); setResolution("640");
    setShowAdvanced(false);
  }

  async function handleQueueRun() {
    if (!canQueue || isQueueing) {
      return;
    }
    await onQueueRun?.({
      lat: latitudeValue,
      lon: longitudeValue,
      name: runName.trim() || null,
    });
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

        <div className="grid grid-cols-2 gap-2.5">
          <div className="flex flex-col gap-1">
            <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>
              Latitude
              <span style={{ fontWeight: 400, color: "var(--gs-slate)", marginLeft: "4px" }}>required</span>
            </label>
            <input
              type="number"
              inputMode="decimal"
              min={-90}
              max={90}
              step="any"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              placeholder="e.g. 43.6532"
              aria-invalid={hasLatitude && !latitudeValid}
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
          <div className="flex flex-col gap-1">
            <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>
              Longitude
              <span style={{ fontWeight: 400, color: "var(--gs-slate)", marginLeft: "4px" }}>required</span>
            </label>
            <input
              type="number"
              inputMode="decimal"
              min={-180}
              max={180}
              step="any"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              placeholder="e.g. -79.3832"
              aria-invalid={hasLongitude && !longitudeValid}
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
              {hasLatitude && (
                <span className="font-mono" style={{ fontSize: "11.5px", color: "var(--gs-navy)" }}>
                  Latitude: {latitude}
                </span>
              )}
              {hasLongitude && (
                <span className="font-mono" style={{ fontSize: "11.5px", color: "var(--gs-navy)" }}>
                  Longitude: {longitude}
                </span>
              )}
              {runName.trim() && (
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
            disabled={!canQueue || isQueueing}
            onClick={() => void handleQueueRun()}
            className="flex items-center justify-center gap-1.5 py-2 rounded flex-1 transition-opacity"
            style={{
              backgroundColor: canQueue && !isQueueing ? "var(--gs-navy)" : "var(--muted)",
              color: canQueue && !isQueueing ? "white" : "var(--gs-slate)",
              border: "none",
              cursor: canQueue && !isQueueing ? "pointer" : "not-allowed",
              fontSize: "12.5px",
              fontWeight: 600,
            }}
          >
            <Play size={11} />
            {isQueueing ? "Queueing..." : "Queue Run"}
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
        {feedback && (
          <p style={{ fontSize: "11px", color: "var(--gs-slate)" }}>
            {feedback}
          </p>
        )}
      </div>
    </div>
  );
}

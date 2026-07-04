import { useState, type ReactNode } from "react";
import { ChevronDown, ChevronRight, WifiOff, Play, RotateCcw, Search, Satellite } from "lucide-react";
import type { CreateRunInput, EarthEnginePlan, EarthEnginePlanInput, RoiPreview, RoiPreviewInput } from "../api/client";
import { TargetLeafletMap } from "./TargetLeafletMap";

const steps = [
  { n: 1, label: "Define Target" },
  { n: 2, label: "Execute Run" },
  { n: 3, label: "Review Results" },
];

interface RunWorkflowCardProps {
  onQueueRun?: (input: CreateRunInput) => Promise<void>;
  onPreviewRoi?: (input: RoiPreviewInput) => Promise<RoiPreview>;
  onPlanEarthEngine?: (input: EarthEnginePlanInput) => Promise<EarthEnginePlan>;
  isQueueing?: boolean;
  feedback?: string | null;
  externalTilesEnabled?: boolean;
  tileUrlTemplate?: string;
}

export function RunWorkflowCard({ onQueueRun, onPreviewRoi, onPlanEarthEngine, isQueueing = false, feedback = null, externalTilesEnabled = false, tileUrlTemplate = "" }: RunWorkflowCardProps) {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [runName, setRunName] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [roiPreview, setRoiPreview] = useState<RoiPreview | null>(null);
  const [roiPreviewError, setRoiPreviewError] = useState<string | null>(null);
  const [isPreviewingRoi, setIsPreviewingRoi] = useState(false);
  const [acquisitionStart, setAcquisitionStart] = useState(defaultAcquisitionStart());
  const [acquisitionEnd, setAcquisitionEnd] = useState(defaultAcquisitionEnd());
  const [cloudPercentMax, setCloudPercentMax] = useState("20");
  const [eePlan, setEePlan] = useState<EarthEnginePlan | null>(null);
  const [eePlanError, setEePlanError] = useState<string | null>(null);
  const [isPlanningEe, setIsPlanningEe] = useState(false);

  const lat = Number.parseFloat(latitude);
  const lon = Number.parseFloat(longitude);
  const hasLat = latitude.trim().length > 0;
  const hasLon = longitude.trim().length > 0;
  const latOk = Number.isFinite(lat) && lat >= -90 && lat <= 90;
  const lonOk = Number.isFinite(lon) && lon >= -180 && lon <= 180;
  const targetOk = latOk && lonOk;
  const startDate = Date.parse(`${acquisitionStart}T00:00:00Z`);
  const endDate = Date.parse(`${acquisitionEnd}T00:00:00Z`);
  const acquisitionOk = Boolean(acquisitionStart && acquisitionEnd && Number.isFinite(startDate) && Number.isFinite(endDate) && endDate >= startDate);
  const cloudValue = Number.parseFloat(cloudPercentMax);
  const cloudOk = cloudPercentMax.trim().length === 0 || (Number.isFinite(cloudValue) && cloudValue >= 0 && cloudValue <= 100);
  const canPreviewRoi = targetOk && !isPreviewingRoi && Boolean(onPreviewRoi);
  const canPlanEe = targetOk && acquisitionOk && cloudOk && !isPlanningEe && Boolean(onPlanEarthEngine);
  const hasPreview = hasLat || hasLon || runName.trim().length > 0;

  function clearComputed() {
    setRoiPreview(null);
    setRoiPreviewError(null);
    setEePlan(null);
    setEePlanError(null);
  }

  function updateLatitude(value: string) {
    setLatitude(value);
    clearComputed();
  }

  function updateLongitude(value: string) {
    setLongitude(value);
    clearComputed();
  }

  function handleTargetChange(target: { lat: number; lon: number }) {
    setLatitude(target.lat.toFixed(8));
    setLongitude(target.lon.toFixed(8));
    clearComputed();
  }

  async function handlePreviewRoi() {
    if (!canPreviewRoi) return;
    setIsPreviewingRoi(true);
    setRoiPreviewError(null);
    try {
      setRoiPreview((await onPreviewRoi?.({ lat, lon })) ?? null);
    } catch (error) {
      setRoiPreview(null);
      setRoiPreviewError(error instanceof Error ? error.message : "Preview request failed.");
    } finally {
      setIsPreviewingRoi(false);
    }
  }

  async function handlePlanEarthEngine() {
    if (!canPlanEe) return;
    setIsPlanningEe(true);
    setEePlanError(null);
    try {
      setEePlan(
        (await onPlanEarthEngine?.({
          lat,
          lon,
          acquisition_start: acquisitionStart,
          acquisition_end: acquisitionEnd,
          cloud_percent_max: cloudPercentMax.trim() ? cloudValue : null,
          sar_orbit: "any",
          sar_polarization: "VV_VH",
          dry_run: true,
        })) ?? null,
      );
    } catch (error) {
      setEePlan(null);
      setEePlanError(error instanceof Error ? error.message : "Planning request failed.");
    } finally {
      setIsPlanningEe(false);
    }
  }

  async function handleQueueRun() {
    if (!targetOk || isQueueing) return;
    await onQueueRun?.({ lat, lon, name: runName.trim() || null });
  }

  function handleReset() {
    setLatitude("");
    setLongitude("");
    setRunName("");
    setShowAdvanced(false);
    clearComputed();
  }

  return (
    <div className="rounded-lg bg-card flex flex-col" style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.06)" }}>
      <div className="flex items-center justify-between px-4 py-2.5" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
        <h3 className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", letterSpacing: "0.07em", textTransform: "uppercase" }}>Run Workflow</h3>
        <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>Queue a new screening run</span>
      </div>
      <div className="px-4 py-3 flex flex-col gap-3">
        <Info text="Pick or enter a target, preview safe grid metadata, optionally dry-run Earth Engine planning, then queue the local run." />

        <div className="flex items-center gap-1">
          {steps.map((step, i) => (
            <div key={step.n} className="flex items-center gap-1">
              <span className="flex items-center justify-center rounded-full" style={{ width: 18, height: 18, backgroundColor: step.n === 1 ? "var(--gs-navy)" : "var(--muted)", color: step.n === 1 ? "white" : "var(--gs-slate)", fontSize: "9.5px", fontWeight: 700 }}>{step.n}</span>
              <span style={{ fontSize: "11px", fontWeight: step.n === 1 ? 600 : 400, color: step.n === 1 ? "var(--gs-navy)" : "var(--gs-slate)" }}>{step.label}</span>
              {i < steps.length - 1 && <ChevronRight size={11} style={{ color: "var(--gs-slate)", opacity: 0.35 }} />}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <Coord label="Latitude" value={latitude} min={-90} max={90} placeholder="e.g. 43.6532" invalid={hasLat && !latOk} onChange={updateLatitude} />
          <Coord label="Longitude" value={longitude} min={-180} max={180} placeholder="e.g. -79.3832" invalid={hasLon && !lonOk} onChange={updateLongitude} />
        </div>
        {((hasLat && !latOk) || (hasLon && !lonOk)) && <Message text="Latitude must be -90 to 90 and longitude must be -180 to 180." />}
        {!targetOk && <Info text="Enter a valid latitude and longitude, or pick a point on the map, before previewing or queueing." />}

        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>Large map target picker</span>
            <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>{externalTilesEnabled ? "mouse drag + scroll zoom" : "tiles disabled"}</span>
          </div>
          <TargetLeafletMap externalTilesEnabled={externalTilesEnabled} tileUrlTemplate={tileUrlTemplate} target={targetOk ? { lat, lon } : null} onTargetChange={handleTargetChange} />
        </div>

        <label className="flex flex-col gap-1">
          <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>Run name <span style={{ fontWeight: 400, color: "var(--gs-slate)" }}>optional</span></span>
          <input type="text" value={runName} onChange={(e) => setRunName(e.target.value)} placeholder="e.g. validation-run-2026" className="rounded outline-none" style={inputStyle} />
        </label>

        <div>
          <button onClick={() => setShowAdvanced((p) => !p)} className="flex items-center gap-1" style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}>
            {showAdvanced ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
            <span style={{ fontSize: "11px", color: "var(--gs-slate)", fontWeight: 500 }}>Advanced settings</span>
          </button>
          {showAdvanced && (
            <div className="mt-2 pl-3 flex flex-col gap-1.5" style={{ borderLeft: "2px solid var(--border)" }}>
              <div className="font-mono" style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase" }}>Fixed notebook grid</div>
              <div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>640 x 640 cells, 10 m cell size, 6.4 km processing ROI.</div>
              <div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>Buffer radius and resolution are fixed for A1 and are not configurable from this screen.</div>
            </div>
          )}
        </div>

        {hasPreview && (
          <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}>
            <div className="font-mono" style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase" }}>Target Preview</div>
            <div className="flex flex-wrap gap-x-4">
              {hasLat && <span className="font-mono" style={{ fontSize: "11.5px", color: "var(--gs-navy)" }}>Latitude: {latitude}</span>}
              {hasLon && <span className="font-mono" style={{ fontSize: "11.5px", color: "var(--gs-navy)" }}>Longitude: {longitude}</span>}
              {runName.trim() && <span style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>"{runName}"</span>}
            </div>
            <div className="flex items-center gap-1"><WifiOff size={9} style={{ color: "var(--gs-slate)", opacity: 0.5 }} /><span style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.55 }}>{externalTilesEnabled ? "Mouse-driven map picker available" : "External tiles disabled"}</span></div>
          </div>
        )}

        <Panel title="ROI / Grid Preview" subtitle="Preview metadata is computed before queueing." icon={<Search size={11} />} label={isPreviewingRoi ? "Previewing..." : "Preview"} disabled={!canPreviewRoi} onClick={() => void handlePreviewRoi()}>
          {roiPreviewError && <Message text={roiPreviewError} />}
          {!roiPreview && !roiPreviewError && <Info text={targetOk ? "Preview will compute grid metadata only before queueing." : "Enter a valid target before requesting ROI / Grid Preview."} />}
          {roiPreview && (
            <div className="grid grid-cols-2 gap-2">
              <Metric label="Reference" value={roiPreview.gridPreview.referenceSystemLabel} />
              <Metric label="Zone" value={`${roiPreview.gridPreview.zoneNumber} ${roiPreview.gridPreview.hemisphere}`} />
              <Metric label="Grid" value={`${roiPreview.gridPreview.widthCells} x ${roiPreview.gridPreview.heightCells} cells`} />
              <Metric label="Cell" value={`${roiPreview.gridPreview.cellSizeMeters} m`} />
              <Metric label="Window" value={`${roiPreview.roiWindowPreview.widthMeters.toFixed(0)} x ${roiPreview.roiWindowPreview.heightMeters.toFixed(0)} m`} />
              <Metric label="Affine" value={roiPreview.gridPreview.affineCoefficients.map((item) => item.toFixed(2)).join(", ")} wide />
            </div>
          )}
        </Panel>

        <Panel title="Earth Engine Backend" subtitle="Planning only. Real execution stays disabled unless backend config allows it." icon={<Satellite size={11} />} label={isPlanningEe ? "Planning..." : "Plan"} disabled={!canPlanEe} onClick={() => void handlePlanEarthEngine()}>
          <div className="grid grid-cols-3 gap-2">
            <DateField label="Start" value={acquisitionStart} onChange={(v) => { setAcquisitionStart(v); setEePlan(null); setEePlanError(null); }} />
            <DateField label="End" value={acquisitionEnd} onChange={(v) => { setAcquisitionEnd(v); setEePlan(null); setEePlanError(null); }} />
            <Small label="Cloud max" value={cloudPercentMax} onChange={(v) => { setCloudPercentMax(v); setEePlan(null); setEePlanError(null); }} type="number" />
          </div>
          {(!acquisitionOk || !cloudOk) && <Message text="Acquisition dates must be ordered and cloud max must be 0 to 100." />}
          {eePlanError && <Message text={eePlanError} />}
          {!eePlan && !eePlanError && <Info text={targetOk ? "Earth Engine planning is a dry run only; it checks backend readiness before execution." : "Enter a valid target before planning Earth Engine backend readiness."} />}
          {eePlan && (
            <div className="grid grid-cols-2 gap-2">
              <Metric label="Status" value={formatStatus(eePlan.executionStatus)} />
              <Metric label="Dry run" value={eePlan.dryRun ? "yes" : "no"} />
              <Metric label="Auth" value={formatStatus(eePlan.authReadiness.status)} />
              <Metric label="Providers" value={eePlan.plannedProviderFamilies.join(", ")} wide />
            </div>
          )}
        </Panel>

        <div className="flex gap-2">
          <button disabled={!targetOk || isQueueing} onClick={() => void handleQueueRun()} className="flex items-center justify-center gap-1.5 py-2 rounded flex-1" style={{ backgroundColor: targetOk && !isQueueing ? "var(--gs-navy)" : "var(--muted)", color: targetOk && !isQueueing ? "white" : "var(--gs-slate)", border: "none", cursor: targetOk && !isQueueing ? "pointer" : "not-allowed", fontSize: "12.5px", fontWeight: 600 }}><Play size={11} />{isQueueing ? "Queueing..." : "Queue Run"}</button>
          <button onClick={handleReset} className="flex items-center gap-1.5 px-3 py-2 rounded" style={{ backgroundColor: "transparent", color: "var(--gs-slate)", border: "1px solid var(--border)", cursor: "pointer", fontSize: "12px", fontWeight: 500 }}><RotateCcw size={11} />Reset</button>
        </div>
        {!targetOk && <Info text="Queue Run stays disabled until both target fields are valid." />}
        {targetOk && !feedback && <Info text="Ready to queue a local run. ROI preview and Earth Engine plan are optional checks." />}
        {feedback && <p style={{ fontSize: "11px", color: "var(--gs-slate)" }}>{feedback}</p>}
      </div>
    </div>
  );
}

function Coord({ label, value, min, max, placeholder, invalid, onChange }: { label: string; value: string; min: number; max: number; placeholder: string; invalid: boolean; onChange: (value: string) => void }) {
  return <label className="flex flex-col gap-1"><span style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>{label} <span style={{ fontWeight: 400, color: "var(--gs-slate)" }}>required</span></span><input type="number" inputMode="decimal" min={min} max={max} step="any" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="font-mono rounded outline-none" style={{ ...inputStyle, borderColor: invalid ? "var(--gs-red-border)" : "var(--border)" }} /></label>;
}

function Small({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return <label className="flex flex-col gap-1"><span style={smallLabel}>{label}</span><input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="font-mono rounded outline-none" style={smallInputStyle} /></label>;
}

function DateField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="flex flex-col gap-1"><span style={smallLabel}>{label}</span><input type="date" value={value} onChange={(e) => onChange(e.target.value)} className="font-mono rounded outline-none" style={smallInputStyle} /></label>;
}

function Panel({ title, subtitle, icon, label, disabled, onClick, children }: { title: string; subtitle: string; icon: ReactNode; label: string; disabled: boolean; onClick: () => void; children: ReactNode }) {
  return <div className="rounded px-3 py-2 flex flex-col gap-2" style={{ backgroundColor: "rgba(255,255,255,0.72)", border: "1px solid rgba(28,43,94,0.12)" }}><div className="flex items-center justify-between gap-2"><div><div className="font-mono" style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase" }}>{title}</div><div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>{subtitle}</div></div><button type="button" disabled={disabled} onClick={onClick} className="flex items-center gap-1.5 rounded px-2.5 py-1.5" style={{ backgroundColor: disabled ? "var(--muted)" : "var(--gs-navy)", color: disabled ? "var(--gs-slate)" : "white", border: "none", cursor: disabled ? "not-allowed" : "pointer", fontSize: "11px", fontWeight: 600 }}>{icon}{label}</button></div>{children}</div>;
}

function Message({ text }: { text: string }) {
  return <div className="rounded px-3 py-2" style={{ fontSize: "11px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}>{text}</div>;
}

function Info({ text }: { text: string }) {
  return <div className="rounded px-3 py-2" style={{ fontSize: "11px", color: "var(--gs-slate)", backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", lineHeight: "1.5" }}>{text}</div>;
}

function Metric({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return <div className={wide ? "col-span-2" : ""}><div className="font-mono" style={{ fontSize: 9, color: "var(--gs-slate)", textTransform: "uppercase" }}>{label}</div><div className="font-mono" style={{ fontSize: 11, color: "var(--gs-navy)", wordBreak: "break-word" }}>{value}</div></div>;
}

const inputStyle = { fontSize: "12px", padding: "6px 10px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" };
const smallLabel = { fontSize: "10.5px", fontWeight: 600, color: "var(--gs-slate)" };
const smallInputStyle = { fontSize: "11.5px", padding: "5px 8px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" };

function defaultAcquisitionEnd() { return new Date().toISOString().slice(0, 10); }
function defaultAcquisitionStart() { const date = new Date(); date.setUTCDate(date.getUTCDate() - 30); return date.toISOString().slice(0, 10); }
function formatStatus(value: string) { return value.split("_").filter(Boolean).map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`).join(" "); }

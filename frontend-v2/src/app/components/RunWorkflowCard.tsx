import { useEffect, useMemo, useState, type MouseEvent } from "react";
import { ChevronDown, ChevronRight, WifiOff, Play, RotateCcw, MapPin, Search, Satellite } from "lucide-react";
import type { CreateRunInput, EarthEnginePlan, EarthEnginePlanInput, RoiPreview, RoiPreviewInput } from "../api/client";

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

type TileLoadState = "loading" | "success" | "error";
const ZOOM = 15;
const TILE_SIZE = 256;

export function RunWorkflowCard({ onQueueRun, onPreviewRoi, onPlanEarthEngine, isQueueing = false, feedback = null, externalTilesEnabled = false, tileUrlTemplate = "" }: RunWorkflowCardProps) {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [runName, setRunName] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [bufferKm, setBufferKm] = useState("2.0");
  const [resolution, setResolution] = useState("640");
  const [tileStates, setTileStates] = useState<Record<string, TileLoadState>>({});
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
  const canQueue = targetOk;
  const canPreviewRoi = targetOk && !isPreviewingRoi && Boolean(onPreviewRoi);
  const templateOk = tileUrlTemplate.includes("{z}") && tileUrlTemplate.includes("{x}") && tileUrlTemplate.includes("{y}");
  const grid = useMemo(
    () => externalTilesEnabled && templateOk ? buildTiles(tileUrlTemplate, latOk ? lat : 0, lonOk ? lon : 0, ZOOM) : null,
    [externalTilesEnabled, templateOk, tileUrlTemplate, latOk, lonOk, lat, lon],
  );
  const centerLoaded = grid ? tileStates[grid.center.key] === "success" : false;
  const centerFailed = grid ? tileStates[grid.center.key] === "error" : false;

  const startDate = Date.parse(`${acquisitionStart}T00:00:00Z`);
  const endDate = Date.parse(`${acquisitionEnd}T00:00:00Z`);
  const acquisitionOk = acquisitionStart && acquisitionEnd && Number.isFinite(startDate) && Number.isFinite(endDate) && endDate >= startDate;
  const cloudValue = Number.parseFloat(cloudPercentMax);
  const cloudOk = cloudPercentMax.trim().length === 0 || (Number.isFinite(cloudValue) && cloudValue >= 0 && cloudValue <= 100);
  const canPlanEe = targetOk && Boolean(acquisitionOk) && cloudOk && !isPlanningEe && Boolean(onPlanEarthEngine);
  const hasPreview = hasLat || hasLon || runName.trim().length > 0;

  useEffect(() => {
    setTileStates(grid ? Object.fromEntries(grid.tiles.map((tile) => [tile.key, "loading" satisfies TileLoadState])) : {});
  }, [grid]);

  function clearComputed() {
    setRoiPreview(null);
    setRoiPreviewError(null);
    setEePlan(null);
    setEePlanError(null);
  }

  function updateLat(value: string) { setLatitude(value); clearComputed(); }
  function updateLon(value: string) { setLongitude(value); clearComputed(); }

  function handleMapClick(event: MouseEvent<HTMLButtonElement>) {
    if (!grid) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const displayTile = rect.width / 3;
    const dx = event.clientX - rect.left - rect.width / 2;
    const dy = event.clientY - rect.top - rect.height / 2;
    const point = pixelToLatLon(grid.centerPixel.x + dx * (TILE_SIZE / displayTile), grid.centerPixel.y + dy * (TILE_SIZE / displayTile), grid.zoom);
    setLatitude(point.lat.toFixed(8));
    setLongitude(point.lon.toFixed(8));
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
      setEePlan((await onPlanEarthEngine?.({ lat, lon, acquisition_start: acquisitionStart, acquisition_end: acquisitionEnd, cloud_percent_max: cloudPercentMax.trim() ? cloudValue : null, sar_orbit: "any", sar_polarization: "VV_VH", dry_run: true })) ?? null);
    } catch (error) {
      setEePlan(null);
      setEePlanError(error instanceof Error ? error.message : "Planning request failed.");
    } finally {
      setIsPlanningEe(false);
    }
  }

  async function handleQueueRun() {
    if (!canQueue || isQueueing) return;
    await onQueueRun?.({ lat, lon, name: runName.trim() || null });
  }

  function handleReset() {
    setLatitude(""); setLongitude(""); setRunName(""); setBufferKm("2.0"); setResolution("640"); setShowAdvanced(false); clearComputed();
  }

  return (
    <div className="rounded-lg bg-card flex flex-col" style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.06)" }}>
      <div className="flex items-center justify-between px-4 py-2.5" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
        <h3 className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", letterSpacing: "0.07em", textTransform: "uppercase" }}>Run Workflow</h3>
        <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>Queue a new screening run</span>
      </div>
      <div className="px-4 py-3 flex flex-col gap-3">
        <div className="flex items-center gap-1">{steps.map((step, i) => <div key={step.n} className="flex items-center gap-1"><span className="flex items-center justify-center rounded-full" style={{ width: 18, height: 18, backgroundColor: step.n === 1 ? "var(--gs-navy)" : "var(--muted)", color: step.n === 1 ? "white" : "var(--gs-slate)", fontSize: "9.5px", fontWeight: 700 }}>{step.n}</span><span style={{ fontSize: "11px", fontWeight: step.n === 1 ? 600 : 400, color: step.n === 1 ? "var(--gs-navy)" : "var(--gs-slate)" }}>{step.label}</span>{i < steps.length - 1 && <ChevronRight size={11} style={{ color: "var(--gs-slate)", opacity: 0.35 }} />}</div>)}</div>
        <div className="grid grid-cols-2 gap-2.5"><Coord label="Latitude" value={latitude} min={-90} max={90} placeholder="e.g. 43.6532" invalid={hasLat && !latOk} onChange={updateLat} /><Coord label="Longitude" value={longitude} min={-180} max={180} placeholder="e.g. -79.3832" invalid={hasLon && !lonOk} onChange={updateLon} /></div>
        {((hasLat && !latOk) || (hasLon && !lonOk)) && <Message text="Latitude must be -90 to 90 and longitude must be -180 to 180." />}
        <div className="flex flex-col gap-1"><div className="flex items-center justify-between"><span style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>Map point picker</span><span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>{externalTilesEnabled ? "real map tiles" : "tiles disabled"}</span></div><MapPicker grid={grid} targetOk={targetOk} centerLoaded={centerLoaded} centerFailed={centerFailed} tileStates={tileStates} externalTilesEnabled={externalTilesEnabled} templateOk={templateOk} onClick={handleMapClick} onTileLoad={(key) => setTileStates((current) => ({ ...current, [key]: "success" }))} onTileError={(key) => setTileStates((current) => ({ ...current, [key]: "error" }))} /></div>
        <label className="flex flex-col gap-1"><span style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>Run name <span style={{ fontWeight: 400, color: "var(--gs-slate)" }}>optional</span></span><input type="text" value={runName} onChange={(e) => setRunName(e.target.value)} placeholder="e.g. validation-run-2026" className="rounded outline-none" style={inputStyle} /></label>
        <div><button onClick={() => setShowAdvanced((p) => !p)} className="flex items-center gap-1" style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}>{showAdvanced ? <ChevronDown size={11} /> : <ChevronRight size={11} />}<span style={{ fontSize: "11px", color: "var(--gs-slate)", fontWeight: 500 }}>Advanced settings</span></button>{showAdvanced && <div className="mt-2 pl-3 grid grid-cols-2 gap-2.5" style={{ borderLeft: "2px solid var(--border)" }}><Small label="Buffer radius (km)" value={bufferKm} onChange={setBufferKm} /><label className="flex flex-col gap-1"><span style={smallLabel}>Grid resolution</span><select value={resolution} onChange={(e) => setResolution(e.target.value)} className="font-mono rounded outline-none" style={smallInputStyle}><option value="320">320 m</option><option value="640">640 m</option><option value="1280">1280 m</option></select></label></div>}</div>
        {hasPreview && <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}><div className="font-mono" style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase" }}>Target Preview</div><div className="flex flex-wrap gap-x-4">{hasLat && <span className="font-mono" style={{ fontSize: "11.5px", color: "var(--gs-navy)" }}>Latitude: {latitude}</span>}{hasLon && <span className="font-mono" style={{ fontSize: "11.5px", color: "var(--gs-navy)" }}>Longitude: {longitude}</span>}{runName.trim() && <span style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>"{runName}"</span>}</div><div className="flex items-center gap-1"><WifiOff size={9} style={{ color: "var(--gs-slate)", opacity: 0.5 }} /><span style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.55 }}>{externalTilesEnabled ? "Map picker available" : "External tiles disabled"}</span></div></div>}
        <Panel title="ROI / Grid Preview" subtitle="Preview metadata is computed before queueing." icon={<Search size={11} />} label={isPreviewingRoi ? "Previewing..." : "Preview"} disabled={!canPreviewRoi} onClick={() => void handlePreviewRoi()}>{roiPreviewError && <Message text={roiPreviewError} />}{roiPreview && <div className="grid grid-cols-2 gap-2"><Metric label="Reference" value={roiPreview.gridPreview.referenceSystemLabel} /><Metric label="Zone" value={`${roiPreview.gridPreview.zoneNumber} ${roiPreview.gridPreview.hemisphere}`} /><Metric label="Grid" value={`${roiPreview.gridPreview.widthCells} x ${roiPreview.gridPreview.heightCells} cells`} /><Metric label="Cell" value={`${roiPreview.gridPreview.cellSizeMeters} m`} /><Metric label="Window" value={`${roiPreview.roiWindowPreview.widthMeters.toFixed(0)} x ${roiPreview.roiWindowPreview.heightMeters.toFixed(0)} m`} /><Metric label="Affine" value={roiPreview.gridPreview.affineCoefficients.map((item) => item.toFixed(2)).join(", ")} wide /></div>}</Panel>
        <Panel title="Earth Engine Backend" subtitle="Planning only. Real execution stays disabled unless backend config allows it." icon={<Satellite size={11} />} label={isPlanningEe ? "Planning..." : "Plan"} disabled={!canPlanEe} onClick={() => void handlePlanEarthEngine()}><div className="grid grid-cols-3 gap-2"><DateField label="Start" value={acquisitionStart} onChange={(v) => { setAcquisitionStart(v); setEePlan(null); setEePlanError(null); }} /><DateField label="End" value={acquisitionEnd} onChange={(v) => { setAcquisitionEnd(v); setEePlan(null); setEePlanError(null); }} /><Small label="Cloud max" value={cloudPercentMax} onChange={(v) => { setCloudPercentMax(v); setEePlan(null); setEePlanError(null); }} type="number" /></div>{(!acquisitionOk || !cloudOk) && <Message text="Acquisition dates must be ordered and cloud max must be 0 to 100." />}{eePlanError && <Message text={eePlanError} />}{eePlan && <div className="grid grid-cols-2 gap-2"><Metric label="Status" value={formatStatus(eePlan.executionStatus)} /><Metric label="Dry run" value={eePlan.dryRun ? "yes" : "no"} /><Metric label="Auth" value={formatStatus(eePlan.authReadiness.status)} /><Metric label="Providers" value={eePlan.plannedProviderFamilies.join(", ")} wide /></div>}</Panel>
        <div className="flex gap-2"><button disabled={!canQueue || isQueueing} onClick={() => void handleQueueRun()} className="flex items-center justify-center gap-1.5 py-2 rounded flex-1" style={{ backgroundColor: canQueue && !isQueueing ? "var(--gs-navy)" : "var(--muted)", color: canQueue && !isQueueing ? "white" : "var(--gs-slate)", border: "none", cursor: canQueue && !isQueueing ? "pointer" : "not-allowed", fontSize: "12.5px", fontWeight: 600 }}><Play size={11} />{isQueueing ? "Queueing..." : "Queue Run"}</button><button onClick={handleReset} className="flex items-center gap-1.5 px-3 py-2 rounded" style={{ backgroundColor: "transparent", color: "var(--gs-slate)", border: "1px solid var(--border)", cursor: "pointer", fontSize: "12px", fontWeight: 500 }}><RotateCcw size={11} />Reset</button></div>{feedback && <p style={{ fontSize: "11px", color: "var(--gs-slate)" }}>{feedback}</p>}
      </div>
    </div>
  );
}

function MapPicker({ grid, targetOk, centerLoaded, centerFailed, tileStates, externalTilesEnabled, templateOk, onClick, onTileLoad, onTileError }: { grid: ReturnType<typeof buildTiles> | null; targetOk: boolean; centerLoaded: boolean; centerFailed: boolean; tileStates: Record<string, TileLoadState>; externalTilesEnabled: boolean; templateOk: boolean; onClick: (event: MouseEvent<HTMLButtonElement>) => void; onTileLoad: (key: string) => void; onTileError: (key: string) => void }) {
  if (!externalTilesEnabled) return <MapNotice title="Map picker disabled" detail="Enable External map tiles in Settings to see a real map and click to place the target pin." />;
  if (!templateOk) return <MapNotice title="Map picker unavailable" detail="Tile URL template must include {z}, {x}, and {y}." />;
  if (!grid) return <MapNotice title="Map picker loading" detail="Preparing map tiles." />;
  return <div className="rounded overflow-hidden" style={{ border: "1px solid rgba(28,43,94,0.14)", backgroundColor: "rgba(248,247,242,0.95)" }}><button type="button" onClick={onClick} className="block" style={{ position: "relative", width: "100%", height: 300, overflow: "hidden", border: "none", padding: 0, cursor: "crosshair", backgroundColor: "rgba(248,247,242,0.95)" }}>{!centerFailed && <div style={{ position: "absolute", inset: 0, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gridTemplateRows: "repeat(3, 1fr)" }}>{grid.tiles.map((tile) => <div key={tile.key} style={{ position: "relative", overflow: "hidden" }}><img src={tile.url} alt={tile.isCenter ? "Target map center tile" : "Target map surrounding tile"} onLoad={() => onTileLoad(tile.key)} onError={() => onTileError(tile.key)} style={{ width: "100%", height: "100%", objectFit: "cover", display: tileStates[tile.key] === "error" ? "none" : "block", opacity: tileStates[tile.key] === "loading" ? 0.45 : 1 }} />{tileStates[tile.key] === "error" && <span style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, color: "var(--gs-slate)" }}>tile unavailable</span>}</div>)}</div>}{centerFailed && <MapNotice title="Tile preview failed" detail="The configured tile URL did not return the center map image." absolute />}{tileStates[grid.center.key] === "loading" && !centerLoaded && !centerFailed && <MapNotice title="Loading map..." detail="Waiting for the center tile image." absolute />}{centerLoaded && <div style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%, -50%)", pointerEvents: "none", textAlign: "center" }}>{targetOk ? <><span style={{ width: 30, height: 30, borderRadius: 999, backgroundColor: "rgba(255,255,255,0.86)", border: "2px solid var(--gs-red)", display: "inline-flex", alignItems: "center", justifyContent: "center", boxShadow: "0 1px 5px rgba(28,43,94,0.25)" }}><MapPin size={17} style={{ color: "var(--gs-red)" }} /></span><div className="font-mono" style={{ fontSize: 9, fontWeight: 700, color: "var(--gs-navy)", backgroundColor: "rgba(255,255,255,0.9)", borderRadius: 3, padding: "1px 5px", marginTop: 3 }}>Target</div></> : <span style={{ fontSize: 11, color: "var(--gs-navy)", backgroundColor: "rgba(255,255,255,0.9)", padding: "4px 7px", borderRadius: 4 }}>Click map to place target pin</span>}</div>}</button><div className="px-2.5 py-1.5" style={{ fontSize: 10, color: "var(--gs-slate)", borderTop: "1px solid rgba(28,43,94,0.12)", display: "flex", justifyContent: "space-between" }}><span>{grid.providerLabel}</span><span className="font-mono">z{grid.zoom} x{grid.center.x} y{grid.center.y}</span></div></div>;
}

function MapNotice({ title, detail, absolute = false }: { title: string; detail: string; absolute?: boolean }) { return <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ minHeight: absolute ? undefined : 170, position: absolute ? "absolute" : "relative", inset: absolute ? 0 : undefined, textAlign: "center" }}><div style={{ fontSize: 12, fontWeight: 600, color: "var(--gs-navy)" }}>{title}</div><div style={{ fontSize: "10.5px", color: "var(--gs-slate)", maxWidth: 300 }}>{detail}</div></div>; }
function Coord({ label, value, min, max, placeholder, invalid, onChange }: { label: string; value: string; min: number; max: number; placeholder: string; invalid: boolean; onChange: (value: string) => void }) { return <label className="flex flex-col gap-1"><span style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>{label} <span style={{ fontWeight: 400, color: "var(--gs-slate)" }}>required</span></span><input type="number" inputMode="decimal" min={min} max={max} step="any" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} aria-invalid={invalid} className="font-mono rounded outline-none" style={inputStyle} /></label>; }
function Small({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) { return <label className="flex flex-col gap-1"><span style={smallLabel}>{label}</span><input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="font-mono rounded outline-none" style={smallInputStyle} /></label>; }
function DateField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label className="flex flex-col gap-1"><span style={smallLabel}>{label}</span><input type="date" value={value} onChange={(e) => onChange(e.target.value)} className="font-mono rounded outline-none" style={smallInputStyle} /></label>; }
function Panel({ title, subtitle, icon, label, disabled, onClick, children }: { title: string; subtitle: string; icon: React.ReactNode; label: string; disabled: boolean; onClick: () => void; children: React.ReactNode }) { return <div className="rounded px-3 py-2 flex flex-col gap-2" style={{ backgroundColor: "rgba(255,255,255,0.72)", border: "1px solid rgba(28,43,94,0.12)" }}><div className="flex items-center justify-between gap-2"><div><div className="font-mono" style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase" }}>{title}</div><div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>{subtitle}</div></div><button type="button" disabled={disabled} onClick={onClick} className="flex items-center gap-1.5 rounded px-2.5 py-1.5" style={{ backgroundColor: disabled ? "var(--muted)" : "var(--gs-navy)", color: disabled ? "var(--gs-slate)" : "white", border: "none", cursor: disabled ? "not-allowed" : "pointer", fontSize: "11px", fontWeight: 600 }}>{icon}{label}</button></div>{children}</div>; }
function Message({ text }: { text: string }) { return <div className="rounded px-3 py-2" style={{ fontSize: "11px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}>{text}</div>; }
function Metric({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) { return <div className={wide ? "col-span-2" : ""}><div className="font-mono" style={{ fontSize: 9, color: "var(--gs-slate)", textTransform: "uppercase" }}>{label}</div><div className="font-mono" style={{ fontSize: 11, color: "var(--gs-navy)", wordBreak: "break-word" }}>{value}</div></div>; }

const inputStyle = { fontSize: "12px", padding: "6px 10px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" };
const smallLabel = { fontSize: "10.5px", fontWeight: 600, color: "var(--gs-slate)" };
const smallInputStyle = { fontSize: "11.5px", padding: "5px 8px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" };

function buildTiles(template: string, latitude: number, longitude: number, zoom: number) {
  const centerPixel = latLonToPixel(latitude, longitude, zoom);
  const center = { x: Math.floor(centerPixel.x / TILE_SIZE), y: Math.floor(centerPixel.y / TILE_SIZE), key: "" };
  center.key = `${zoom}-${center.x}-${center.y}`;
  const tiles = [-1, 0, 1].flatMap((yo) => [-1, 0, 1].map((xo) => { const x = clampTile(center.x + xo, zoom); const y = clampTile(center.y + yo, zoom); return { key: `${zoom}-${x}-${y}`, x, y, isCenter: xo === 0 && yo === 0, url: template.replaceAll("{z}", String(zoom)).replaceAll("{x}", String(x)).replaceAll("{y}", String(y)) }; }));
  return { providerLabel: tileLabel(template), zoom, center, centerPixel, tiles };
}
function latLonToPixel(latitude: number, longitude: number, zoom: number) { const sinLat = Math.sin((clamp(latitude, -85.05112878, 85.05112878) * Math.PI) / 180); const size = TILE_SIZE * 2 ** zoom; return { x: ((longitude + 180) / 360) * size, y: (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * size }; }
function pixelToLatLon(x: number, y: number, zoom: number) { const size = TILE_SIZE * 2 ** zoom; const lon = (clamp(x, 0, size - 1) / size) * 360 - 180; const n = Math.PI - (2 * Math.PI * clamp(y, 0, size - 1)) / size; const lat = (180 / Math.PI) * Math.atan(Math.sinh(n)); return { lat: clamp(lat, -90, 90), lon: clamp(lon, -180, 180) }; }
function clampTile(value: number, zoom: number) { return Math.max(0, Math.min(2 ** zoom - 1, value)); }
function tileLabel(template: string) { try { return new URL(template).hostname || "custom tile template"; } catch (_error) { return "custom tile template"; } }
function clamp(value: number, min: number, max: number) { return Math.max(min, Math.min(max, value)); }
function defaultAcquisitionEnd() { return new Date().toISOString().slice(0, 10); }
function defaultAcquisitionStart() { const date = new Date(); date.setUTCDate(date.getUTCDate() - 30); return date.toISOString().slice(0, 10); }
function formatStatus(value: string) { return value.split("_").filter(Boolean).map((part) => part[0]?.toUpperCase() + part.slice(1)).join(" "); }

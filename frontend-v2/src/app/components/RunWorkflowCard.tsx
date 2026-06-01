import { useEffect, useMemo, useState } from "react";
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
  externalTilesEnabled?: boolean;
  tileUrlTemplate?: string;
}

const PREVIEW_TILE_ZOOM = 15;
type TilePreviewStatus = "idle" | "loading" | "success" | "error";

export function RunWorkflowCard({
  onQueueRun,
  isQueueing = false,
  feedback = null,
  externalTilesEnabled = false,
  tileUrlTemplate = "",
}: RunWorkflowCardProps) {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [runName, setRunName] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [bufferKm, setBufferKm] = useState("2.0");
  const [resolution, setResolution] = useState("640");
  const [tilePreviewStatus, setTilePreviewStatus] = useState<TilePreviewStatus>("idle");

  const latitudeValue = Number.parseFloat(latitude);
  const longitudeValue = Number.parseFloat(longitude);
  const hasLatitude = latitude.trim().length > 0;
  const hasLongitude = longitude.trim().length > 0;
  const latitudeValid = Number.isFinite(latitudeValue) && latitudeValue >= -90 && latitudeValue <= 90;
  const longitudeValid = Number.isFinite(longitudeValue) && longitudeValue >= -180 && longitudeValue <= 180;
  const canQueue = latitudeValid && longitudeValid;
  const hasPreview = hasLatitude || hasLongitude || runName.trim().length > 0;
  const tileTemplateValid = hasTileTemplatePlaceholders(tileUrlTemplate);
  const tilePreview = useMemo(
    () =>
      externalTilesEnabled && latitudeValid && longitudeValid && tileTemplateValid
        ? buildTilePreview(tileUrlTemplate, latitudeValue, longitudeValue, PREVIEW_TILE_ZOOM)
        : null,
    [externalTilesEnabled, latitudeValid, latitudeValue, longitudeValid, longitudeValue, tileTemplateValid, tileUrlTemplate],
  );

  useEffect(() => {
    if (!externalTilesEnabled || !tileTemplateValid || !latitudeValid || !longitudeValid || !tilePreview) {
      setTilePreviewStatus("idle");
      return;
    }
    setTilePreviewStatus("loading");
  }, [externalTilesEnabled, latitudeValid, longitudeValid, tilePreview, tileTemplateValid]);

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
                {!externalTilesEnabled
                  ? "External tiles disabled"
                  : tilePreviewStatus === "success"
                    ? "External tile preview enabled"
                    : tilePreviewStatus === "loading"
                      ? "Loading tile preview..."
                      : tilePreviewStatus === "error"
                        ? "Tile preview failed to load"
                        : "Tile preview ready"}
              </span>
            </div>

            <div
              className="rounded overflow-hidden"
              style={{
                backgroundColor: "rgba(248,247,242,0.9)",
                border: "1px solid rgba(28,43,94,0.12)",
                minHeight: "172px",
              }}
            >
              {!externalTilesEnabled && (
                <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ minHeight: "170px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>Map preview disabled</div>
                  <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", textAlign: "center", maxWidth: "260px" }}>
                    Enable External map tiles in Settings to preview map tiles.
                  </div>
                </div>
              )}

              {externalTilesEnabled && !tileTemplateValid && (
                <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ minHeight: "170px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>
                    Map preview unavailable
                  </div>
                  <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", textAlign: "center", maxWidth: "280px" }}>
                    Tile URL template must include {"{z}"}, {"{x}"}, and {"{y}"}.
                  </div>
                </div>
              )}

              {externalTilesEnabled && tileTemplateValid && (!latitudeValid || !longitudeValid) && (
                <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ minHeight: "170px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>
                    Map preview ready
                  </div>
                  <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", textAlign: "center", maxWidth: "280px" }}>
                    Enter latitude and longitude to preview map tile.
                  </div>
                </div>
              )}

              {tilePreview && (
                <div className="flex flex-col">
                  <div style={{ position: "relative", width: "100%", aspectRatio: "1 / 1", backgroundColor: "rgba(248,247,242,0.95)" }}>
                    {tilePreviewStatus !== "error" && (
                      <img
                        key={tilePreview.url}
                        src={tilePreview.url}
                        alt="Target map tile preview"
                        onLoad={() => setTilePreviewStatus("success")}
                        onError={() => setTilePreviewStatus("error")}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                          display: tilePreviewStatus === "success" ? "block" : "none",
                        }}
                      />
                    )}
                    {tilePreviewStatus === "loading" && (
                      <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ position: "absolute", inset: 0 }}>
                        <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>Loading tile preview...</div>
                        <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", textAlign: "center", maxWidth: "280px" }}>
                          Waiting for tile image response from the configured template.
                        </div>
                      </div>
                    )}
                    {tilePreviewStatus === "error" && (
                      <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ position: "absolute", inset: 0 }}>
                        <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>
                          Tile preview failed to load. Check tile URL template.
                        </div>
                        <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", textAlign: "center", maxWidth: "280px" }}>
                          The current tile request did not return a usable image preview.
                        </div>
                      </div>
                    )}
                  </div>
                  <div
                    className="px-2.5 py-1.5"
                    style={{
                      fontSize: "10px",
                      color: "var(--gs-slate)",
                      borderTop: "1px solid rgba(28,43,94,0.12)",
                      backgroundColor: "rgba(255,255,255,0.72)",
                      display: "flex",
                      justifyContent: "space-between",
                      gap: "12px",
                      flexWrap: "wrap",
                    }}
                  >
                    <span>{tilePreview.providerLabel}</span>
                    <span className="font-mono">
                      z{tilePreview.zoom} x{tilePreview.x} y{tilePreview.y}
                    </span>
                  </div>
                </div>
              )}
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

function hasTileTemplatePlaceholders(template: string): boolean {
  return template.includes("{z}") && template.includes("{x}") && template.includes("{y}");
}

function buildTilePreview(template: string, latitude: number, longitude: number, zoom: number) {
  const { x, y } = latLonToTile(latitude, longitude, zoom);
  return {
    url: template
      .replaceAll("{z}", String(zoom))
      .replaceAll("{x}", String(x))
      .replaceAll("{y}", String(y)),
    providerLabel: tileTemplateLabel(template),
    zoom,
    x,
    y,
  };
}

function latLonToTile(latitude: number, longitude: number, zoom: number): { x: number; y: number } {
  const latRadians = (Math.max(Math.min(latitude, 85.05112878), -85.05112878) * Math.PI) / 180;
  const tilesPerAxis = 2 ** zoom;
  const x = Math.floor(((longitude + 180) / 360) * tilesPerAxis);
  const y = Math.floor(
    ((1 - Math.log(Math.tan(latRadians) + 1 / Math.cos(latRadians)) / Math.PI) / 2) * tilesPerAxis,
  );
  return {
    x: Math.max(0, Math.min(tilesPerAxis - 1, x)),
    y: Math.max(0, Math.min(tilesPerAxis - 1, y)),
  };
}

function tileTemplateLabel(template: string): string {
  try {
    const url = new URL(template);
    return url.hostname || "custom tile template";
  } catch (_error) {
    return "custom tile template";
  }
}

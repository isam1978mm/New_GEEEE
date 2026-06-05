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

const PREVIEW_TILE_ZOOM = 15;
type TilePreviewStatus = "idle" | "loading" | "success" | "error";
type TileLoadState = "loading" | "success" | "error";

export function RunWorkflowCard({
  onQueueRun,
  onPreviewRoi,
  onPlanEarthEngine,
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

  const latitudeValue = Number.parseFloat(latitude);
  const longitudeValue = Number.parseFloat(longitude);
  const hasLatitude = latitude.trim().length > 0;
  const hasLongitude = longitude.trim().length > 0;
  const latitudeValid = Number.isFinite(latitudeValue) && latitudeValue >= -90 && latitudeValue <= 90;
  const longitudeValid = Number.isFinite(longitudeValue) && longitudeValue >= -180 && longitudeValue <= 180;
  const canQueue = latitudeValid && longitudeValid;
  const canPreviewRoi = canQueue && !isPreviewingRoi && Boolean(onPreviewRoi);
  const acquisitionStartDate = Date.parse(`${acquisitionStart}T00:00:00Z`);
  const acquisitionEndDate = Date.parse(`${acquisitionEnd}T00:00:00Z`);
  const acquisitionWindowValid =
    acquisitionStart.length > 0 &&
    acquisitionEnd.length > 0 &&
    Number.isFinite(acquisitionStartDate) &&
    Number.isFinite(acquisitionEndDate) &&
    acquisitionEndDate >= acquisitionStartDate;
  const cloudPercentValue = Number.parseFloat(cloudPercentMax);
  const cloudPercentValid =
    cloudPercentMax.trim().length === 0 || (Number.isFinite(cloudPercentValue) && cloudPercentValue >= 0 && cloudPercentValue <= 100);
  const canPlanEe = canQueue && acquisitionWindowValid && cloudPercentValid && !isPlanningEe && Boolean(onPlanEarthEngine);
  const hasPreview = hasLatitude || hasLongitude || runName.trim().length > 0;
  const tileTemplateValid = hasTileTemplatePlaceholders(tileUrlTemplate);
  const tilePreview = useMemo(
    () =>
      externalTilesEnabled && latitudeValid && longitudeValid && tileTemplateValid
        ? buildTilePreviewGrid(tileUrlTemplate, latitudeValue, longitudeValue, PREVIEW_TILE_ZOOM)
        : null,
    [externalTilesEnabled, latitudeValid, latitudeValue, longitudeValid, longitudeValue, tileTemplateValid, tileUrlTemplate],
  );

  useEffect(() => {
    if (!externalTilesEnabled || !tileTemplateValid || !latitudeValid || !longitudeValid || !tilePreview) {
      setTilePreviewStatus("idle");
      setTileStates({});
      return;
    }
    setTilePreviewStatus("loading");
    setTileStates(
      Object.fromEntries(tilePreview.tiles.map((tile) => [tile.key, "loading" satisfies TileLoadState])),
    );
  }, [externalTilesEnabled, latitudeValid, longitudeValid, tilePreview, tileTemplateValid]);

  function handleReset() {
    setLatitude(""); setLongitude(""); setRunName("");
    setBufferKm("2.0"); setResolution("640");
    setShowAdvanced(false);
    setRoiPreview(null);
    setRoiPreviewError(null);
    setEePlan(null);
    setEePlanError(null);
  }

  function handleLatitudeChange(value: string) {
    setLatitude(value);
    setRoiPreview(null);
    setRoiPreviewError(null);
    setEePlan(null);
    setEePlanError(null);
  }

  function handleLongitudeChange(value: string) {
    setLongitude(value);
    setRoiPreview(null);
    setRoiPreviewError(null);
    setEePlan(null);
    setEePlanError(null);
  }

  async function handlePreviewRoi() {
    if (!canPreviewRoi) {
      return;
    }
    setIsPreviewingRoi(true);
    setRoiPreviewError(null);
    try {
      const preview = await onPreviewRoi?.({ lat: latitudeValue, lon: longitudeValue });
      setRoiPreview(preview ?? null);
    } catch (error) {
      setRoiPreview(null);
      setRoiPreviewError(error instanceof Error ? error.message : "Preview request failed.");
    } finally {
      setIsPreviewingRoi(false);
    }
  }

  async function handlePlanEarthEngine() {
    if (!canPlanEe) {
      return;
    }
    setIsPlanningEe(true);
    setEePlanError(null);
    try {
      const plan = await onPlanEarthEngine?.({
        lat: latitudeValue,
        lon: longitudeValue,
        acquisition_start: acquisitionStart,
        acquisition_end: acquisitionEnd,
        cloud_percent_max: cloudPercentMax.trim().length > 0 ? cloudPercentValue : null,
        sar_orbit: "any",
        sar_polarization: "VV_VH",
        dry_run: true,
      });
      setEePlan(plan ?? null);
    } catch (error) {
      setEePlan(null);
      setEePlanError(error instanceof Error ? error.message : "Planning request failed.");
    } finally {
      setIsPlanningEe(false);
    }
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

  const centerTileFailed = tilePreview ? tileStates[tilePreview.centerTile.key] === "error" : false;
  const centerTileLoaded = tilePreview ? tileStates[tilePreview.centerTile.key] === "success" : false;
  const surroundingTileFailure =
    tilePreview?.tiles.some((tile) => !tile.isCenter && tileStates[tile.key] === "error") ?? false;

  function handleTileLoad(tileKey: string, isCenter: boolean) {
    setTileStates((current) => ({ ...current, [tileKey]: "success" }));
    if (isCenter) {
      setTilePreviewStatus("success");
    }
  }

  function handleTileError(tileKey: string, isCenter: boolean) {
    setTileStates((current) => ({ ...current, [tileKey]: "error" }));
    if (isCenter) {
      setTilePreviewStatus("error");
    }
  }

  function handleLocalPickerClick(event: MouseEvent<HTMLButtonElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const xRatio = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
    const yRatio = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));
    const baseLatitude = latitudeValid ? latitudeValue : 0;
    const baseLongitude = longitudeValid ? longitudeValue : 0;
    const nextLatitude = clamp(baseLatitude + (0.5 - yRatio) * 0.1, -90, 90);
    const nextLongitude = clamp(baseLongitude + (xRatio - 0.5) * 0.1, -180, 180);
    setLatitude(nextLatitude.toFixed(6));
    setLongitude(nextLongitude.toFixed(6));
    setRoiPreview(null);
    setRoiPreviewError(null);
    setEePlan(null);
    setEePlanError(null);
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
              onChange={(e) => handleLatitudeChange(e.target.value)}
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
              onChange={(e) => handleLongitudeChange(e.target.value)}
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
        {((hasLatitude && !latitudeValid) || (hasLongitude && !longitudeValid)) && (
          <div
            className="rounded px-3 py-2"
            style={{
              fontSize: "11px",
              color: "var(--gs-red)",
              backgroundColor: "var(--gs-red-bg)",
              border: "1px solid var(--gs-red-border)",
            }}
          >
            Latitude must be -90 to 90 and longitude must be -180 to 180.
          </div>
        )}

        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>
              Point picker
            </span>
            <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>local preview</span>
          </div>
          <button
            type="button"
            onClick={handleLocalPickerClick}
            className="rounded"
            style={{
              position: "relative",
              minHeight: "128px",
              backgroundColor: "rgba(248,247,242,0.95)",
              border: "1px solid rgba(28,43,94,0.14)",
              cursor: "crosshair",
              overflow: "hidden",
            }}
          >
            <span style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(rgba(28,43,94,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(28,43,94,0.08) 1px, transparent 1px)", backgroundSize: "32px 32px" }} />
            <span style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: "1px", backgroundColor: "rgba(28,43,94,0.18)" }} />
            <span style={{ position: "absolute", top: "50%", left: 0, right: 0, height: "1px", backgroundColor: "rgba(28,43,94,0.18)" }} />
            {latitudeValid && longitudeValid ? (
              <span
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "50%",
                  transform: "translate(-50%, -50%)",
                  width: "24px",
                  height: "24px",
                  border: "2px solid var(--gs-red)",
                  borderRadius: "999px",
                  backgroundColor: "rgba(255,255,255,0.82)",
                  boxShadow: "0 1px 4px rgba(28,43,94,0.18)",
                }}
              >
                <MapPin size={13} style={{ color: "var(--gs-red)", margin: "2px auto 0" }} />
              </span>
            ) : (
              <span
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "50%",
                  transform: "translate(-50%, -50%)",
                  fontSize: "11px",
                  color: "var(--gs-slate)",
                }}
              >
                Click to seed point
              </span>
            )}
          </button>
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
                  <div
                    style={{
                      position: "relative",
                      width: "100%",
                      height: "360px",
                      backgroundColor: "rgba(248,247,242,0.95)",
                      overflow: "hidden",
                    }}
                  >
                    {tilePreviewStatus !== "error" && (
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(3, 1fr)",
                          gridTemplateRows: "repeat(3, 1fr)",
                          width: "100%",
                          height: "100%",
                        }}
                      >
                        {tilePreview.tiles.map((tile) => (
                          <div
                            key={tile.key}
                            style={{
                              position: "relative",
                              overflow: "hidden",
                              backgroundColor: tileStates[tile.key] === "error" ? "rgba(148,163,184,0.12)" : "rgba(248,247,242,0.6)",
                            }}
                          >
                            <img
                              src={tile.url}
                              alt={tile.isCenter ? "Target map tile preview center tile" : "Target map tile preview surrounding tile"}
                              onLoad={() => handleTileLoad(tile.key, tile.isCenter)}
                              onError={() => handleTileError(tile.key, tile.isCenter)}
                              style={{
                                width: "100%",
                                height: "100%",
                                objectFit: "cover",
                                display: tileStates[tile.key] === "error" ? "none" : "block",
                                opacity: tileStates[tile.key] === "loading" ? 0.45 : 1,
                              }}
                            />
                            {tileStates[tile.key] === "error" && !tile.isCenter && (
                              <div
                                style={{
                                  position: "absolute",
                                  inset: 0,
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: "10px",
                                  color: "var(--gs-slate)",
                                }}
                              >
                                tile unavailable
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    {tilePreviewStatus === "loading" && !centerTileLoaded && (
                      <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ position: "absolute", inset: 0 }}>
                        <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>Loading tile preview...</div>
                        <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", textAlign: "center", maxWidth: "280px" }}>
                          Waiting for the center tile image response from the configured template.
                        </div>
                      </div>
                    )}
                    {tilePreviewStatus === "error" && centerTileFailed && (
                      <div className="flex flex-col items-center justify-center gap-1 px-4 py-6" style={{ position: "absolute", inset: 0 }}>
                        <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}>
                          Tile preview failed to load. Check tile URL template.
                        </div>
                        <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", textAlign: "center", maxWidth: "280px" }}>
                          The current tile request did not return a usable image preview.
                        </div>
                      </div>
                    )}
                    {centerTileLoaded && (
                      <div
                        style={{
                          position: "absolute",
                          left: "50%",
                          top: "50%",
                          transform: "translate(-50%, -50%)",
                          pointerEvents: "none",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        <div
                          style={{
                            position: "relative",
                            width: "28px",
                            height: "28px",
                            border: "2px solid rgba(255,255,255,0.92)",
                            borderRadius: "999px",
                            boxShadow: "0 0 0 1px rgba(28,43,94,0.35)",
                            backgroundColor: "rgba(28,43,94,0.08)",
                          }}
                        >
                          <span style={{ position: "absolute", left: "50%", top: "2px", bottom: "2px", width: "2px", backgroundColor: "var(--gs-red)", transform: "translateX(-50%)" }} />
                          <span style={{ position: "absolute", top: "50%", left: "2px", right: "2px", height: "2px", backgroundColor: "var(--gs-red)", transform: "translateY(-50%)" }} />
                        </div>
                        <span
                          className="font-mono"
                          style={{
                            fontSize: "9px",
                            fontWeight: 700,
                            color: "var(--gs-navy)",
                            backgroundColor: "rgba(255,255,255,0.88)",
                            border: "1px solid rgba(28,43,94,0.12)",
                            padding: "1px 5px",
                            borderRadius: "3px",
                          }}
                        >
                          Target
                        </span>
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
                      z{tilePreview.zoom} x{tilePreview.centerTile.x} y{tilePreview.centerTile.y}
                    </span>
                  </div>
                  {centerTileLoaded && surroundingTileFailure && (
                    <div
                      className="px-2.5 py-1.5"
                      style={{
                        fontSize: "10px",
                        color: "var(--gs-slate)",
                        borderTop: "1px solid rgba(28,43,94,0.08)",
                        backgroundColor: "rgba(255,255,255,0.65)",
                      }}
                    >
                      Some surrounding tiles failed to load.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        <div
          className="rounded px-3 py-2 flex flex-col gap-2"
          style={{ backgroundColor: "rgba(255,255,255,0.72)", border: "1px solid rgba(28,43,94,0.12)" }}
        >
          <div className="flex items-center justify-between gap-2">
            <div>
              <div
                className="font-mono"
                style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
              >
                ROI / Grid Preview
              </div>
              <div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                Preview metadata is computed before queueing.
              </div>
            </div>
            <button
              type="button"
              disabled={!canPreviewRoi}
              onClick={() => void handlePreviewRoi()}
              className="flex items-center gap-1.5 rounded px-2.5 py-1.5"
              style={{
                backgroundColor: canPreviewRoi ? "var(--gs-navy)" : "var(--muted)",
                color: canPreviewRoi ? "white" : "var(--gs-slate)",
                border: "none",
                cursor: canPreviewRoi ? "pointer" : "not-allowed",
                fontSize: "11px",
                fontWeight: 600,
                whiteSpace: "nowrap",
              }}
            >
              <Search size={11} />
              {isPreviewingRoi ? "Previewing..." : "Preview"}
            </button>
          </div>

          {roiPreviewError && (
            <div
              className="rounded px-2 py-1.5"
              style={{ fontSize: "11px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}
            >
              {roiPreviewError}
            </div>
          )}

          {roiPreview && (
            <div className="grid grid-cols-2 gap-2">
              <PreviewMetric label="Reference" value={roiPreview.gridPreview.referenceSystemLabel} />
              <PreviewMetric label="Zone" value={`${roiPreview.gridPreview.zoneNumber} ${roiPreview.gridPreview.hemisphere}`} />
              <PreviewMetric label="Grid" value={`${roiPreview.gridPreview.widthCells} x ${roiPreview.gridPreview.heightCells} cells`} />
              <PreviewMetric label="Cell" value={`${roiPreview.gridPreview.cellSizeMeters} m`} />
              <PreviewMetric label="Window" value={`${roiPreview.roiWindowPreview.widthMeters.toFixed(0)} x ${roiPreview.roiWindowPreview.heightMeters.toFixed(0)} m`} />
              <PreviewMetric label="Affine" value={roiPreview.gridPreview.affineCoefficients.map((item) => item.toFixed(2)).join(", ")} wide />
              {roiPreview.warnings.length > 0 && (
                <div className="col-span-2" style={{ fontSize: "10px", color: "var(--gs-slate)" }}>
                  {roiPreview.warnings[0]}
                </div>
              )}
            </div>
          )}
        </div>

        <div
          className="rounded px-3 py-2 flex flex-col gap-2"
          style={{ backgroundColor: "rgba(255,255,255,0.72)", border: "1px solid rgba(28,43,94,0.12)" }}
        >
          <div className="flex items-center justify-between gap-2">
            <div>
              <div
                className="font-mono"
                style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
              >
                Earth Engine Backend
              </div>
              <div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                Planning only. Real execution stays disabled unless backend config allows it.
              </div>
            </div>
            <button
              type="button"
              disabled={!canPlanEe}
              onClick={() => void handlePlanEarthEngine()}
              className="flex items-center gap-1.5 rounded px-2.5 py-1.5"
              style={{
                backgroundColor: canPlanEe ? "var(--gs-navy)" : "var(--muted)",
                color: canPlanEe ? "white" : "var(--gs-slate)",
                border: "none",
                cursor: canPlanEe ? "pointer" : "not-allowed",
                fontSize: "11px",
                fontWeight: 600,
                whiteSpace: "nowrap",
              }}
            >
              <Satellite size={11} />
              {isPlanningEe ? "Planning..." : "Plan"}
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="flex flex-col gap-1">
              <label style={{ fontSize: "10px", fontWeight: 600, color: "var(--gs-slate)" }}>
                Start
              </label>
              <input
                type="date"
                value={acquisitionStart}
                onChange={(event) => {
                  setAcquisitionStart(event.target.value);
                  setEePlan(null);
                  setEePlanError(null);
                }}
                className="font-mono rounded outline-none"
                style={{ fontSize: "11px", padding: "5px 7px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label style={{ fontSize: "10px", fontWeight: 600, color: "var(--gs-slate)" }}>
                End
              </label>
              <input
                type="date"
                value={acquisitionEnd}
                onChange={(event) => {
                  setAcquisitionEnd(event.target.value);
                  setEePlan(null);
                  setEePlanError(null);
                }}
                className="font-mono rounded outline-none"
                style={{ fontSize: "11px", padding: "5px 7px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label style={{ fontSize: "10px", fontWeight: 600, color: "var(--gs-slate)" }}>
                Cloud max
              </label>
              <input
                type="number"
                min={0}
                max={100}
                step="1"
                value={cloudPercentMax}
                onChange={(event) => {
                  setCloudPercentMax(event.target.value);
                  setEePlan(null);
                  setEePlanError(null);
                }}
                className="font-mono rounded outline-none"
                style={{ fontSize: "11px", padding: "5px 7px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }}
              />
            </div>
          </div>

          {(!acquisitionWindowValid || !cloudPercentValid) && (
            <div
              className="rounded px-2 py-1.5"
              style={{ fontSize: "11px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}
            >
              Acquisition dates must be ordered and cloud max must be 0 to 100.
            </div>
          )}

          {eePlanError && (
            <div
              className="rounded px-2 py-1.5"
              style={{ fontSize: "11px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}
            >
              {eePlanError}
            </div>
          )}

          {eePlan && (
            <div className="grid grid-cols-2 gap-2">
              <PreviewMetric label="Status" value={formatStatus(eePlan.executionStatus)} />
              <PreviewMetric label="Dry run" value={eePlan.dryRun ? "yes" : "no"} />
              <PreviewMetric label="Auth" value={formatStatus(eePlan.authReadiness.status)} />
              <PreviewMetric label="Providers" value={eePlan.plannedProviderFamilies.join(", ")} wide />
              {eePlan.warnings.length > 0 && (
                <div className="col-span-2" style={{ fontSize: "10px", color: "var(--gs-slate)" }}>
                  {eePlan.warnings[0]}
                </div>
              )}
            </div>
          )}
        </div>

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

function PreviewMetric({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={wide ? "col-span-2" : ""}>
      <div className="font-mono" style={{ fontSize: "9px", color: "var(--gs-slate)", textTransform: "uppercase" }}>
        {label}
      </div>
      <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)", wordBreak: "break-word" }}>
        {value}
      </div>
    </div>
  );
}

function hasTileTemplatePlaceholders(template: string): boolean {
  return template.includes("{z}") && template.includes("{x}") && template.includes("{y}");
}

function buildTilePreviewGrid(template: string, latitude: number, longitude: number, zoom: number) {
  const centerTile = latLonToTile(latitude, longitude, zoom);
  const tiles = [-1, 0, 1].flatMap((yOffset) =>
    [-1, 0, 1].map((xOffset) => {
      const x = centerTile.x + xOffset;
      const y = centerTile.y + yOffset;
      return {
        key: `${zoom}-${x}-${y}`,
        x,
        y,
        isCenter: xOffset === 0 && yOffset === 0,
        url: template
          .replaceAll("{z}", String(zoom))
          .replaceAll("{x}", String(x))
          .replaceAll("{y}", String(y)),
      };
    }),
  );
  return {
    providerLabel: tileTemplateLabel(template),
    zoom,
    centerTile,
    tiles,
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

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function defaultAcquisitionEnd(): string {
  return new Date().toISOString().slice(0, 10);
}

function defaultAcquisitionStart(): string {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() - 30);
  return date.toISOString().slice(0, 10);
}

function formatStatus(value: string): string {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");
}

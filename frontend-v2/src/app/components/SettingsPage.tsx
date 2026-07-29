interface SettingsPageProps {
  externalTilesEnabled: boolean;
  tileUrlTemplate: string;
  showAdvancedUnavailableOutputs: boolean;
  operatorPrivateOverlayEnabled?: boolean;
  pollingIntervalSeconds: number;
  onToggleExternalTiles: (enabled: boolean) => void;
  onTileUrlTemplateChange: (value: string) => void;
  onToggleAdvancedUnavailableOutputs: (enabled: boolean) => void;
  onToggleOperatorPrivateOverlay?: (enabled: boolean) => void;
}

export function SettingsPage({
  externalTilesEnabled,
  tileUrlTemplate,
  showAdvancedUnavailableOutputs,
  operatorPrivateOverlayEnabled = false,
  pollingIntervalSeconds,
  onToggleExternalTiles,
  onTileUrlTemplateChange,
  onToggleAdvancedUnavailableOutputs,
  onToggleOperatorPrivateOverlay,
}: SettingsPageProps) {
  return (
    <div style={{ maxWidth: "720px", margin: "0 auto" }}>
      <div className="mb-4">
        <h2 className="font-mono" style={{ fontSize: "14px", fontWeight: 700, color: "var(--gs-navy)" }}>
          Settings
        </h2>
        <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>
          Local operator configuration stored in this browser only.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <section
          className="rounded-lg bg-card overflow-hidden"
          style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
        >
          <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
            <span
              className="font-mono"
              style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              External map tiles
            </span>
          </div>

          <div className="px-4 py-3 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--gs-navy)" }}>
                  External map tiles
                </div>
                <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px" }}>
                  Disabled by default. Keep this off unless you explicitly want browser tile requests to leave the local app.
                </div>
              </div>
              <label className="flex items-center gap-2" style={{ cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={externalTilesEnabled}
                  onChange={(event) => onToggleExternalTiles(event.target.checked)}
                />
                <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)" }}>
                  {externalTilesEnabled ? "Enabled" : "Disabled"}
                </span>
              </label>
            </div>

            <div
              className="rounded px-3 py-2"
              style={{
                backgroundColor: externalTilesEnabled ? "var(--gs-amber-bg)" : "var(--accent)",
                border: externalTilesEnabled
                  ? "1px solid var(--gs-amber-border)"
                  : "1px solid rgba(28,43,94,0.12)",
              }}
            >
              <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>Privacy warning</div>
              <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px", lineHeight: "1.5" }}>
                If this URL points to an external provider, that provider may receive browser tile requests. Use a local tile server to avoid third-party requests.
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--gs-navy)" }}>
                Tile URL template
              </label>
              <input
                type="text"
                value={tileUrlTemplate}
                onChange={(event) => onTileUrlTemplateChange(event.target.value)}
                disabled={!externalTilesEnabled}
                placeholder="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                className="font-mono rounded outline-none"
                style={{
                  fontSize: "11.5px",
                  padding: "7px 10px",
                  backgroundColor: "var(--input-background)",
                  border: "1px solid var(--border)",
                  color: externalTilesEnabled ? "var(--gs-navy)" : "var(--gs-slate)",
                  opacity: externalTilesEnabled ? 1 : 0.7,
                }}
              />
              <div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                {externalTilesEnabled
                  ? "Stored locally and used by the target map preview only when external tiles are enabled."
                  : "External tiles disabled. No external tile URL is requested."}
              </div>
            </div>
          </div>
        </section>

        <section
          className="rounded-lg bg-card overflow-hidden"
          style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
        >
          <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
            <span
              className="font-mono"
              style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              Operator private tools
            </span>
          </div>
          <div className="px-4 py-3 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--gs-navy)" }}>
                  Operator-only private tools
                </div>
                <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px", lineHeight: "1.5" }}>
                  Shows coordinate-free private previews and the reviewed local-depth calibration panel. Both backend capabilities remain separately gated and disabled by default. Local depth also requires measured anchor polygons and explicit operator review.
                </div>
              </div>
              <label className="flex items-center gap-2" style={{ cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={operatorPrivateOverlayEnabled}
                  onChange={(event) => onToggleOperatorPrivateOverlay?.(event.target.checked)}
                />
                <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)" }}>
                  {operatorPrivateOverlayEnabled ? "Shown" : "Hidden"}
                </span>
              </label>
            </div>
            <div
              className="rounded px-3 py-2"
              style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}
            >
              <div style={{ fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
                The browser does not create operator identity, role, or run-authorization headers. A trusted upstream layer must provide them in network deployments. Local development remains loopback-only. Private overlay must show coordinate-free summaries only; verify existing UI safety tests before changing this panel. No public downloads, public overlay layer, private geometry, KMZ contents, raw payloads, coordinates, or filesystem paths are shown. Private geometry is never returned in the local-depth response.
              </div>
            </div>
          </div>
        </section>

        <section
          className="rounded-lg bg-card overflow-hidden"
          style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
        >
          <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
            <span
              className="font-mono"
              style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              Run monitoring
            </span>
          </div>
          <div className="px-4 py-3 flex flex-col gap-3">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--gs-navy)" }}>Status polling interval</div>
                <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px" }}>
                  Matches the legacy UI parity contract for active runs.
                </div>
              </div>
              <span className="font-mono" style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-slate)" }}>
                {pollingIntervalSeconds}s read-only
              </span>
            </div>
          </div>
        </section>

        <section
          className="rounded-lg bg-card overflow-hidden"
          style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
        >
          <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
            <span
              className="font-mono"
              style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              Exports browser
            </span>
          </div>
          <div className="px-4 py-3 flex items-start justify-between gap-4">
            <div>
              <div style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--gs-navy)" }}>
                Show advanced / unavailable outputs
              </div>
              <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px" }}>
                Controls whether the guarded Exports view opens its secondary unavailable section by default.
              </div>
            </div>
            <label className="flex items-center gap-2" style={{ cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={showAdvancedUnavailableOutputs}
                onChange={(event) => onToggleAdvancedUnavailableOutputs(event.target.checked)}
              />
              <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)" }}>
                {showAdvancedUnavailableOutputs ? "Shown" : "Collapsed"}
              </span>
            </label>
          </div>
        </section>
      </div>
    </div>
  );
}

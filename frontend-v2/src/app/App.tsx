import { useState } from "react";
import { NavBar } from "./components/NavBar";
import { StatusStrip } from "./components/StatusStrip";
import { RunWorkflowCard } from "./components/RunWorkflowCard";
import { ActivityCard } from "./components/ActivityCard";
import { OverviewTab } from "./components/OverviewTab";
import { ExportsTab } from "./components/ExportsTab";
import { StatusHistoryTab } from "./components/StatusHistoryTab";
import { DiagnosticsTab } from "./components/DiagnosticsTab";
import { RunArchivePage } from "./components/RunArchivePage";
import { COMPLETED_RUN, RUN_ID } from "./data/mockData";
import type { Run, RunState } from "./data/mockData";
import { Plus } from "lucide-react";

type NavTab = "dashboard" | "archive" | "exports" | "settings";
type RunTab = "overview" | "exports" | "status-history" | "diagnostics";
type DemoMode = "empty" | "completed" | "running" | "failed";

const RUN_TABS: { key: RunTab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "exports", label: "Exports" },
  { key: "status-history", label: "Status History" },
  { key: "diagnostics", label: "Diagnostics" },
];

const DEMO_RUN_DATA: Record<DemoMode, (Run & { runState: RunState }) | null> = {
  empty: null,
  completed: { ...COMPLETED_RUN, runState: "done" },
  running: {
    id: "f0g17i55-6h8d-72i9-2f0j-44456h7g8e9i",
    name: "hypercube-test",
    state: "running",
    stage: "FOCUS",
    updated: "2026-05-31T15:10:00Z",
    created: "2026-05-31T14:00:00Z",
    runState: "running",
  },
  failed: {
    id: "c7d84f22-3e5a-49f6-9c7g-11123e4d5b6f",
    name: "new1",
    state: "failed",
    stage: "SAR",
    updated: "2026-05-29T16:48:20Z",
    created: "2026-05-29T15:00:00Z",
    runState: "failed",
  },
};

function RunStateBadge({ state }: { state: RunState }) {
  const map: Record<RunState, { dot: string; label: string }> = {
    done: { dot: "var(--gs-green)", label: "Done" },
    running: { dot: "var(--gs-blue)", label: "Running" },
    failed: { dot: "var(--gs-red)", label: "Failed" },
    queued: { dot: "var(--gs-amber)", label: "Queued" },
  };
  const cfg = map[state];
  return (
    <span className="flex items-center gap-1.5">
      <span
        className="rounded-full inline-block"
        style={{ width: "7px", height: "7px", backgroundColor: cfg.dot, flexShrink: 0 }}
      />
      <span style={{ fontSize: "12px", fontWeight: 600, color: cfg.dot }}>{cfg.label}</span>
    </span>
  );
}

export default function App() {
  const [activeNav, setActiveNav] = useState<NavTab>("dashboard");
  const [activeRunTab, setActiveRunTab] = useState<RunTab>("overview");
  const [demoMode, setDemoMode] = useState<DemoMode>("completed");

  const currentRunData = DEMO_RUN_DATA[demoMode];
  const hasSelectedRun = currentRunData !== null;

  function handleDemoChange(mode: DemoMode) {
    setDemoMode(mode);
    setActiveRunTab("overview");
    if (mode !== "empty") setActiveNav("dashboard");
  }

  function handleSelectRun(run: Run) {
    const mode: DemoMode =
      run.state === "done" ? "completed" :
      run.state === "running" ? "running" :
      run.state === "failed" ? "failed" : "completed";
    setDemoMode(mode);
    setActiveNav("dashboard");
    setActiveRunTab("overview");
  }

  const runId = currentRunData?.id ?? RUN_ID;
  const runState: RunState = currentRunData?.state ?? "done";
  const runStage = currentRunData?.stage ?? "Completed";

  return (
    <div
      className="flex flex-col"
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--background)",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      <NavBar
        activeTab={activeNav}
        onTabChange={(t) => setActiveNav(t as NavTab)}
        demoMode={demoMode}
        onDemoChange={handleDemoChange}
      />
      <StatusStrip runId={runId} state={runState} stage={runStage} />

      <main className="flex-1 px-5 py-4">

        {/* ─── DASHBOARD ─── */}
        {activeNav === "dashboard" && (
          <>
            {/* Empty state */}
            {!hasSelectedRun && (
              <div
                className="grid gap-4"
                style={{
                  gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)",
                  maxWidth: "1140px",
                  margin: "0 auto",
                }}
              >
                <RunWorkflowCard />
                <ActivityCard runState="done" hasRun={false} />
              </div>
            )}

            {/* Selected run: tabbed view */}
            {hasSelectedRun && (
              <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
                {/* Run header bar */}
                <div
                  className="flex items-center justify-between mb-3 pb-3"
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <h2
                          className="font-mono"
                          style={{ fontSize: "14px", fontWeight: 700, color: "var(--gs-navy)", letterSpacing: "-0.01em" }}
                        >
                          {currentRunData.name}
                        </h2>
                        <RunStateBadge state={currentRunData.state} />
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span
                          className="font-mono"
                          style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.55 }}
                        >
                          {currentRunData.id}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Run switcher */}
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>Switch run:</span>
                    <div className="flex items-center gap-1">
                      {(["completed", "running", "failed"] as const).map((mode) => {
                        const labels = { completed: "validation-run", running: "hypercube-test", failed: "new1" };
                        const colors = { completed: "var(--gs-green)", running: "var(--gs-blue)", failed: "var(--gs-red)" };
                        const active = demoMode === mode;
                        return (
                          <button
                            key={mode}
                            onClick={() => handleDemoChange(mode)}
                            className="px-2.5 py-1 rounded transition-all"
                            style={{
                              fontSize: "11.5px",
                              fontWeight: active ? 600 : 400,
                              color: active ? colors[mode] : "var(--gs-slate)",
                              backgroundColor: active ? "var(--card)" : "transparent",
                              border: active ? `1px solid rgba(28,43,94,0.15)` : "1px solid transparent",
                              cursor: "pointer",
                            }}
                          >
                            {labels[mode]}
                          </button>
                        );
                      })}
                    </div>
                    <button
                      onClick={() => handleDemoChange("empty")}
                      className="flex items-center gap-1 px-2.5 py-1 rounded ml-1"
                      style={{
                        fontSize: "11px",
                        color: "var(--gs-navy)",
                        backgroundColor: "var(--accent)",
                        border: "1px solid rgba(28,43,94,0.15)",
                        cursor: "pointer",
                      }}
                    >
                      <Plus size={11} />
                      New run
                    </button>
                  </div>
                </div>

                {/* Run sub-tabs */}
                <div
                  className="flex items-stretch mb-4"
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  {RUN_TABS.map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveRunTab(tab.key)}
                      className="px-4 py-1.5 transition-all"
                      style={{
                        fontSize: "12.5px",
                        fontWeight: activeRunTab === tab.key ? 600 : 400,
                        color: activeRunTab === tab.key ? "var(--gs-navy)" : "var(--gs-slate)",
                        background: "none",
                        border: "none",
                        borderBottom:
                          activeRunTab === tab.key
                            ? "2px solid var(--gs-navy)"
                            : "2px solid transparent",
                        cursor: "pointer",
                        marginBottom: "-1px",
                      }}
                    >
                      {tab.label}
                      {tab.key === "status-history" && currentRunData.state === "failed" && (
                        <span
                          className="ml-1.5 font-mono"
                          style={{
                            fontSize: "9px",
                            fontWeight: 700,
                            color: "white",
                            backgroundColor: "var(--gs-red)",
                            padding: "1px 4px",
                            borderRadius: "3px",
                          }}
                        >
                          ERR
                        </span>
                      )}
                      {tab.key === "status-history" && currentRunData.state === "running" && (
                        <span
                          className="ml-1.5 font-mono"
                          style={{
                            fontSize: "9px",
                            fontWeight: 700,
                            color: "white",
                            backgroundColor: "var(--gs-blue)",
                            padding: "1px 4px",
                            borderRadius: "3px",
                          }}
                        >
                          LIVE
                        </span>
                      )}
                    </button>
                  ))}
                </div>

                {/* Tab content */}
                {activeRunTab === "overview" && (
                  <OverviewTab onSelectRun={handleSelectRun} runState={currentRunData.runState} />
                )}
                {activeRunTab === "exports" && <ExportsTab />}
                {activeRunTab === "status-history" && (
                  <StatusHistoryTab runState={currentRunData.runState} />
                )}
                {activeRunTab === "diagnostics" && <DiagnosticsTab />}
              </div>
            )}
          </>
        )}

        {/* ─── RUN ARCHIVE ─── */}
        {activeNav === "archive" && (
          <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
            <RunArchivePage onSelectRun={handleSelectRun} />
          </div>
        )}

        {/* ─── EXPORTS ─── */}
        {activeNav === "exports" && (
          <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
            <div className="flex items-end justify-between mb-3">
              <div>
                <h2
                  className="font-mono"
                  style={{ fontSize: "14px", fontWeight: 700, color: "var(--gs-navy)" }}
                >
                  Exports
                </h2>
                <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>
                  All safe deliverables · <span className="font-mono">validation-run</span> · 421 files
                </p>
              </div>
              <button
                onClick={() => { setActiveNav("dashboard"); setDemoMode("completed"); setActiveRunTab("exports"); }}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded"
                style={{
                  fontSize: "11.5px",
                  fontWeight: 500,
                  color: "var(--gs-navy)",
                  backgroundColor: "var(--card)",
                  border: "1px solid rgba(28,43,94,0.18)",
                  cursor: "pointer",
                }}
              >
                Open in run view
              </button>
            </div>
            <ExportsTab />
          </div>
        )}

        {/* ─── SETTINGS ─── */}
        {activeNav === "settings" && (
          <div style={{ maxWidth: "640px", margin: "0 auto" }}>
            <div className="mb-4">
              <h2
                className="font-mono"
                style={{ fontSize: "14px", fontWeight: 700, color: "var(--gs-navy)" }}
              >
                Settings
              </h2>
              <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>
                Local operator configuration
              </p>
            </div>
            <div
              className="rounded-lg bg-card overflow-hidden"
              style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
            >
              {[
                { label: "External tile sources", value: "Disabled", note: "Map tiles are fetched from local cache only. No external requests are made." },
                { label: "Access mode", value: "Local", note: "Local-only operator app. No sign-in surface is exposed in this mock phase." },
                { label: "Grid resolution default", value: "640 m", note: "Default grid resolution for new screening runs." },
                { label: "SAR xfail policy", value: "Accept residual", note: "RADAR_STACK inherited SAR dB residuals are accepted by default." },
                { label: "App version", value: "GEE Screening v2.4.1", note: "" },
              ].map((item, i, arr) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between px-4 py-3"
                  style={{ borderBottom: i < arr.length - 1 ? "1px solid var(--border)" : "none" }}
                >
                  <div>
                    <div style={{ fontSize: "12.5px", fontWeight: 500, color: "var(--gs-navy)" }}>
                      {item.label}
                    </div>
                    {item.note && (
                      <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px" }}>
                        {item.note}
                      </div>
                    )}
                  </div>
                  <span
                    className="font-mono"
                    style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-slate)" }}
                  >
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

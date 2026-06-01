import { useEffect, useRef, useState } from "react";
import { Plus } from "lucide-react";
import {
  buildActivityEvents,
  createRun,
  deleteRun,
  getOperatorOutputs,
  getRunDetail,
  listRuns,
  type CreateRunInput,
  type DeleteRunResult,
  type OperatorOutputTree,
  type Run,
  type RunDetail,
  type RunState,
} from "./api/client";
import { NavBar } from "./components/NavBar";
import { StatusStrip } from "./components/StatusStrip";
import { RunWorkflowCard } from "./components/RunWorkflowCard";
import { ActivityCard } from "./components/ActivityCard";
import { OverviewTab } from "./components/OverviewTab";
import { ExportsTab } from "./components/ExportsTab";
import { StatusHistoryTab } from "./components/StatusHistoryTab";
import { DiagnosticsTab } from "./components/DiagnosticsTab";
import { RunArchivePage } from "./components/RunArchivePage";
import { SettingsPage } from "./components/SettingsPage";

type NavTab = "dashboard" | "archive" | "exports" | "settings";
type RunTab = "overview" | "exports" | "status-history" | "diagnostics";

const RUN_TABS: { key: RunTab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "exports", label: "Exports" },
  { key: "status-history", label: "Status History" },
  { key: "diagnostics", label: "Diagnostics" },
];

const EMPTY_OUTPUT_TREE: OperatorOutputTree = {
  runId: "",
  outputs: [],
  groups: [],
  keyDownloads: [],
  unavailable: [],
};

const UI_SETTINGS_STORAGE_KEY = "gs_operator_ui_settings_v1";
const DEFAULT_TILE_URL_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const RUN_POLLING_INTERVAL_SECONDS = 2;

interface UiSettings {
  externalTilesEnabled: boolean;
  tileUrlTemplate: string;
  showAdvancedUnavailableOutputs: boolean;
}

function loadUiSettings(): UiSettings {
  if (typeof window === "undefined") {
    return defaultUiSettings();
  }
  try {
    const raw = window.localStorage.getItem(UI_SETTINGS_STORAGE_KEY);
    if (!raw) {
      return defaultUiSettings();
    }
    const parsed = JSON.parse(raw) as Partial<UiSettings>;
    return {
      externalTilesEnabled: parsed.externalTilesEnabled === true,
      tileUrlTemplate:
        typeof parsed.tileUrlTemplate === "string" && parsed.tileUrlTemplate.trim().length > 0
          ? parsed.tileUrlTemplate
          : DEFAULT_TILE_URL_TEMPLATE,
      showAdvancedUnavailableOutputs: parsed.showAdvancedUnavailableOutputs === true,
    };
  } catch (_error) {
    return defaultUiSettings();
  }
}

function defaultUiSettings(): UiSettings {
  return {
    externalTilesEnabled: false,
    tileUrlTemplate: DEFAULT_TILE_URL_TEMPLATE,
    showAdvancedUnavailableOutputs: false,
  };
}

function RunStateBadge({ state }: { state: RunState }) {
  const map: Record<RunState, { dot: string; label: string }> = {
    done: { dot: "var(--gs-green)", label: "Done" },
    running: { dot: "var(--gs-blue)", label: "Running" },
    failed: { dot: "var(--gs-red)", label: "Failed" },
    queued: { dot: "var(--gs-amber)", label: "Queued" },
    cancelled: { dot: "var(--gs-slate)", label: "Cancelled" },
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
  const pollTimerRef = useRef<number | null>(null);
  const activePollRunIdRef = useRef<string | null>(null);
  const pollFailureCountRef = useRef(0);
  const [activeNav, setActiveNav] = useState<NavTab>("dashboard");
  const [activeRunTab, setActiveRunTab] = useState<RunTab>("overview");
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null);
  const [outputTree, setOutputTree] = useState<OperatorOutputTree>(EMPTY_OUTPUT_TREE);
  const [runsLoading, setRunsLoading] = useState(true);
  const [runLoading, setRunLoading] = useState(false);
  const [outputsLoading, setOutputsLoading] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [outputsError, setOutputsError] = useState<string | null>(null);
  const [queueFeedback, setQueueFeedback] = useState<string | null>(null);
  const [queueing, setQueueing] = useState(false);
  const [pollingPaused, setPollingPaused] = useState(false);
  const [uiSettings, setUiSettings] = useState<UiSettings>(() => loadUiSettings());

  useEffect(() => {
    void refreshRuns();
  }, []);

  useEffect(() => {
    window.localStorage.setItem(UI_SETTINGS_STORAGE_KEY, JSON.stringify(uiSettings));
  }, [uiSettings]);

  useEffect(() => {
    return () => {
      clearRunPollTimer();
    };
  }, []);

  useEffect(() => {
    clearRunPollTimer();
    pollFailureCountRef.current = 0;
    setPollingPaused(false);

    if (!selectedRun || !shouldPollRun(selectedRun.state)) {
      activePollRunIdRef.current = null;
      return;
    }

    activePollRunIdRef.current = selectedRun.id;

    const scheduleNextPoll = () => {
      clearRunPollTimer();
      pollTimerRef.current = window.setTimeout(() => {
        void pollSelectedRun(selectedRun.id);
      }, 2000);
    };

    scheduleNextPoll();
    return () => {
      clearRunPollTimer();
    };
  }, [selectedRun?.id, selectedRun?.state]);

  async function refreshRuns(selectFirst = true) {
    setRunsLoading(true);
    setRunsError(null);
    try {
      const loadedRuns = await listRuns();
      setRuns(loadedRuns);
      if (selectFirst && loadedRuns.length > 0 && !selectedRun) {
        await loadRun(loadedRuns[0].id);
      }
    } catch (error) {
      setRuns([]);
      setRunsError(error instanceof Error ? error.message : "Recent runs are temporarily unavailable.");
    } finally {
      setRunsLoading(false);
    }
  }

  async function loadRun(runId: string) {
    setRunLoading(true);
    setRunError(null);
    setOutputsError(null);
    setPollingPaused(false);
    pollFailureCountRef.current = 0;
    try {
      const detail = await getRunDetail(runId);
      syncRunSummary(detail);
      setSelectedRun(detail);
      setActiveNav("dashboard");
      setActiveRunTab("overview");
      if (detail.state === "done") {
        await loadOutputs(detail.id);
      } else {
        setOutputTree(EMPTY_OUTPUT_TREE);
      }
    } catch (error) {
      setSelectedRun(null);
      setOutputTree(EMPTY_OUTPUT_TREE);
      setRunError(error instanceof Error ? error.message : "Run detail is temporarily unavailable.");
    } finally {
      setRunLoading(false);
    }
  }

  async function loadOutputs(runId: string) {
    setOutputsLoading(true);
    setOutputsError(null);
    try {
      setOutputTree(await getOperatorOutputs(runId));
    } catch (error) {
      setOutputTree(EMPTY_OUTPUT_TREE);
      setOutputsError(error instanceof Error ? error.message : "Exports are temporarily unavailable.");
    } finally {
      setOutputsLoading(false);
    }
  }

  async function handleSelectRun(run: Run) {
    await loadRun(run.id);
  }

  async function handleQueueRun(input: CreateRunInput) {
    setQueueing(true);
    setQueueFeedback("Queueing local run...");
    try {
      const queuedRun = await createRun(input);
      setQueueFeedback(`Run queued: ${queuedRun.id}`);
      await refreshRuns(false);
      await loadRun(queuedRun.id);
    } catch (error) {
      setQueueFeedback(error instanceof Error ? error.message : "Run request failed.");
    } finally {
      setQueueing(false);
    }
  }

  async function handleDeleteRun(run: Run): Promise<DeleteRunResult> {
    const result = await deleteRun(run.id);
    setRuns((currentRuns) => currentRuns.filter((item) => item.id !== run.id));
    if (selectedRun?.id === run.id) {
      clearRunPollTimer();
      activePollRunIdRef.current = null;
      setSelectedRun(null);
      setOutputTree(EMPTY_OUTPUT_TREE);
      setActiveRunTab("overview");
    }
    return result;
  }

  const runId = selectedRun?.id ?? "Not started";
  const runState: RunState = selectedRun?.state ?? "queued";
  const runStage = selectedRun?.stage ?? "Queued";

  function clearRunPollTimer() {
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }

  function shouldPollRun(state: RunState) {
    return state === "queued" || state === "running";
  }

  function syncRunSummary(detail: RunDetail) {
    setRuns((currentRuns) => {
      let matched = false;
      const nextRuns = currentRuns.map((run) => {
        if (run.id !== detail.id) {
          return run;
        }
        matched = true;
        return {
          ...run,
          name: detail.name,
          state: detail.state,
          stage: detail.stage,
          updated: detail.updated,
          created: detail.created,
        };
      });
      return matched ? nextRuns : currentRuns;
    });
  }

  async function pollSelectedRun(runId: string) {
    if (activePollRunIdRef.current !== runId) {
      return;
    }

    try {
      const detail = await getRunDetail(runId);
      if (activePollRunIdRef.current !== runId) {
        return;
      }

      pollFailureCountRef.current = 0;
      setPollingPaused(false);
      syncRunSummary(detail);
      setSelectedRun((currentRun) => (currentRun && currentRun.id === runId ? detail : currentRun));

      if (detail.state === "done") {
        await loadOutputs(detail.id);
        return;
      }

      if (shouldPollRun(detail.state)) {
        clearRunPollTimer();
        pollTimerRef.current = window.setTimeout(() => {
          void pollSelectedRun(runId);
        }, 2000);
      }
    } catch (error) {
      console.error("Selected run polling failed.", error);
      if (activePollRunIdRef.current !== runId) {
        return;
      }

      pollFailureCountRef.current += 1;
      if (pollFailureCountRef.current >= 5) {
        clearRunPollTimer();
        setPollingPaused(true);
        return;
      }

      pollTimerRef.current = window.setTimeout(() => {
        void pollSelectedRun(runId);
      }, 2000);
    }
  }

  async function handleManualRefresh() {
    if (!selectedRun) {
      return;
    }
    setPollingPaused(false);
    pollFailureCountRef.current = 0;
    await loadRun(selectedRun.id);
  }

  return (
    <div
      className="flex flex-col"
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--background)",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      <NavBar activeTab={activeNav} onTabChange={(t) => setActiveNav(t as NavTab)} />
      <StatusStrip runId={runId} state={runState} stage={runStage} />

      <main className="flex-1 px-5 py-4">
        {activeNav === "dashboard" && (
          <>
            {!selectedRun && (
              <div
                className="grid gap-4"
                style={{
                  gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)",
                  maxWidth: "1140px",
                  margin: "0 auto",
                }}
              >
                <RunWorkflowCard
                  onQueueRun={handleQueueRun}
                  isQueueing={queueing}
                  feedback={queueFeedback}
                  externalTilesEnabled={uiSettings.externalTilesEnabled}
                  tileUrlTemplate={uiSettings.tileUrlTemplate}
                />
                <ActivityCard hasRun={false} />
              </div>
            )}

            {selectedRun && (
              <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
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
                          {selectedRun.name}
                        </h2>
                        <RunStateBadge state={selectedRun.state} />
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className="font-mono" style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.55 }}>
                          {selectedRun.id}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {runLoading && <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>Loading run...</span>}
                    {pollingPaused && (
                      <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>Status updates paused</span>
                    )}
                    {selectedRun && (
                      <button
                        onClick={() => { void handleManualRefresh(); }}
                        className="px-2.5 py-1 rounded"
                        style={{
                          fontSize: "11px",
                          color: "var(--gs-navy)",
                          backgroundColor: "transparent",
                          border: "1px solid rgba(28,43,94,0.15)",
                          cursor: "pointer",
                        }}
                      >
                        Refresh
                      </button>
                    )}
                    <button
                      onClick={() => { setSelectedRun(null); setOutputTree(EMPTY_OUTPUT_TREE); setActiveRunTab("overview"); }}
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

                {runError && (
                  <div className="mb-3 rounded px-3 py-2" style={{ fontSize: "12px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}>
                    {runError}
                  </div>
                )}

                <div className="flex items-stretch mb-4" style={{ borderBottom: "1px solid var(--border)" }}>
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
                        borderBottom: activeRunTab === tab.key ? "2px solid var(--gs-navy)" : "2px solid transparent",
                        cursor: "pointer",
                        marginBottom: "-1px",
                      }}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {activeRunTab === "overview" && (
                  <OverviewTab
                    selectedRun={selectedRun}
                    recentRuns={runs}
                    keyDownloads={outputTree.keyDownloads}
                    loadingOutputs={outputsLoading}
                    onSelectRun={handleSelectRun}
                  />
                )}
                {activeRunTab === "exports" && (
                  <ExportsTab
                    groups={outputTree.groups}
                    unavailable={outputTree.unavailable}
                    loading={outputsLoading}
                    error={outputsError}
                    showAdvancedByDefault={uiSettings.showAdvancedUnavailableOutputs}
                  />
                )}
                {activeRunTab === "status-history" && <StatusHistoryTab run={selectedRun} />}
                {activeRunTab === "diagnostics" && (
                  <DiagnosticsTab outputTree={outputTree} artifacts={selectedRun.artifacts} />
                )}
              </div>
            )}
          </>
        )}

        {activeNav === "archive" && (
          <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
            <RunArchivePage
              runs={runs}
              loading={runsLoading}
              error={runsError}
              onSelectRun={handleSelectRun}
              onDeleteRun={handleDeleteRun}
            />
          </div>
        )}

        {activeNav === "exports" && (
          <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
            <div className="flex items-end justify-between mb-3">
              <div>
                <h2 className="font-mono" style={{ fontSize: "14px", fontWeight: 700, color: "var(--gs-navy)" }}>
                  Exports
                </h2>
                <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>
                  Guarded deliverables returned by the run output API.
                </p>
              </div>
            </div>
            <ExportsTab
              groups={outputTree.groups}
              unavailable={outputTree.unavailable}
              loading={outputsLoading}
              error={outputsError}
              showAdvancedByDefault={uiSettings.showAdvancedUnavailableOutputs}
            />
          </div>
        )}

        {activeNav === "settings" && (
          <SettingsPage
            externalTilesEnabled={uiSettings.externalTilesEnabled}
            tileUrlTemplate={uiSettings.tileUrlTemplate}
            showAdvancedUnavailableOutputs={uiSettings.showAdvancedUnavailableOutputs}
            pollingIntervalSeconds={RUN_POLLING_INTERVAL_SECONDS}
            onToggleExternalTiles={(externalTilesEnabled) =>
              setUiSettings((current) => ({ ...current, externalTilesEnabled }))
            }
            onTileUrlTemplateChange={(tileUrlTemplate) =>
              setUiSettings((current) => ({ ...current, tileUrlTemplate }))
            }
            onToggleAdvancedUnavailableOutputs={(showAdvancedUnavailableOutputs) =>
              setUiSettings((current) => ({ ...current, showAdvancedUnavailableOutputs }))
            }
          />
        )}
      </main>
    </div>
  );
}

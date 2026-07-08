import { useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Clock,
  Loader2,
  XCircle,
} from "lucide-react";
import { StageStatusPills } from "./StageStatusPills";
import { KeyDownloads } from "./KeyDownloads";
import { formatFileSize, type KeyDownload, type Run, type RunDetail } from "../api/client";

function fmtDate(iso: string) {
  const d = new Date(iso);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" }) +
    " · " +
    d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })
  );
}

function fmtRunSize(run: Run) {
  return run.diskUsageBytes === null ? "Unknown size" : formatFileSize(run.diskUsageBytes);
}

function StateBadge({ state }: { state: Run["state"] }) {
  const map = {
    done: { label: "Done", color: "var(--gs-green)", bg: "var(--gs-green-bg)", border: "var(--gs-green-border)" },
    running: { label: "Running", color: "var(--gs-blue)", bg: "var(--gs-blue-bg)", border: "var(--gs-blue-border)" },
    failed: { label: "Failed", color: "var(--gs-red)", bg: "var(--gs-red-bg)", border: "var(--gs-red-border)" },
    stale_failed: { label: "Stale failed", color: "var(--gs-red)", bg: "var(--gs-red-bg)", border: "var(--gs-red-border)" },
    queued: { label: "Queued", color: "var(--gs-amber)", bg: "var(--gs-amber-bg)", border: "var(--gs-amber-border)" },
    cancelled: { label: "Cancelled", color: "var(--gs-slate)", bg: "rgba(100,116,139,0.06)", border: "rgba(100,116,139,0.15)" },
  };
  const cfg = map[state];
  return (
    <span
      className="font-mono"
      style={{
        fontSize: "10px",
        fontWeight: 600,
        color: cfg.color,
        backgroundColor: cfg.bg,
        border: `1px solid ${cfg.border}`,
        padding: "1px 6px",
        borderRadius: "3px",
        whiteSpace: "nowrap",
      }}
    >
      {cfg.label}
    </span>
  );
}

function lastRecordedEvent(run: RunDetail): string {
  const lastEvent = run.history.length > 0 ? run.history[run.history.length - 1] : null;
  return lastEvent ? `${lastEvent.stage}: ${lastEvent.message}` : "No status history event was recorded.";
}

function backendFailureDetail(run: RunDetail): string | null {
  if (run.detail) {
    return run.detail;
  }
  const terminalEvent = run.history
    .slice()
    .reverse()
    .find((event) => event.state === "failed" || event.state === "stale_failed");
  return terminalEvent?.message ?? null;
}

function FailureNotice({ run }: { run: RunDetail }) {
  if (run.state === "stale_failed") {
    const terminalDetail = backendFailureDetail(run);
    return (
      <div
        className="rounded px-3 py-2 mt-2"
        style={{ backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}
      >
        <p style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-red)" }}>Run is stale_failed.</p>
        <p style={{ fontSize: "11.5px", color: "var(--gs-red)", marginTop: "2px" }}>
          Last known stage: {run.stage}
        </p>
        <p style={{ fontSize: "11.5px", color: "var(--gs-red)", marginTop: "2px" }}>
          Last recorded event: {lastRecordedEvent(run)}
        </p>
        <p style={{ fontSize: "11.5px", color: "var(--gs-red)", marginTop: "2px" }}>
          {terminalDetail ?? "No terminal failure message was recorded."}
        </p>
      </div>
    );
  }

  if (run.state === "failed") {
    return (
      <div
        className="rounded px-3 py-2 mt-2"
        style={{ backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}
      >
        <p style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-red)" }}>
          {backendFailureDetail(run) ?? "Run failed. No failure detail was recorded."}
        </p>
      </div>
    );
  }

  return null;
}

interface OverviewTabProps {
  onSelectRun?: (run: Run) => void;
  selectedRun: RunDetail;
  recentRuns: Run[];
  keyDownloads: KeyDownload[];
  loadingOutputs?: boolean;
}

export function OverviewTab({ onSelectRun, selectedRun, recentRuns, keyDownloads, loadingOutputs = false }: OverviewTabProps) {
  const [showArchive, setShowArchive] = useState(false);
  const [archiveSearch, setArchiveSearch] = useState("");

  const filteredArchive = recentRuns.filter(
    (r) =>
      r.name.toLowerCase().includes(archiveSearch.toLowerCase()) ||
      r.id.toLowerCase().includes(archiveSearch.toLowerCase())
  );

  const lifecycleSummary =
    selectedRun.state === "done"
      ? { icon: <CheckCircle2 size={13} />, color: "var(--gs-green)", label: "Complete", detail: `${selectedRun.stages.filter((s) => s.status === "done").length} stages complete` }
      : selectedRun.state === "running"
      ? { icon: <Loader2 size={13} className="animate-spin" />, color: "var(--gs-blue)", label: "Running", detail: `${selectedRun.stage} in progress` }
      : selectedRun.state === "failed"
      ? { icon: <XCircle size={13} />, color: "var(--gs-red)", label: "Failed", detail: selectedRun.stage }
      : selectedRun.state === "stale_failed"
      ? { icon: <XCircle size={13} />, color: "var(--gs-red)", label: "Stale failed", detail: `Last known stage: ${selectedRun.stage}` }
      : { icon: <Clock size={13} />, color: "var(--gs-amber)", label: "Queued", detail: "Waiting for first stage update" };

  return (
    <div className="flex flex-col gap-3">
      {/* Lifecycle summary + stage pills — full width */}
      <div
        className="rounded-lg bg-card px-4 py-3"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2">
            <span style={{ color: lifecycleSummary.color }}>{lifecycleSummary.icon}</span>
            <span
              className="font-mono"
              style={{ fontSize: "11.5px", fontWeight: 700, color: lifecycleSummary.color }}
            >
              {lifecycleSummary.label}
            </span>
            <span style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>{lifecycleSummary.detail}</span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-slate)", opacity: 0.65 }}>
              <Clock size={10} className="inline mr-1" />
              {fmtDate(selectedRun.updated)}
            </span>
          </div>
        </div>
        <StageStatusPills stages={selectedRun.stages} />
        <FailureNotice run={selectedRun} />
      </div>

      {/* Two-column: Key Downloads | Recent Runs */}
      <div className="grid gap-3" style={{ gridTemplateColumns: "1fr minmax(280px, 380px)" }}>
        {/* Left: Key Downloads */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span
              className="font-mono"
              style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              Private Local Outputs
            </span>
            <span
              className="font-mono"
              style={{
                fontSize: "9px",
                fontWeight: 700,
                color: "var(--gs-blue)",
                backgroundColor: "var(--gs-blue-bg)",
                border: "1px solid var(--gs-blue-border)",
                padding: "1px 5px",
                borderRadius: "3px",
                letterSpacing: "0.03em",
              }}
            >
              PRIVATE_LOCAL
            </span>
            <span style={{ fontSize: "10.5px", color: "var(--gs-slate)", opacity: 0.6 }}>
              pinned downloads
            </span>
          </div>
          <KeyDownloads downloads={keyDownloads} loading={loadingOutputs} />
        </div>

        {/* Right: Recent Runs + Archive */}
        <div
          className="rounded-lg bg-card overflow-hidden flex flex-col"
          style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
        >
          {/* Section: Recent Runs */}
          <div
            className="flex items-center justify-between px-3 py-2"
            style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
          >
            <span
              className="font-mono"
              style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              Recent Runs
            </span>
            <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>last 3</span>
          </div>

          <div className="flex flex-col">
            {recentRuns.slice(0, 3).map((run, i) => (
              <div
                key={run.id}
                className="flex items-center gap-2 px-3 py-2 hover:bg-accent/30 transition-colors"
                style={{ borderBottom: i < 2 ? "1px solid var(--border)" : "none" }}
              >
                <StateBadge state={run.state} />
                <div className="flex-1 min-w-0">
                  <div
                    className="font-mono truncate"
                    style={{ fontSize: "12px", fontWeight: 600, color: "var(--gs-navy)" }}
                  >
                    {run.name}
                  </div>
                  <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", opacity: 0.7 }}>
                    {fmtDate(run.updated)} · Disk used {fmtRunSize(run)}
                  </div>
                </div>
                <button
                  onClick={() => onSelectRun?.(run)}
                  className="flex items-center gap-1 px-2 py-1 rounded transition-colors hover:bg-accent shrink-0"
                  style={{
                    fontSize: "11px",
                    fontWeight: 500,
                    color: "var(--gs-navy)",
                    backgroundColor: "transparent",
                    border: "1px solid rgba(28,43,94,0.18)",
                    cursor: "pointer",
                  }}
                >
                  <ExternalLink size={9} />
                  Open
                </button>
              </div>
            ))}
            {recentRuns.length === 0 && (
              <div className="px-3 py-3" style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
                No recent runs returned by the API.
              </div>
            )}
          </div>

          {/* Run Archive collapsible */}
          <div style={{ borderTop: "1px solid var(--border)" }}>
            <button
              onClick={() => setShowArchive((p) => !p)}
              className="flex items-center gap-1.5 px-3 py-2 w-full hover:bg-accent/20 transition-colors"
              style={{ background: "none", border: "none", cursor: "pointer" }}
            >
              {showArchive ? (
                <ChevronDown size={11} style={{ color: "var(--gs-slate)" }} />
              ) : (
                <ChevronRight size={11} style={{ color: "var(--gs-slate)" }} />
              )}
              <span style={{ fontSize: "11px", fontWeight: 500, color: "var(--gs-slate)" }}>
                Run Archive
              </span>
            </button>

            {showArchive && (
              <div className="px-3 pb-2 flex flex-col gap-1.5">
                <input
                  type="text"
                  value={archiveSearch}
                  onChange={(e) => setArchiveSearch(e.target.value)}
                  placeholder="Search runs…"
                  className="rounded px-2 py-1 w-full outline-none"
                  style={{
                    fontSize: "11.5px",
                    backgroundColor: "var(--input-background)",
                    border: "1px solid var(--border)",
                    color: "var(--gs-navy)",
                  }}
                />
                {filteredArchive.length === 0 ? (
                  <p style={{ fontSize: "11px", color: "var(--gs-slate)" }}>No runs match.</p>
                ) : (
                  <div className="flex flex-col gap-0.5">
                    {filteredArchive.map((run) => (
                      <div
                        key={run.id}
                        className="flex items-center gap-2 py-1 px-1 hover:bg-accent/20 rounded transition-colors"
                      >
                        <StateBadge state={run.state} />
                        <span
                          className="font-mono flex-1 truncate"
                          style={{ fontSize: "11px", color: "var(--gs-navy)" }}
                        >
                          {run.name}
                        </span>
                        <button
                          onClick={() => onSelectRun?.(run)}
                          style={{
                            fontSize: "10px",
                            color: "var(--gs-navy)",
                            backgroundColor: "transparent",
                            border: "1px solid rgba(28,43,94,0.15)",
                            borderRadius: "3px",
                            padding: "1px 6px",
                            cursor: "pointer",
                          }}
                        >
                          Open
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

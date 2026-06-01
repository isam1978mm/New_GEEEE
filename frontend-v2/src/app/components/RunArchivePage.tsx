import { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Search,
  Trash2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { formatFileSize, type DeleteRunResult, type Run } from "../api/client";

function fmtDate(iso: string) {
  const d = new Date(iso);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) +
    " · " +
    d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })
  );
}

const stateIcon: Record<Run["state"], React.ReactNode> = {
  done: <CheckCircle2 size={12} />,
  running: <Loader2 size={12} className="animate-spin" />,
  failed: <XCircle size={12} />,
  queued: <Clock size={12} />,
  cancelled: <Clock size={12} />,
};

const stateColor: Record<Run["state"], string> = {
  done: "var(--gs-green)",
  running: "var(--gs-blue)",
  failed: "var(--gs-red)",
  queued: "var(--gs-amber)",
  cancelled: "var(--gs-slate)",
};

const stateBg: Record<Run["state"], string> = {
  done: "var(--gs-green-bg)",
  running: "var(--gs-blue-bg)",
  failed: "var(--gs-red-bg)",
  queued: "var(--gs-amber-bg)",
  cancelled: "rgba(100,116,139,0.06)",
};

const stateBorder: Record<Run["state"], string> = {
  done: "var(--gs-green-border)",
  running: "var(--gs-blue-border)",
  failed: "var(--gs-red-border)",
  queued: "var(--gs-amber-border)",
  cancelled: "rgba(100,116,139,0.15)",
};

interface RunArchivePageProps {
  runs: Run[];
  loading?: boolean;
  error?: string | null;
  onSelectRun?: (run: Run) => void;
  onDeleteRun?: (run: Run) => Promise<DeleteRunResult>;
}

function canDeleteRun(run: Run) {
  return run.state === "done" || run.state === "failed" || run.state === "cancelled";
}

export function RunArchivePage({ runs, loading = false, error = null, onSelectRun, onDeleteRun }: RunArchivePageProps) {
  const [search, setSearch] = useState("");
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [stateFilter, setStateFilter] = useState<Run["state"] | "all">("all");
  const [confirmRun, setConfirmRun] = useState<Run | null>(null);
  const [confirmText, setConfirmText] = useState("");
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);
  const [deleteFeedback, setDeleteFeedback] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const filtered = runs.filter((r) => {
    const matchSearch =
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.id.toLowerCase().includes(search.toLowerCase());
    const matchState = stateFilter === "all" || r.state === stateFilter;
    return matchSearch && matchState;
  });

  const stateFilters: Array<{ key: Run["state"] | "all"; label: string }> = [
    { key: "all", label: "All" },
    { key: "done", label: "Done" },
    { key: "running", label: "Running" },
    { key: "failed", label: "Failed" },
    { key: "queued", label: "Queued" },
    { key: "cancelled", label: "Cancelled" },
  ];

  const confirmMatches =
    confirmRun !== null &&
    (confirmText.trim() === confirmRun.id || confirmText.trim() === confirmRun.name);

  async function handleConfirmDelete() {
    if (!confirmRun || !onDeleteRun || !confirmMatches) {
      return;
    }
    setDeletingRunId(confirmRun.id);
    setDeleteError(null);
    setDeleteFeedback(null);
    try {
      const result = await onDeleteRun(confirmRun);
      setDeleteFeedback(`Run deleted. Freed ${formatFileSize(result.freedBytes)} from ${result.deletedFilesCount} files.`);
      setConfirmRun(null);
      setConfirmText("");
    } catch (_error) {
      setDeleteError("Run could not be deleted. Check that it is not active, then try again.");
    } finally {
      setDeletingRunId(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h2
            className="font-mono"
            style={{ fontSize: "14px", fontWeight: 700, color: "var(--gs-navy)", letterSpacing: "-0.01em" }}
          >
            Run Archive
          </h2>
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>
            All screening runs for this operator session
          </p>
        </div>
        <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-slate)" }}>
          {runs.length} runs
        </span>
      </div>

      {deleteFeedback && (
        <div className="rounded px-3 py-2" style={{ fontSize: "12px", color: "var(--gs-green)", backgroundColor: "var(--gs-green-bg)", border: "1px solid var(--gs-green-border)" }}>
          {deleteFeedback}
        </div>
      )}
      {deleteError && (
        <div className="rounded px-3 py-2" style={{ fontSize: "12px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}>
          {deleteError}
        </div>
      )}

      {/* Search + filters */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "var(--gs-slate)", opacity: 0.5 }} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or ID…"
            className="rounded px-2.5 py-1.5 pl-7 w-full outline-none"
            style={{
              fontSize: "12px",
              backgroundColor: "var(--card)",
              border: "1px solid var(--border)",
              color: "var(--gs-navy)",
            }}
          />
        </div>
        <div className="flex items-center gap-0.5">
          {stateFilters.map((f) => (
            <button
              key={f.key}
              onClick={() => setStateFilter(f.key)}
              className="px-2.5 py-1 rounded transition-all"
              style={{
                fontSize: "11.5px",
                fontWeight: stateFilter === f.key ? 600 : 400,
                color: stateFilter === f.key ? "var(--gs-navy)" : "var(--gs-slate)",
                backgroundColor: stateFilter === f.key ? "var(--card)" : "transparent",
                border: stateFilter === f.key ? "1px solid rgba(28,43,94,0.18)" : "1px solid transparent",
                cursor: "pointer",
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div
        className="rounded-lg bg-card overflow-hidden"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        {/* Table header */}
        <div
          className="grid px-4 py-2"
          style={{
            gridTemplateColumns: "24px 1fr 110px 90px 160px 160px",
            gap: "12px",
            borderBottom: "1px solid var(--border)",
            backgroundColor: "var(--accent)",
          }}
        >
          {["", "Name / ID", "State", "Stage", "Updated", ""].map((h, i) => (
            <span
              key={i}
              className="font-mono"
              style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              {h}
            </span>
          ))}
        </div>

        {/* Rows */}
        {loading ? (
          <div className="px-4 py-8 text-center">
            <p style={{ fontSize: "13px", color: "var(--gs-slate)" }}>Loading runs from API...</p>
          </div>
        ) : error ? (
          <div className="px-4 py-8 text-center">
            <p style={{ fontSize: "13px", color: "var(--gs-red)" }}>{error}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p style={{ fontSize: "13px", color: "var(--gs-slate)" }}>No runs match your filter.</p>
          </div>
        ) : (
          filtered.map((run, ri) => {
            const isExpanded = expandedRun === run.id;
            const color = stateColor[run.state];
            const bg = stateBg[run.state];
            const border = stateBorder[run.state];
            return (
              <div
                key={run.id}
                style={{ borderBottom: ri < filtered.length - 1 ? "1px solid var(--border)" : "none" }}
              >
                {/* Row */}
                <div
                  className="grid px-4 py-2 hover:bg-accent/30 transition-colors items-center cursor-pointer"
                  style={{ gridTemplateColumns: "24px 1fr 110px 90px 160px 160px", gap: "12px" }}
                  onClick={() => setExpandedRun(isExpanded ? null : run.id)}
                >
                  <span style={{ display: "flex", alignItems: "center", color: "var(--gs-slate)" }}>
                    {isExpanded
                      ? <ChevronDown size={11} />
                      : <ChevronRight size={11} />
                    }
                  </span>

                  <div className="min-w-0">
                    <div className="font-mono truncate" style={{ fontSize: "12.5px", fontWeight: 700, color: "var(--gs-navy)" }}>
                      {run.name}
                    </div>
                    <div className="font-mono truncate" style={{ fontSize: "9.5px", color: "var(--gs-slate)", opacity: 0.55 }}>
                      {run.id.slice(0, 20)}…
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span style={{ color, display: "flex", alignItems: "center" }}>{stateIcon[run.state]}</span>
                    <span style={{ fontSize: "11.5px", fontWeight: 600, color }}>
                      {run.state.charAt(0).toUpperCase() + run.state.slice(1)}
                    </span>
                  </div>

                  <span className="font-mono" style={{ fontSize: "11px", color: "var(--gs-slate)" }}>
                    {run.stage}
                  </span>

                  <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                    {fmtDate(run.updated)}
                  </span>

                  <div className="flex items-center gap-1.5 justify-end">
                    <button
                      onClick={(e) => { e.stopPropagation(); onSelectRun?.(run); }}
                      className="flex items-center gap-1 px-2 py-1 rounded hover:bg-accent transition-colors"
                      style={{
                        fontSize: "11px",
                        fontWeight: 500,
                        color: "var(--gs-navy)",
                        backgroundColor: "var(--accent)",
                        border: "1px solid rgba(28,43,94,0.15)",
                        cursor: "pointer",
                      }}
                    >
                      <ExternalLink size={9} />
                      Open
                    </button>
                    {canDeleteRun(run) ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmRun(run);
                          setConfirmText("");
                          setDeleteError(null);
                        }}
                        className="flex items-center gap-1 px-2 py-1 rounded hover:bg-accent transition-colors"
                        style={{
                          fontSize: "11px",
                          fontWeight: 500,
                          color: "var(--gs-red)",
                          backgroundColor: "transparent",
                          border: "1px solid var(--gs-red-border)",
                          cursor: "pointer",
                        }}
                      >
                        <Trash2 size={9} />
                        Delete
                      </button>
                    ) : (
                      <button
                        disabled
                        title="Cannot delete active run"
                        className="flex items-center gap-1 px-2 py-1 rounded"
                        style={{
                          fontSize: "11px",
                          fontWeight: 500,
                          color: "var(--gs-slate)",
                          backgroundColor: "transparent",
                          border: "1px solid rgba(100,116,139,0.15)",
                          cursor: "not-allowed",
                          opacity: 0.7,
                        }}
                      >
                        <Trash2 size={9} />
                        Cannot delete active run
                      </button>
                    )}
                  </div>
                </div>

                {/* Expanded detail */}
                {isExpanded && (
                  <div
                    className="grid px-4 py-3 gap-4"
                    style={{
                      backgroundColor: bg,
                      borderTop: `1px solid ${border}`,
                      gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                    }}
                  >
                    <div className="flex flex-col gap-0.5">
                      <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Run ID</span>
                      <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-navy)", fontWeight: 600 }}>
                        {run.id}
                      </span>
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Created</span>
                      <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-navy)" }}>
                        {fmtDate(run.created)}
                      </span>
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Final state</span>
                      <span className="font-mono" style={{ fontSize: "11px", color, fontWeight: 700 }}>
                        {run.state.toUpperCase()}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {confirmRun && (
        <div
          className="fixed inset-0 flex items-center justify-center"
          style={{ backgroundColor: "rgba(15,23,42,0.28)", zIndex: 40 }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-run-title"
        >
          <div
            className="rounded-lg bg-card p-4"
            style={{ width: "min(440px, calc(100vw - 32px))", border: "1px solid var(--border)", boxShadow: "0 18px 40px rgba(15,23,42,0.18)" }}
          >
            <h3 id="delete-run-title" className="font-mono" style={{ fontSize: "14px", fontWeight: 700, color: "var(--gs-navy)" }}>
              Delete run?
            </h3>
            <p style={{ fontSize: "12px", color: "var(--gs-slate)", marginTop: "8px" }}>
              This permanently deletes the run record and all files for this run.
            </p>
            <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "10px" }}>
              Type the run name or run ID to confirm.
            </p>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              className="rounded px-2.5 py-1.5 w-full outline-none mt-2"
              style={{
                fontSize: "12px",
                backgroundColor: "var(--input-background)",
                border: "1px solid var(--border)",
                color: "var(--gs-navy)",
              }}
            />
            <div className="flex items-center justify-end gap-2 mt-4">
              <button
                onClick={() => { setConfirmRun(null); setConfirmText(""); }}
                className="px-3 py-1.5 rounded"
                style={{ fontSize: "12px", color: "var(--gs-navy)", backgroundColor: "transparent", border: "1px solid rgba(28,43,94,0.15)", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                onClick={() => { void handleConfirmDelete(); }}
                disabled={!confirmMatches || deletingRunId === confirmRun.id}
                className="px-3 py-1.5 rounded"
                style={{
                  fontSize: "12px",
                  color: "white",
                  backgroundColor: "var(--gs-red)",
                  border: "1px solid var(--gs-red-border)",
                  cursor: confirmMatches && deletingRunId !== confirmRun.id ? "pointer" : "not-allowed",
                  opacity: confirmMatches && deletingRunId !== confirmRun.id ? 1 : 0.55,
                }}
              >
                {deletingRunId === confirmRun.id ? "Deleting..." : "Delete permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

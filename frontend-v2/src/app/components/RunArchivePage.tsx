import { useEffect, useState } from "react";
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
import {
  type CleanupRunSuggestion,
  type CleanupSummary,
  formatFileSize,
  type DeletionAuditSummary,
  type DeleteRunResult,
  type Run,
  type RunListOrder,
  type RunListParams,
  type RunListSortField,
  type RunListStatusFilter,
} from "../api/client";

function fmtDate(iso: string) {
  const d = new Date(iso);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) +
    " · " +
    d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })
  );
}

function fmtMaybeDate(iso: string | null) {
  return iso ? fmtDate(iso) : "Not scanned";
}

function fmtRunSize(run: Run) {
  return run.diskUsageBytes === null ? "Unknown size" : formatFileSize(run.diskUsageBytes);
}

function fmtFileCount(run: Run) {
  return run.outputFileCount === null ? "Unknown" : `${run.outputFileCount}`;
}

function stateLabel(state: Run["state"]) {
  return state === "stale_failed" ? "Stale failed" : state.charAt(0).toUpperCase() + state.slice(1);
}

const stateIcon: Record<Run["state"], React.ReactNode> = {
  done: <CheckCircle2 size={12} />,
  running: <Loader2 size={12} className="animate-spin" />,
  failed: <XCircle size={12} />,
  stale_failed: <XCircle size={12} />,
  queued: <Clock size={12} />,
  cancelled: <Clock size={12} />,
};

const stateColor: Record<Run["state"], string> = {
  done: "var(--gs-green)",
  running: "var(--gs-blue)",
  failed: "var(--gs-red)",
  stale_failed: "var(--gs-red)",
  queued: "var(--gs-amber)",
  cancelled: "var(--gs-slate)",
};

const stateBg: Record<Run["state"], string> = {
  done: "var(--gs-green-bg)",
  running: "var(--gs-blue-bg)",
  failed: "var(--gs-red-bg)",
  stale_failed: "var(--gs-red-bg)",
  queued: "var(--gs-amber-bg)",
  cancelled: "rgba(100,116,139,0.06)",
};

const stateBorder: Record<Run["state"], string> = {
  done: "var(--gs-green-border)",
  running: "var(--gs-blue-border)",
  failed: "var(--gs-red-border)",
  stale_failed: "var(--gs-red-border)",
  queued: "var(--gs-amber-border)",
  cancelled: "rgba(100,116,139,0.15)",
};

interface RunArchivePageProps {
  runs: Run[];
  loading?: boolean;
  error?: string | null;
  onQueryChange?: (query: RunListParams) => void | Promise<void>;
  onSelectRun?: (run: Run) => void;
  onDeleteRun?: (run: Run) => Promise<DeleteRunResult>;
  deletionAudit?: DeletionAuditSummary;
  cleanupSummary?: CleanupSummary;
}

type SortOption = "newest" | "oldest" | "largest" | "smallest" | "most_files" | "name_asc";

function canDeleteRun(run: Run) {
  return run.state === "done" || run.state === "failed" || run.state === "stale_failed" || run.state === "cancelled";
}

function mapSortOption(sortOption: SortOption): { sort: RunListSortField; order: RunListOrder } {
  switch (sortOption) {
    case "oldest":
      return { sort: "created_at", order: "asc" };
    case "largest":
      return { sort: "disk_usage_bytes", order: "desc" };
    case "smallest":
      return { sort: "disk_usage_bytes", order: "asc" };
    case "most_files":
      return { sort: "output_file_count", order: "desc" };
    case "name_asc":
      return { sort: "name", order: "asc" };
    case "newest":
    default:
      return { sort: "created_at", order: "desc" };
  }
}

function toRunFromSuggestion(suggestion: CleanupRunSuggestion): Run {
  return {
    id: suggestion.id,
    name: suggestion.name,
    state: suggestion.state,
    stage:
      suggestion.state === "done"
        ? "Completed"
        : suggestion.state === "failed"
          ? "Failed"
          : suggestion.state === "stale_failed"
            ? "Stale failed"
            : suggestion.state === "running"
              ? "Running"
              : "Queued",
    updated: suggestion.created,
    created: suggestion.created,
    diskUsageBytes: suggestion.diskUsageBytes,
    outputFileCount: suggestion.outputFileCount,
    lastDiskScanAt: suggestion.lastDiskScanAt,
  };
}

function CleanupSuggestionList({
  title,
  emptyText,
  items,
  onSelectRun,
  onRequestDelete,
}: {
  title: string;
  emptyText: string;
  items: CleanupRunSuggestion[];
  onSelectRun?: (run: Run) => void;
  onRequestDelete?: (run: Run) => void;
}) {
  return (
    <div className="rounded-lg bg-card px-3 py-2 flex flex-col gap-2" style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}>
      <div className="flex items-center justify-between">
        <span className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          {title}
        </span>
      </div>
      {items.length === 0 ? (
        <p style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>{emptyText}</p>
      ) : (
        <div className="flex flex-col gap-2">
          {items.map((item) => {
            const run = toRunFromSuggestion(item);
            return (
              <div key={`${title}-${item.id}`} className="flex items-center justify-between gap-3 rounded px-2 py-2" style={{ backgroundColor: "var(--accent)" }}>
                <div className="min-w-0 flex-1">
                  <div className="font-mono truncate" style={{ fontSize: "11px", color: "var(--gs-navy)", fontWeight: 700 }}>
                    {item.name || item.id.slice(0, 8)}
                  </div>
                  <div style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                    {stateLabel(item.state)} · {fmtDate(item.created)} · {item.diskUsageBytes === null ? "Size not scanned" : formatFileSize(item.diskUsageBytes)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onSelectRun?.(run)}
                    className="flex items-center gap-1 px-2 py-1 rounded hover:bg-accent transition-colors"
                    style={{ fontSize: "11px", fontWeight: 500, color: "var(--gs-navy)", backgroundColor: "var(--card)", border: "1px solid rgba(28,43,94,0.15)", cursor: "pointer" }}
                  >
                    <ExternalLink size={9} />
                    Open
                  </button>
                  {canDeleteRun(run) && (
                    <button
                      onClick={() => onRequestDelete?.(run)}
                      className="flex items-center gap-1 px-2 py-1 rounded hover:bg-accent transition-colors"
                      style={{ fontSize: "11px", fontWeight: 500, color: "var(--gs-red)", backgroundColor: "transparent", border: "1px solid var(--gs-red-border)", cursor: "pointer" }}
                    >
                      <Trash2 size={9} />
                      Delete
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function RunArchivePage({ runs, loading = false, error = null, onQueryChange, onSelectRun, onDeleteRun, deletionAudit, cleanupSummary }: RunArchivePageProps) {
  const [search, setSearch] = useState("");
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [stateFilter, setStateFilter] = useState<RunListStatusFilter | "all">("all");
  const [sortOption, setSortOption] = useState<SortOption>("newest");
  const [confirmRun, setConfirmRun] = useState<Run | null>(null);
  const [confirmText, setConfirmText] = useState("");
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);
  const [deleteFeedback, setDeleteFeedback] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    const { sort, order } = mapSortOption(sortOption);
    void onQueryChange?.({
      q: search.trim() || undefined,
      status: stateFilter === "all" ? undefined : stateFilter,
      sort,
      order,
      limit: 100,
      offset: 0,
    });
  }, [search, stateFilter, sortOption]);

  const isDefaultQuery = search.trim().length === 0 && stateFilter === "all" && sortOption === "newest";

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
            Stored screening runs from the local archive
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

      <div className="rounded-lg bg-card px-3 py-3 flex flex-col gap-3" style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}>
        <div className="flex items-center justify-between">
          <div>
            <div className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
              Storage Health
            </div>
            <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "4px" }}>
              {cleanupSummary?.warningReason || "No runs yet."}
            </div>
          </div>
          <div className="font-mono" style={{ fontSize: "11px", fontWeight: 700, color: cleanupSummary?.cleanupRecommended ? "var(--gs-red)" : "var(--gs-green)" }}>
            {cleanupSummary?.cleanupRecommended ? "Cleanup recommended" : "Storage healthy"}
          </div>
        </div>
        <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
          <div>
            <div style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Total run storage</div>
            <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)", fontWeight: 700 }}>{formatFileSize(cleanupSummary?.totalDiskUsageBytes ?? 0)}</div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Number of runs</div>
            <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)", fontWeight: 700 }}>{cleanupSummary?.totalRuns ?? 0}</div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Active runs</div>
            <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)", fontWeight: 700 }}>{cleanupSummary?.activeRunsCount ?? 0}</div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Terminal runs</div>
            <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)", fontWeight: 700 }}>{cleanupSummary?.terminalRunsCount ?? 0}</div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Deleted runs</div>
            <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)", fontWeight: 700 }}>{cleanupSummary?.deletedRunsCount ?? 0}</div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Total freed</div>
            <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-green)", fontWeight: 700 }}>{formatFileSize(cleanupSummary?.totalFreedBytes ?? 0)}</div>
          </div>
        </div>
        {cleanupSummary && cleanupSummary.totalRuns === 0 && (
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>No runs yet.</p>
        )}
        {cleanupSummary && cleanupSummary.totalRuns > 0 && cleanupSummary.totalDiskUsageBytes === 0 && (
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>Run sizes are still being scanned.</p>
        )}
      </div>

      <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        <CleanupSuggestionList
          title="Largest runs"
          emptyText="No terminal runs available."
          items={cleanupSummary?.largestRuns ?? []}
          onSelectRun={onSelectRun}
          onRequestDelete={(run) => {
            setConfirmRun(run);
            setConfirmText("");
            setDeleteError(null);
          }}
        />
        <CleanupSuggestionList
          title="Oldest runs"
          emptyText="No terminal runs available."
          items={cleanupSummary?.oldestTerminalRuns ?? []}
          onSelectRun={onSelectRun}
          onRequestDelete={(run) => {
            setConfirmRun(run);
            setConfirmText("");
            setDeleteError(null);
          }}
        />
        <CleanupSuggestionList
          title="Stale failed runs"
          emptyText="No stale failed runs."
          items={cleanupSummary?.staleFailedRuns ?? []}
          onSelectRun={onSelectRun}
          onRequestDelete={(run) => {
            setConfirmRun(run);
            setConfirmText("");
            setDeleteError(null);
          }}
        />
      </div>

      <div
        className="rounded-lg bg-card px-3 py-2 flex flex-col gap-2"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div className="flex items-center justify-between">
          <span className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
            Deleted Runs / Cleanup Summary
          </span>
          <span className="font-mono" style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-green)" }}>
            Total freed: {formatFileSize(deletionAudit?.totalFreedBytes ?? 0)}
          </span>
        </div>
        {(deletionAudit?.records.length ?? 0) === 0 ? (
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>No deleted run audit records yet.</p>
        ) : (
          <div className="flex flex-col gap-1">
            {deletionAudit?.records.slice(0, 3).map((record) => (
              <div key={`${record.runId}-${record.deletedAt}`} className="flex items-center justify-between gap-3">
                <span className="font-mono truncate" style={{ fontSize: "11px", color: "var(--gs-navy)" }}>
                  {record.runName || record.runId.slice(0, 8)}
                </span>
                <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>{fmtDate(record.deletedAt)}</span>
                <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-green)", fontWeight: 700 }}>
                  {formatFileSize(record.freedBytes)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search + filters */}
      <div className="grid gap-2" style={{ gridTemplateColumns: "minmax(0,1.5fr) minmax(160px,0.8fr) minmax(180px,1fr)" }}>
        <div className="relative flex-1">
          <label htmlFor="archive-run-search" className="font-mono" style={{ display: "block", fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: "6px" }}>
            Search runs
          </label>
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "var(--gs-slate)", opacity: 0.5 }} />
          <input
            id="archive-run-search"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or ID..."
            className="rounded px-2.5 py-1.5 pl-7 w-full outline-none"
            style={{
              fontSize: "12px",
              backgroundColor: "var(--card)",
              border: "1px solid var(--border)",
              color: "var(--gs-navy)",
            }}
          />
        </div>
        <div>
          <label htmlFor="archive-status-filter" className="font-mono" style={{ display: "block", fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: "6px" }}>
            Status filter
          </label>
          <select
            id="archive-status-filter"
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value as RunListStatusFilter | "all")}
            className="rounded px-2.5 py-1.5 w-full outline-none"
            style={{ fontSize: "12px", backgroundColor: "var(--card)", border: "1px solid var(--border)", color: "var(--gs-navy)" }}
          >
            <option value="all">All statuses</option>
            <option value="done">Done</option>
            <option value="running">Running</option>
            <option value="failed">Failed</option>
            <option value="stale_failed">Stale failed</option>
            <option value="queued">Queued</option>
          </select>
        </div>
        <div>
          <label htmlFor="archive-sort-runs" className="font-mono" style={{ display: "block", fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: "6px" }}>
            Sort runs
          </label>
          <select
            id="archive-sort-runs"
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value as SortOption)}
            className="rounded px-2.5 py-1.5 w-full outline-none"
            style={{ fontSize: "12px", backgroundColor: "var(--card)", border: "1px solid var(--border)", color: "var(--gs-navy)" }}
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="largest">Largest first</option>
            <option value="smallest">Smallest first</option>
            <option value="most_files">Most files</option>
            <option value="name_asc">Name A-Z</option>
          </select>
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
        ) : runs.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p style={{ fontSize: "13px", color: "var(--gs-slate)" }}>
              {isDefaultQuery ? "No runs yet." : "No runs match this filter."}
            </p>
          </div>
        ) : (
          runs.map((run, ri) => {
            const isExpanded = expandedRun === run.id;
            const color = stateColor[run.state];
            const bg = stateBg[run.state];
            const border = stateBorder[run.state];
            return (
              <div
                key={run.id}
                style={{ borderBottom: ri < runs.length - 1 ? "1px solid var(--border)" : "none" }}
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
                      {stateLabel(run.state)}
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
                        {stateLabel(run.state)}
                      </span>
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Run size</span>
                      <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-navy)", fontWeight: 600 }}>
                        {fmtRunSize(run)}
                      </span>
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>File count</span>
                      <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-navy)", fontWeight: 600 }}>
                        {fmtFileCount(run)}
                      </span>
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>Last scanned</span>
                      <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-navy)" }}>
                        {fmtMaybeDate(run.lastDiskScanAt)}
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
            <div
              className="rounded px-3 py-2 mt-3"
              style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}
            >
              <div style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
                Estimated size: <span className="font-mono" style={{ color: "var(--gs-navy)", fontWeight: 700 }}>{fmtRunSize(confirmRun)}</span>
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", marginTop: "2px" }}>
                File count: <span className="font-mono" style={{ color: "var(--gs-navy)", fontWeight: 700 }}>{fmtFileCount(confirmRun)}</span>
              </div>
            </div>
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

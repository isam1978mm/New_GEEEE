import { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Search,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import type { Run } from "../api/client";

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
}

export function RunArchivePage({ runs, loading = false, error = null, onSelectRun }: RunArchivePageProps) {
  const [search, setSearch] = useState("");
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [stateFilter, setStateFilter] = useState<Run["state"] | "all">("all");

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
            gridTemplateColumns: "24px 1fr 110px 90px 160px 76px",
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
                  style={{ gridTemplateColumns: "24px 1fr 110px 90px 160px 76px", gap: "12px" }}
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
    </div>
  );
}

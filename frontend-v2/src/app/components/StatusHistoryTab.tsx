import { useState } from "react";
import { CheckCircle2, XCircle, Loader2, Clock, ChevronDown, ChevronRight } from "lucide-react";
import type { RunDetail, RunState, StatusEvent } from "../api/client";

const stateIcon: Record<RunState, React.ReactNode> = {
  done: <CheckCircle2 size={12} />,
  running: <Loader2 size={12} className="animate-spin" />,
  failed: <XCircle size={12} />,
  stale_failed: <XCircle size={12} />,
  queued: <Clock size={12} />,
  cancelled: <Clock size={12} />,
};

const stateColor: Record<RunState, string> = {
  done: "var(--gs-green)",
  running: "var(--gs-blue)",
  failed: "var(--gs-red)",
  stale_failed: "var(--gs-red)",
  queued: "var(--gs-slate)",
  cancelled: "var(--gs-slate)",
};

function fmtTime(iso: string) {
  const d = new Date(iso);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" }) +
    " · " +
    d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })
  );
}

function EventRow({ event, isLast }: { event: StatusEvent; isLast: boolean }) {
  const color = stateColor[event.state];
  const icon = stateIcon[event.state];

  return (
    <div className="flex gap-3 px-4 py-2.5" style={{ borderBottom: isLast ? "none" : "1px solid var(--border)" }}>
      <div className="flex flex-col items-center shrink-0">
        <div
          className="flex items-center justify-center rounded-full"
          style={{
            width: "22px",
            height: "22px",
            backgroundColor: `${color}18`,
            color,
            border: `1px solid ${color}40`,
            flexShrink: 0,
          }}
        >
          {icon}
        </div>
        {!isLast && (
          <div style={{ width: "1px", flex: 1, backgroundColor: "var(--border)", marginTop: "3px", minHeight: "12px" }} />
        )}
      </div>
      <div className="flex-1 min-w-0 pb-0.5">
        <div className="flex items-center gap-2 mb-0.5">
          <span
            className="font-mono"
            style={{ fontSize: "10.5px", fontWeight: 700, color, textTransform: "uppercase", letterSpacing: "0.04em" }}
          >
            {event.stage}
          </span>
          <span
            className="font-mono"
            style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.55 }}
          >
            {fmtTime(event.time)}
          </span>
        </div>
        <p
          style={{
            fontSize: "11.5px",
            color: event.state === "failed" || event.state === "stale_failed" ? "var(--gs-red)" : "var(--foreground)",
            lineHeight: "1.45",
          }}
        >
          {event.message}
        </p>
      </div>
    </div>
  );
}

interface StatusHistoryTabProps {
  run: RunDetail;
}

function stateLabel(state: RunState): string {
  const labels: Record<RunState, string> = {
    done: "Done",
    running: "Running",
    failed: "Failed",
    stale_failed: "Stale failed",
    queued: "Queued",
    cancelled: "Cancelled",
  };
  return labels[state];
}

function lastRecordedEvent(events: StatusEvent[]): string {
  const lastEvent = events.length > 0 ? events[events.length - 1] : null;
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

function FailureSummary({ run }: { run: RunDetail }) {
  if (run.state === "stale_failed") {
    const terminalDetail = backendFailureDetail(run);
    return (
      <div>
        <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-red)" }}>
          Run is stale_failed.
        </span>
        <p style={{ fontSize: "11px", color: "var(--gs-red)", marginTop: "1px", opacity: 0.85 }}>
          Last known stage: {run.stage}
        </p>
        <p style={{ fontSize: "11px", color: "var(--gs-red)", marginTop: "1px", opacity: 0.85 }}>
          Last recorded event: {lastRecordedEvent(run.history)}
        </p>
        <p style={{ fontSize: "11px", color: "var(--gs-red)", marginTop: "1px", opacity: 0.85 }}>
          {terminalDetail ?? "No terminal failure message was recorded."}
        </p>
      </div>
    );
  }

  if (run.state === "failed") {
    return (
      <div>
        <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-red)" }}>
          {backendFailureDetail(run) ?? "Run failed. No failure detail was recorded."}
        </span>
      </div>
    );
  }

  return null;
}

export function StatusHistoryTab({ run }: StatusHistoryTabProps) {
  const runState = run.state;
  const events = run.history;
  const autoExpand = runState === "running" || runState === "failed" || runState === "stale_failed";
  const [expanded, setExpanded] = useState(autoExpand);

  const headerColor =
    runState === "failed" || runState === "stale_failed" ? "var(--gs-red)" :
    runState === "running" ? "var(--gs-blue)" :
    "var(--gs-navy)";

  const headerBg =
    runState === "failed" || runState === "stale_failed" ? "var(--gs-red-bg)" :
    runState === "running" ? "var(--gs-blue-bg)" :
    "var(--accent)";

  return (
    <div className="flex flex-col gap-3">
      <div
        className="rounded-lg bg-card overflow-hidden"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        {/* Header / toggle */}
        <button
          onClick={() => setExpanded((p) => !p)}
          className="flex items-center gap-2 px-4 py-2.5 w-full hover:opacity-90 transition-opacity"
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            backgroundColor: headerBg,
            borderBottom: expanded ? "1px solid var(--border)" : "none",
          }}
        >
          {expanded
            ? <ChevronDown size={12} style={{ color: headerColor, flexShrink: 0 }} />
            : <ChevronRight size={12} style={{ color: headerColor, flexShrink: 0 }} />
          }
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: headerColor, textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            Status History
          </span>
          <span
            className="font-mono"
            style={{
              fontSize: "9.5px",
              fontWeight: 700,
              color: "white",
              backgroundColor: headerColor,
              padding: "1px 6px",
              borderRadius: "3px",
            }}
          >
            {events.length} events
          </span>

          <div className="ml-auto flex items-center gap-1.5">
            {(runState === "failed" || runState === "stale_failed") && (
              <>
                <XCircle size={12} style={{ color: "var(--gs-red)" }} />
                <span style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-red)" }}>
                  {stateLabel(runState)}
                </span>
              </>
            )}
            {runState === "done" && (
              <>
                <CheckCircle2 size={12} style={{ color: "var(--gs-green)" }} />
                <span style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-green)" }}>
                  Completed successfully
                </span>
              </>
            )}
            {runState === "running" && (
              <>
                <Loader2 size={12} className="animate-spin" style={{ color: "var(--gs-blue)" }} />
                <span style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-blue)" }}>
                  In progress
                </span>
              </>
            )}
          </div>
        </button>

        {expanded && (runState === "failed" || runState === "stale_failed") && (
          <div
            className="px-4 py-2 flex items-start gap-2"
            style={{ backgroundColor: "var(--gs-red-bg)", borderBottom: "1px solid var(--gs-red-border)" }}
          >
            <XCircle size={12} style={{ color: "var(--gs-red)", marginTop: "1px", flexShrink: 0 }} />
            <FailureSummary run={run} />
          </div>
        )}

        {/* Events */}
        {expanded && (
          <div>
            {events.length === 0 && (
              <div className="px-4 py-3" style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
                No detailed status history is available for this run.
              </div>
            )}
            {events.map((ev, i) => (
              <EventRow key={ev.id} event={ev} isLast={i === events.length - 1} />
            ))}
          </div>
        )}

        {!expanded && (
          <div className="px-4 py-2">
            <p style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
              Click to expand event timeline ({events.length} events).
            </p>
          </div>
        )}
      </div>

      {/* Run metadata strip */}
      <div
        className="rounded-lg px-4 py-2.5 grid gap-3"
        style={{
          backgroundColor: "var(--card)",
          border: "1px solid var(--border)",
          gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
        }}
      >
        {[
          { label: "Run ID", value: run.id },
          { label: "Run name", value: run.name },
          {
            label: "Final state",
            value: stateLabel(runState),
            highlight:
              runState === "failed" || runState === "stale_failed" ? "var(--gs-red)" :
              runState === "running" ? "var(--gs-blue)" :
              "var(--gs-green)",
          },
          { label: "Events", value: `${events.length}` },
        ].map((item) => (
          <div key={item.label} className="flex flex-col gap-0.5">
            <span style={{ fontSize: "10px", color: "var(--gs-slate)" }}>{item.label}</span>
            <span
              className="font-mono"
              style={{ fontSize: "12px", fontWeight: 700, color: item.highlight || "var(--gs-navy)" }}
            >
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

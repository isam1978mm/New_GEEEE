import { useState } from "react";
import { ChevronDown, ChevronRight, Inbox } from "lucide-react";
import type { ActivityEvent, RunDetail } from "../api/client";

const dotColor: Record<ActivityEvent["type"], string> = {
  done: "var(--gs-green)",
  info: "var(--gs-blue)",
  running: "var(--gs-amber)",
  failed: "var(--gs-red)",
};

const dotBg: Record<ActivityEvent["type"], string> = {
  done: "var(--gs-green-bg)",
  info: "var(--gs-blue-bg)",
  running: "var(--gs-amber-bg)",
  failed: "var(--gs-red-bg)",
};

interface ActivityCardProps {
  run?: RunDetail | null;
  events?: ActivityEvent[];
  hasRun?: boolean;
}

export function ActivityCard({ run = null, events = [], hasRun = true }: ActivityCardProps) {
  const [showSysMessages, setShowSysMessages] = useState(false);
  const runState = run?.state ?? "queued";

  const lifecycleItems =
    runState === "done"
      ? [
          { label: "State", value: "Done", color: "var(--gs-green)" },
          { label: "Stage", value: run?.stage ?? "Completed", color: "var(--gs-navy)" },
          { label: "Events", value: `${events.length}`, color: "var(--gs-navy)" },
          { label: "At", value: run ? new Date(run.updated).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }) : "-", color: "var(--gs-slate)" },
        ]
      : runState === "running"
      ? [
          { label: "State", value: "Running", color: "var(--gs-blue)" },
          { label: "Stage", value: run?.stage ?? "Running", color: "var(--gs-navy)" },
          { label: "Events", value: `${events.length}`, color: "var(--gs-navy)" },
          { label: "At", value: run ? new Date(run.updated).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }) : "-", color: "var(--gs-slate)" },
        ]
      : runState === "failed"
      ? [
          { label: "State", value: "Failed", color: "var(--gs-red)" },
          { label: "Stage", value: run?.stage ?? "Failed", color: "var(--gs-navy)" },
          { label: "Events", value: `${events.length}`, color: "var(--gs-red)" },
          { label: "At", value: run ? new Date(run.updated).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }) : "-", color: "var(--gs-slate)" },
        ]
      : runState === "stale_failed"
      ? [
          { label: "State", value: "Stale failed", color: "var(--gs-red)" },
          { label: "Stage", value: run?.stage ?? "Unknown", color: "var(--gs-navy)" },
          { label: "Events", value: `${events.length}`, color: "var(--gs-red)" },
          { label: "At", value: run ? new Date(run.updated).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }) : "-", color: "var(--gs-slate)" },
        ]
      : [
          { label: "State", value: "Queued", color: "var(--gs-amber)" },
          { label: "Stage", value: run?.stage ?? "Queued", color: "var(--gs-navy)" },
          { label: "Events", value: `${events.length}`, color: "var(--gs-navy)" },
          { label: "At", value: run ? new Date(run.updated).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }) : "-", color: "var(--gs-slate)" },
        ];

  return (
    <div
      className="rounded-lg bg-card flex flex-col"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.06)" }}
    >
      {/* Header */}
      <div
        className="flex items-center gap-2 px-4 py-2.5"
        style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
      >
        <h3
          className="font-mono"
          style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", letterSpacing: "0.07em", textTransform: "uppercase" }}
        >
          Activity
        </h3>
        <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>
          Run lifecycle &amp; event feed
        </span>
      </div>

      {!hasRun ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center px-6 py-10 flex-1">
          <Inbox size={28} style={{ color: "var(--gs-slate)", opacity: 0.3, marginBottom: "10px" }} />
          <p style={{ fontSize: "13px", fontWeight: 500, color: "var(--gs-slate)", opacity: 0.6, textAlign: "center" }}>
            No active run
          </p>
          <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", opacity: 0.45, textAlign: "center", marginTop: "4px", maxWidth: "200px" }}>
            Queue a run from the workflow card to see activity here.
          </p>
        </div>
      ) : (
        <div className="px-4 py-3 flex flex-col gap-3">
          {/* Lifecycle summary */}
          <div
            className="rounded p-2.5 grid gap-2"
            style={{
              backgroundColor: "var(--accent)",
              border: "1px solid rgba(28,43,94,0.1)",
              gridTemplateColumns: "repeat(4, 1fr)",
            }}
          >
            {lifecycleItems.map((item) => (
              <div key={item.label} className="flex flex-col gap-0.5">
                <span style={{ fontSize: "10px", color: "var(--gs-slate)", fontWeight: 400 }}>
                  {item.label}
                </span>
                <span className="font-mono" style={{ fontSize: "11.5px", fontWeight: 700, color: item.color }}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>

          {/* Activity feed */}
          <div>
            <div
              className="font-mono mb-1.5"
              style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.07em" }}
            >
              Activity Feed
            </div>
            <div className="flex flex-col overflow-y-auto" style={{ maxHeight: "240px" }}>
              {events.length === 0 && (
                <div style={{ fontSize: "11.5px", color: "var(--gs-slate)", padding: "6px 0" }}>
                  No activity events are available yet.
                </div>
              )}
              {events.map((ev, i) => (
                <div
                  key={ev.id}
                  className="flex items-start gap-2.5 py-1.5"
                  style={{
                    borderBottom: i < events.length - 1 ? "1px solid rgba(28,43,94,0.05)" : "none",
                  }}
                >
                  <div className="shrink-0 mt-1">
                    <div
                      className="rounded-full"
                      style={{
                        width: "6px",
                        height: "6px",
                        backgroundColor: dotColor[ev.type],
                        boxShadow: `0 0 0 2.5px ${dotBg[ev.type]}`,
                      }}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span style={{ fontSize: "11.5px", color: "var(--gs-navy)", fontWeight: 500 }}>
                      {ev.message}
                    </span>
                    {ev.detail && (
                      <span style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginLeft: "5px" }}>
                        {ev.detail}
                      </span>
                    )}
                  </div>
                  <span
                    className="font-mono shrink-0"
                    style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.55 }}
                  >
                    {ev.time}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* System messages */}
          <div>
            <button
              onClick={() => setShowSysMessages((p) => !p)}
              className="flex items-center gap-1 transition-opacity hover:opacity-75"
              style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
            >
              {showSysMessages ? (
                <ChevronDown size={11} style={{ color: "var(--gs-slate)" }} />
              ) : (
                <ChevronRight size={11} style={{ color: "var(--gs-slate)" }} />
              )}
              <span style={{ fontSize: "11px", color: "var(--gs-slate)", fontWeight: 500 }}>
                System Messages
              </span>
            </button>
            {showSysMessages && (
              <div
                className="mt-1.5 rounded px-3 py-2 font-mono"
                style={{
                  backgroundColor: "var(--input-background)",
                  border: "1px solid var(--border)",
                  fontSize: "10.5px",
                  color: "var(--gs-slate)",
                  lineHeight: "1.7",
                }}
              >
                {events.length === 0 ? (
                  <div>No status messages returned by the API.</div>
                ) : (
                  events.slice(0, 5).map((event) => (
                    <div key={event.id}>[{event.time}] {event.message}</div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

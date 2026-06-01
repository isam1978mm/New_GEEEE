import { WifiOff, CheckCircle2, Loader2, XCircle, Clock } from "lucide-react";
import type { RunState } from "../data/mockData";

interface StatusStripProps {
  runId: string;
  state: RunState;
  stage: string;
}

const stateCfg: Record<RunState, { label: string; color: string; bg: string; border: string; icon: React.ReactNode }> = {
  done: {
    label: "Done",
    color: "var(--gs-green)",
    bg: "var(--gs-green-bg)",
    border: "var(--gs-green-border)",
    icon: <CheckCircle2 size={10} />,
  },
  running: {
    label: "Running",
    color: "var(--gs-blue)",
    bg: "var(--gs-blue-bg)",
    border: "var(--gs-blue-border)",
    icon: <Loader2 size={10} className="animate-spin" />,
  },
  failed: {
    label: "Failed",
    color: "var(--gs-red)",
    bg: "var(--gs-red-bg)",
    border: "var(--gs-red-border)",
    icon: <XCircle size={10} />,
  },
  queued: {
    label: "Queued",
    color: "var(--gs-amber)",
    bg: "var(--gs-amber-bg)",
    border: "var(--gs-amber-border)",
    icon: <Clock size={10} />,
  },
};

function Chip({
  label,
  value,
  color,
  bg,
  border,
  icon,
}: {
  label: string;
  value: string;
  color: string;
  bg: string;
  border: string;
  icon?: React.ReactNode;
}) {
  return (
    <div
      className="flex items-center gap-1.5 px-2 rounded"
      style={{ backgroundColor: bg, border: `1px solid ${border}`, height: "22px" }}
    >
      {icon && <span style={{ color, display: "flex", alignItems: "center" }}>{icon}</span>}
      <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>{label}</span>
      <span className="font-mono" style={{ fontSize: "10.5px", fontWeight: 600, color }}>
        {value}
      </span>
    </div>
  );
}

export function StatusStrip({ runId, state, stage }: StatusStripProps) {
  const cfg = stateCfg[state];
  return (
    <div
      className="flex items-center gap-2 px-5"
      style={{
        backgroundColor: "#F8F7F2",
        borderBottom: "1px solid rgba(28,43,94,0.1)",
        height: "34px",
      }}
    >
      <Chip
        label="Run"
        value={runId.slice(0, 8)}
        color="var(--gs-navy)"
        bg="rgba(28,43,94,0.05)"
        border="rgba(28,43,94,0.12)"
      />
      <Chip
        label="Status"
        value={cfg.label}
        color={cfg.color}
        bg={cfg.bg}
        border={cfg.border}
        icon={cfg.icon}
      />
      <Chip
        label="Stage"
        value={stage}
        color="var(--gs-slate)"
        bg="rgba(100,116,139,0.06)"
        border="rgba(100,116,139,0.15)"
      />

      <div className="ml-auto flex items-center gap-1.5" style={{ opacity: 0.55 }}>
        <WifiOff size={10} style={{ color: "var(--gs-slate)" }} />
        <span
          className="font-mono"
          style={{ fontSize: "10px", color: "var(--gs-slate)", fontWeight: 500 }}
        >
          External tiles disabled
        </span>
      </div>
    </div>
  );
}
